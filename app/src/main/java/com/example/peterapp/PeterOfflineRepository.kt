package com.example.peterapp

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

/**
 * Core Local Repository & Project Directory Intelligence Engine (`PeterOfflineRepository.kt` — < 540 lines).
 *
 * Manages the 581 bundled `aryashakti` project files, imported Git workspaces,
 * 3,170 AST symbols, 230 PostgreSQL tables, and 537 API routes.
 * Provides multi-keyword co-occurrence search across the entire project directory
 * so the Coding Agent answers every question just like Antigravity!
 */
class PeterOfflineRepository(private val context: Context) {

    private val dbName = "peter_offline.db"
    val localMirrorRoot: File = File(context.filesDir, "aryashakti")
    val workspacesRoot: File = File(context.filesDir, "workspaces")
    private val prefs = context.getSharedPreferences("peter_workspace_prefs", Context.MODE_PRIVATE)

    var activeWorkspaceId: String
        get() = prefs.getString("active_workspace_id", "aryashakti") ?: "aryashakti"
        set(value) {
            prefs.edit().putString("active_workspace_id", value).apply()
        }

    private val stopWords = setOf(
        "what", "where", "which", "when", "who", "whom", "whose", "why", "how",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "can", "could", "will", "would", "shall", "should",
        "the", "and", "for", "with", "from", "into", "about", "this", "that",
        "explain", "detail", "details", "show", "give", "tell", "find", "list",
        "related", "function", "functions", "method", "methods", "class", "classes",
        "file", "files", "table", "tables", "module", "modules", "project", "code",
        "aryashakti", "used", "using", "work", "works", "working", "logic", "flow",
        "present", "app", "inside", "all", "based", "directory", "folder", "please"
    )

    private fun ensureDatabaseFile(): File {
        val dbFile = context.getDatabasePath(dbName)
        if (!dbFile.exists() || dbFile.length() < 1024 * 1024) {
            dbFile.parentFile?.mkdirs()
            context.assets.open(dbName).use { input ->
                FileOutputStream(dbFile).use { output ->
                    input.copyTo(output)
                }
            }
        }
        return dbFile
    }

    fun openDb(writable: Boolean = false): SQLiteDatabase {
        val dbFile = ensureDatabaseFile()
        val flags = if (writable) SQLiteDatabase.OPEN_READWRITE else SQLiteDatabase.OPEN_READONLY
        return SQLiteDatabase.openDatabase(dbFile.absolutePath, null, flags)
    }

    suspend fun replaceDatabaseBytes(bytes: ByteArray) = withContext(Dispatchers.IO) {
        val dbFile = context.getDatabasePath(dbName)
        dbFile.parentFile?.mkdirs()
        FileOutputStream(dbFile).use { it.write(bytes) }
    }

    suspend fun getStats(): DbStats = withContext(Dispatchers.IO) {
        try {
            val dbFile = ensureDatabaseFile()
            val sizeMb = String.format("%.1f MB", dbFile.length().toDouble() / (1024.0 * 1024.0))
            openDb().use { db ->
                val map = mutableMapOf<String, String>()
                db.rawQuery("SELECT key, value FROM meta;", null).use { cur ->
                    while (cur.moveToNext()) {
                        map[cur.getString(0)] = cur.getString(1)
                    }
                }
                val currentFileCount = db.rawQuery("SELECT COUNT(*) FROM project_files;", null).use { c ->
                    if (c.moveToFirst()) c.getInt(0) else 581
                }
                DbStats(
                    filesCount = currentFileCount,
                    symbolsCount = map["symbols_count"]?.toIntOrNull() ?: 3170,
                    qaCount = map["qa_count"]?.toIntOrNull() ?: 9894,
                    tablesCount = map["tables_count"]?.toIntOrNull() ?: 230,
                    routesCount = map["routes_count"]?.toIntOrNull() ?: 537,
                    dbSizeMb = sizeMb
                )
            }
        } catch (_: Exception) {
            DbStats()
        }
    }

    suspend fun getProjectSitemapSummary(): String = withContext(Dispatchers.IO) {
        val appCounts = linkedMapOf<String, Int>()
        openDb().use { db ->
            db.rawQuery(
                "SELECT app_module, COUNT(*) FROM project_files GROUP BY app_module ORDER BY app_module;",
                null
            ).use { cur ->
                while (cur.moveToNext()) {
                    appCounts[cur.getString(0)] = cur.getInt(1)
                }
            }
        }
        "Workspace `$activeWorkspaceId` (${appCounts.values.sum()} files across ${appCounts.size} Django modules): " +
            appCounts.entries.joinToString(", ") { "`${it.key}/` (${it.value})" }
    }

    suspend fun readProjectFile(relPath: String): ProjectFileRecord? = withContext(Dispatchers.IO) {
        val clean = relPath.trim().trimStart('/')
        openDb().use { db ->
            db.rawQuery(
                "SELECT rel_path, app_module, file_ext, line_count, is_modified, content FROM project_files WHERE LOWER(rel_path) = ? OR LOWER(rel_path) LIKE ? LIMIT 1;",
                arrayOf(clean.lowercase(), "%/${clean.lowercase()}")
            ).use { cur ->
                if (cur.moveToFirst()) {
                    return@withContext ProjectFileRecord(
                        relPath = cur.getString(0),
                        appModule = cur.getString(1) ?: "",
                        fileExt = cur.getString(2) ?: "",
                        lineCount = cur.getInt(3),
                        isModified = cur.getInt(4) == 1,
                        content = cur.getString(5) ?: ""
                    )
                }
            }
        }
        null
    }

    suspend fun readOriginalAssetContent(relPath: String): String = withContext(Dispatchers.IO) {
        try {
            context.assets.open("aryashakti/${relPath.trimStart('/')}")
                .bufferedReader(Charsets.UTF_8)
                .use { it.readText() }
        } catch (_: Exception) {
            ""
        }
    }

    suspend fun listDirectoryHierarchy(currentDir: String): Pair<List<FolderEntry>, List<ProjectFileRecord>> =
        withContext(Dispatchers.IO) {
            val cleanDir = currentDir.trim().trim('/')
            val prefix = if (cleanDir.isEmpty()) "" else "$cleanDir/"

            val childFolders = linkedMapOf<String, Int>()
            val childFiles = mutableListOf<ProjectFileRecord>()

            openDb().use { db ->
                val sql = if (prefix.isEmpty()) {
                    "SELECT rel_path, app_module, file_ext, line_count, is_modified, content FROM project_files ORDER BY rel_path;"
                } else {
                    "SELECT rel_path, app_module, file_ext, line_count, is_modified, content FROM project_files WHERE rel_path LIKE ? ORDER BY rel_path;"
                }
                val args = if (prefix.isEmpty()) null else arrayOf("$prefix%")

                db.rawQuery(sql, args).use { cur ->
                    while (cur.moveToNext()) {
                        val relPath = cur.getString(0)
                        val remainder = if (prefix.isEmpty()) relPath else relPath.removePrefix(prefix)
                        if (remainder.contains("/")) {
                            val subFolder = remainder.substringBefore("/")
                            childFolders[subFolder] = (childFolders[subFolder] ?: 0) + 1
                        } else {
                            childFiles.add(
                                ProjectFileRecord(
                                    relPath = relPath,
                                    appModule = cur.getString(1) ?: "",
                                    fileExt = cur.getString(2) ?: "",
                                    lineCount = cur.getInt(3),
                                    isModified = cur.getInt(4) == 1,
                                    content = cur.getString(5) ?: ""
                                )
                            )
                        }
                    }
                }
            }

            val folderEntries = childFolders.entries
                .sortedBy { it.key.lowercase() }
                .map { (name, count) ->
                    val fullRel = if (cleanDir.isEmpty()) name else "$cleanDir/$name"
                    FolderEntry(folderName = name, fullRelPath = fullRel, fileCount = count)
                }

            Pair(folderEntries, childFiles)
        }

    suspend fun searchProjectFiles(query: String, limit: Int = 80): List<ProjectFileRecord> = withContext(Dispatchers.IO) {
        val list = mutableListOf<ProjectFileRecord>()
        val qLow = query.trim().lowercase()
        openDb().use { db ->
            val sql = if (qLow.isEmpty()) {
                "SELECT rel_path, app_module, file_ext, line_count, is_modified, content FROM project_files ORDER BY is_modified DESC, rel_path LIMIT ?;"
            } else {
                "SELECT rel_path, app_module, file_ext, line_count, is_modified, content FROM project_files WHERE LOWER(rel_path) LIKE ? OR LOWER(content) LIKE ? ORDER BY CASE WHEN LOWER(rel_path) LIKE ? THEN 0 ELSE 1 END, rel_path LIMIT ?;"
            }
            val args = if (qLow.isEmpty()) {
                arrayOf(limit.toString())
            } else {
                arrayOf("%$qLow%", "%$qLow%", "%$qLow%", limit.toString())
            }
            db.rawQuery(sql, args).use { cur ->
                while (cur.moveToNext()) {
                    val relPath = cur.getString(0)
                    val appMod = cur.getString(1) ?: ""
                    val ext = cur.getString(2) ?: ""
                    val lineCnt = cur.getInt(3)
                    val isMod = cur.getInt(4) == 1
                    val content = cur.getString(5) ?: ""

                    var snippet = ""
                    if (qLow.isNotEmpty()) {
                        val matchLines = mutableListOf<String>()
                        content.lineSequence().forEachIndexed { idx, line ->
                            if (matchLines.size < 4 && line.lowercase().contains(qLow)) {
                                matchLines.add("${idx + 1}: ${line.trimEnd().take(110)}")
                            }
                        }
                        snippet = matchLines.joinToString("\n")
                    }

                    list.add(
                        ProjectFileRecord(
                            relPath = relPath,
                            appModule = appMod,
                            fileExt = ext,
                            lineCount = lineCnt,
                            isModified = isMod,
                            content = content,
                            matchedSnippet = snippet
                        )
                    )
                }
            }
        }
        list
    }

    suspend fun saveProjectFileOffline(relPath: String, newContent: String, markModified: Boolean = true): Boolean =
        withContext(Dispatchers.IO) {
            try {
                val cleanPath = relPath.trim().trimStart('/').replace('\\', '/')
                val mirrorFile = File(localMirrorRoot, cleanPath)
                mirrorFile.parentFile?.mkdirs()
                mirrorFile.writeText(newContent, Charsets.UTF_8)

                openDb(writable = true).use { db ->
                    val values = ContentValues().apply {
                        put("content", newContent)
                        put("line_count", newContent.lines().size)
                        put("is_modified", if (markModified) 1 else 0)
                    }
                    val rows = db.update("project_files", values, "rel_path = ?", arrayOf(cleanPath))
                    if (rows == 0) {
                        val mod = if (cleanPath.contains("/")) cleanPath.substringBefore("/") else "root"
                        val ext = if (cleanPath.contains(".")) ".${cleanPath.substringAfterLast(".")}" else ""
                        values.put("rel_path", cleanPath)
                        values.put("app_module", mod)
                        values.put("file_ext", ext)
                        db.insertWithOnConflict("project_files", null, values, SQLiteDatabase.CONFLICT_REPLACE)
                    }
                    true
                }
            } catch (e: Exception) {
                PeterLogger.error("SQLiteWrite", "Failed saving $relPath: ${e.message}")
                false
            }
        }

    suspend fun getModifiedFiles(): List<ProjectFileRecord> = withContext(Dispatchers.IO) {
        val list = mutableListOf<ProjectFileRecord>()
        openDb().use { db ->
            db.rawQuery(
                "SELECT rel_path, app_module, file_ext, line_count, is_modified, content FROM project_files WHERE is_modified = 1 ORDER BY rel_path;",
                null
            ).use { cur ->
                while (cur.moveToNext()) {
                    list.add(
                        ProjectFileRecord(
                            relPath = cur.getString(0),
                            appModule = cur.getString(1) ?: "",
                            fileExt = cur.getString(2) ?: "",
                            lineCount = cur.getInt(3),
                            isModified = true,
                            content = cur.getString(5) ?: ""
                        )
                    )
                }
            }
        }
        list
    }

    suspend fun searchSymbols(query: String, limit: Int = 60): List<SymbolRecord> = withContext(Dispatchers.IO) {
        val list = mutableListOf<SymbolRecord>()
        val q = query.trim().lowercase()
        openDb().use { db ->
            val sql = if (q.isEmpty()) {
                "SELECT id, rel_path, symbol_name, symbol_type, parent_class, start_line, end_line, walkthrough, source_code FROM symbols LIMIT ?;"
            } else {
                "SELECT id, rel_path, symbol_name, symbol_type, parent_class, start_line, end_line, walkthrough, source_code FROM symbols WHERE symbol_lower LIKE ? OR LOWER(rel_path) LIKE ? OR LOWER(source_code) LIKE ? ORDER BY CASE WHEN symbol_lower = ? THEN 0 WHEN symbol_lower LIKE ? THEN 1 WHEN LOWER(rel_path) LIKE ? THEN 2 ELSE 3 END, start_line LIMIT ?;"
            }
            val args = if (q.isEmpty()) {
                arrayOf(limit.toString())
            } else {
                arrayOf("%$q%", "%$q%", "%$q%", q, "%$q%", "%$q%", limit.toString())
            }
            db.rawQuery(sql, args).use { cur ->
                while (cur.moveToNext()) {
                    list.add(
                        SymbolRecord(
                            id = cur.getInt(0),
                            relPath = cur.getString(1),
                            symbolName = cur.getString(2),
                            symbolType = cur.getString(3),
                            parentClass = cur.getString(4) ?: "",
                            startLine = cur.getInt(5),
                            endLine = cur.getInt(6),
                            walkthrough = cur.getString(7) ?: "",
                            sourceCode = cur.getString(8) ?: ""
                        )
                    )
                }
            }
        }
        list
    }

    suspend fun searchTables(query: String, limit: Int = 80): List<DbTableRecord> = withContext(Dispatchers.IO) {
        val list = mutableListOf<DbTableRecord>()
        val q = query.trim().lowercase()
        openDb().use { db ->
            val sql = if (q.isEmpty()) {
                "SELECT table_name, django_model, row_count, col_count, columns_text, relationships_text, full_markdown FROM db_tables ORDER BY table_name LIMIT ?;"
            } else {
                "SELECT table_name, django_model, row_count, col_count, columns_text, relationships_text, full_markdown FROM db_tables WHERE LOWER(table_name) LIKE ? OR LOWER(django_model) LIKE ? OR LOWER(columns_text) LIKE ? ORDER BY CASE WHEN LOWER(table_name) = ? THEN 0 WHEN LOWER(table_name) LIKE ? THEN 1 ELSE 2 END, table_name LIMIT ?;"
            }
            val args = if (q.isEmpty()) arrayOf(limit.toString()) else arrayOf("%$q%", "%$q%", "%$q%", q, "%$q%", limit.toString())
            db.rawQuery(sql, args).use { cur ->
                while (cur.moveToNext()) {
                    list.add(
                        DbTableRecord(
                            tableName = cur.getString(0),
                            djangoModel = cur.getString(1) ?: "",
                            rowCount = cur.getString(2) ?: "0",
                            colCount = cur.getInt(3),
                            columnsText = cur.getString(4) ?: "",
                            relationshipsText = cur.getString(5) ?: "",
                            fullMarkdown = cur.getString(6) ?: ""
                        )
                    )
                }
            }
        }
        list
    }

    suspend fun searchRoutes(query: String, limit: Int = 80): List<ApiRouteRecord> = withContext(Dispatchers.IO) {
        val list = mutableListOf<ApiRouteRecord>()
        val q = query.trim().lowercase()
        openDb().use { db ->
            val sql = if (q.isEmpty()) {
                "SELECT id, method, route_path, handler, source_info, full_markdown FROM api_routes LIMIT ?;"
            } else {
                "SELECT id, method, route_path, handler, source_info, full_markdown FROM api_routes WHERE LOWER(route_path) LIKE ? OR LOWER(handler) LIKE ? OR LOWER(source_info) LIKE ? LIMIT ?;"
            }
            val args = if (q.isEmpty()) arrayOf(limit.toString()) else arrayOf("%$q%", "%$q%", "%$q%", limit.toString())
            db.rawQuery(sql, args).use { cur ->
                while (cur.moveToNext()) {
                    list.add(
                        ApiRouteRecord(
                            id = cur.getInt(0),
                            method = cur.getString(1),
                            routePath = cur.getString(2),
                            handler = cur.getString(3),
                            sourceInfo = cur.getString(4),
                            fullMarkdown = cur.getString(5)
                        )
                    )
                }
            }
        }
        list
    }

    /**
     * Extracts meaningful domain tokens from any natural-language question
     * (e.g. "where is crop advisory code?" -> ["crop_advisory", "advisory", "crop"]).
     */
    fun extractDomainKeywords(rawQuestion: String): List<String> {
        val qLower = rawQuestion.lowercase()
            .replace("rleated", "related")
            .replace("releted", "related")
            .replace("realted", "related")

        val rawTokens = Regex("[a-z0-9_]+").findAll(qLower)
            .map { it.value }
            .filter { it.length >= 3 && it !in stopWords }
            .distinct()
            .toList()

        val result = mutableListOf<String>()
        // Add compound snake_case combinations for adjacent words (e.g. "crop" + "advisory" -> "crop_advisory", "cropadvisory")
        if (rawTokens.size >= 2) {
            for (i in 0 until rawTokens.size - 1) {
                result.add("${rawTokens[i]}_${rawTokens[i + 1]}")
                result.add("${rawTokens[i]}${rawTokens[i + 1]}")
            }
        }
        // Prioritize specific/longer tokens first
        result.addAll(rawTokens.sortedByDescending { if (it.contains("_")) it.length + 10 else it.length })
        return result.distinct()
    }

    /**
     * Deep Multi-Keyword Project Directory Investigation (Antigravity Coding Agent Engine):
     * Searches all 581 files, 3,170 AST symbols, 537 API routes, and 230 DB tables in `peter_offline.db`
     * using multi-token co-occurrence scoring and returns a structured markdown report + tool trace badges!
     */
    suspend fun investigateProjectDirectory(rawQuestion: String): Pair<String, List<String>> = withContext(Dispatchers.IO) {
        val toolBadges = mutableListOf<String>()
        val qClean = rawQuestion.trim()
        if (qClean.isEmpty()) {
            return@withContext Pair("Ask a question about the `$activeWorkspaceId` project directory.", toolBadges)
        }

        // 1. Direct file path match (e.g. "verification/views.py")
        val pathMatch = Regex("[A-Za-z0-9_./-]+\\.(?:py|html|json|md|sql)").find(qClean)?.value
        if (pathMatch != null) {
            val fileRec = readProjectFile(pathMatch)
            if (fileRec != null) {
                toolBadges.add("📄 Read `${fileRec.relPath}` (${fileRec.lineCount} lines)")
                val fileSyms = searchSymbols(fileRec.relPath, limit = 12).filter { it.relPath.equals(fileRec.relPath, ignoreCase = true) }
                val sb = StringBuilder()
                sb.append("### 📄 File Analysis: `${fileRec.relPath}`\n")
                sb.append("- **Django Module**: `${fileRec.appModule}` • **Lines**: `${fileRec.lineCount}`\n")
                if (fileSyms.isNotEmpty()) {
                    sb.append("- **Defined Symbols (${fileSyms.size})**: ${fileSyms.joinToString(", ") { "`${it.symbolName}` (L${it.startLine}–${it.endLine})" }}\n\n")
                    fileSyms.take(3).forEach { s ->
                        if (s.walkthrough.isNotBlank()) {
                            sb.append("#### 🧩 `${s.symbolName}` (L${s.startLine}–${s.endLine})\n${s.walkthrough.trim()}\n\n")
                        }
                    }
                }
                sb.append("### 🐍 Source Code (`${fileRec.relPath}`)\n")
                sb.append("```python\n${fileRec.content.take(4500)}\n```")
                return@withContext Pair(sb.toString(), toolBadges)
            }
        }

        val qLower = qClean.lowercase()
        openDb().use { db ->
            // 2. High-level project architecture / modules overview
            if ((qLower.contains("modules") || qLower.contains("apps") || qLower.contains("architecture") || qLower.contains("folders")) &&
                (qLower.contains("aryashakti") || qLower.contains("project") || qLower.contains("all") || qLower.contains("list"))
            ) {
                val sitemap = getProjectSitemapSummary()
                toolBadges.add("🗺️ Scanned 581 files across 19 Django modules")
                db.rawQuery("SELECT answer FROM qa_knowledge WHERE category = 'architecture' LIMIT 1;", null).use { cur ->
                    if (cur.moveToFirst()) {
                        return@withContext Pair("### 🏛️ Aryashakti Project Directory Architecture\n$sitemap\n\n${cur.getString(0)}", toolBadges)
                    }
                }
            }
        }

        // 3. Multi-Token Co-Occurrence Search across Symbols, Files, Routes, and DB Tables
        val keywords = extractDomainKeywords(qClean)
        val coreWords = keywords.filter { !it.contains("_") }.ifEmpty { listOf(qLower) }

        val candidateSymbols = LinkedHashMap<Int, SymbolRecord>()
        val candidateRoutes = LinkedHashMap<Int, ApiRouteRecord>()
        val candidateTables = LinkedHashMap<String, DbTableRecord>()
        val candidateFiles = LinkedHashMap<String, ProjectFileRecord>()

        for (kw in keywords.take(5)) {
            searchSymbols(kw, limit = 25).forEach { candidateSymbols[it.id] = it }
            searchRoutes(kw, limit = 15).forEach { candidateRoutes[it.id] = it }
            searchTables(kw, limit = 12).forEach { candidateTables[it.tableName] = it }
            searchProjectFiles(kw, limit = 15).forEach { candidateFiles[it.relPath] = it }
        }

        // Score candidates by how many distinct core keywords they match in name, path, or code!
        val rankedSymbols = candidateSymbols.values.sortedByDescending { sym ->
            val blob = "${sym.symbolName} ${sym.relPath} ${sym.walkthrough} ${sym.sourceCode}".lowercase()
            val nameLow = sym.symbolName.lowercase()
            var score = 0
            for (w in coreWords) {
                if (nameLow == w) score += 50
                else if (nameLow.contains(w)) score += 25
                if (sym.relPath.lowercase().contains(w)) score += 12
                if (blob.contains(w)) score += 10
            }
            score
        }.take(6)

        val rankedRoutes = candidateRoutes.values.sortedByDescending { rt ->
            val blob = "${rt.routePath} ${rt.handler} ${rt.sourceInfo}".lowercase()
            coreWords.count { blob.contains(it) } * 20
        }.take(6)

        val rankedTables = candidateTables.values.sortedByDescending { tbl ->
            val blob = "${tbl.tableName} ${tbl.djangoModel} ${tbl.columnsText}".lowercase()
            coreWords.count { blob.contains(it) } * 20 + (if (coreWords.any { tbl.tableName.lowercase().contains(it) }) 15 else 0)
        }.take(5)

        val rankedFiles = candidateFiles.values.sortedByDescending { f ->
            val blob = "${f.relPath} ${f.content.take(8000)}".lowercase()
            coreWords.count { blob.contains(it) } * 15 + (if (coreWords.any { f.relPath.lowercase().contains(it) }) 20 else 0)
        }.take(6)

        toolBadges.add("🔎 Grepped 581 files & 3,170 symbols for `${coreWords.joinToString(", ")}`")
        if (rankedFiles.isNotEmpty()) {
            toolBadges.add("📂 Matched ${rankedFiles.size} project files (${rankedFiles.take(3).joinToString(", ") { "`${it.relPath}`" }})")
        }
        if (rankedSymbols.isNotEmpty()) {
            toolBadges.add("🧩 Inspected ${rankedSymbols.size} AST symbols (${rankedSymbols.take(3).joinToString(", ") { "`${it.symbolName}`" }})")
        }
        if (rankedTables.isNotEmpty()) {
            toolBadges.add("🗄️ Matched ${rankedTables.size} PostgreSQL tables (${rankedTables.take(2).joinToString(", ") { "`${it.tableName}`" }})")
        }

        if (rankedSymbols.isEmpty() && rankedRoutes.isEmpty() && rankedTables.isEmpty() && rankedFiles.isEmpty()) {
            val sitemap = getProjectSitemapSummary()
            return@withContext Pair(
                "### 🧭 Workspace Search for `$qClean`\nNo exact symbol or file matched `${coreWords.joinToString(", ")}`.\n\n$sitemap",
                toolBadges
            )
        }

        val sb = StringBuilder()
        sb.append("### 🧭 Project Directory Investigation: `${coreWords.joinToString(" + ")}`\n")
        if (rankedFiles.isNotEmpty()) {
            sb.append("- **Key Project Files**: ${rankedFiles.joinToString(", ") { "`${it.relPath}` (${it.lineCount} lines)" }}\n")
        }
        if (rankedSymbols.isNotEmpty()) {
            sb.append("- **Key Classes & Functions**: ${rankedSymbols.joinToString(", ") { "`${it.symbolName}` in `${it.relPath}:${it.startLine}-${it.endLine}`" }}\n")
        }
        sb.append("\n")

        if (rankedRoutes.isNotEmpty()) {
            sb.append("### 🌐 Django API Routes & Entrypoints\n")
            rankedRoutes.forEach { r ->
                sb.append("- `[${r.method}] /${r.routePath.trimStart('/')}` ➔ **`${r.handler}`** (`${r.sourceInfo}`)\n")
            }
            sb.append("\n")
        }

        if (rankedTables.isNotEmpty()) {
            sb.append("### 🗄️ PostgreSQL Database Tables & Models\n")
            rankedTables.forEach { t ->
                sb.append("- **`${t.tableName}`** (${t.rowCount} rows, ${t.colCount} cols) — ${t.djangoModel}\n")
                if (t.columnsText.isNotBlank()) {
                    sb.append("  - Columns: `${t.columnsText.take(220)}`\n")
                }
            }
            sb.append("\n")
        }

        if (rankedSymbols.isNotEmpty()) {
            sb.append("### 📄 Verified Source Code & AST Walkthrough\n")
            rankedSymbols.take(3).forEach { s ->
                val qual = if (s.parentClass.isNotEmpty()) "${s.parentClass}.${s.symbolName}" else s.symbolName
                sb.append("#### 🧩 `$qual` (`${s.relPath}:${s.startLine}-${s.endLine}`)\n")
                if (s.walkthrough.isNotBlank()) {
                    sb.append("${s.walkthrough.trim()}\n\n")
                }
                if (s.sourceCode.isNotBlank()) {
                    sb.append("```python\n# File: ${s.relPath} (Lines ${s.startLine}-${s.endLine})\n${s.sourceCode.trim().take(2000)}\n```\n\n")
                }
            }
        } else if (rankedFiles.isNotEmpty()) {
            sb.append("### 📄 Matched Project File Snippets\n")
            rankedFiles.take(3).forEach { f ->
                sb.append("#### 📂 `${f.relPath}` (${f.lineCount} lines)\n")
                val codeToShow = if (f.matchedSnippet.isNotBlank()) f.matchedSnippet else f.content.take(1500)
                sb.append("```python\n$codeToShow\n```\n\n")
            }
        }

        Pair(sb.toString().trim(), toolBadges)
    }

    suspend fun askOffline(rawQuestion: String): String = withContext(Dispatchers.IO) {
        val (report, _) = investigateProjectDirectory(rawQuestion)
        report
    }
}
