package com.example.peterapp

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Antigravity Coding Agent Tool Executor (`AgentToolExecutor.kt` — < 260 lines).
 *
 * 1. `buildOneTimeSessionInitPrompt()` initializes the Coding Agent session ONCE.
 * 2. `tryExecuteDirectIdeCommand(userMessage)` handles direct IDE commands (`git status`,
 *    `git pull`, `git push`, `manage.py ...`) immediately on-device.
 * 3. `buildLightweightTurnMessage(userMessage)` runs multi-keyword project directory search
 *    (`offlineRepo.investigateProjectDirectory`) and attaches compact verified evidence from the
 *    581 files, 3,170 AST symbols, 537 routes, and 230 DB tables.
 * 4. `executeToolCall(toolName, args)` executes real IDE tools on the phone (`read_file`,
 *    `write_file`, `edit_file`, `grep_files`, `list_dir`, `inspect_symbol`, `inspect_table`,
 *    `git_status`, `git_pull`, `git_push`, `run_django`).
 */
class AgentToolExecutor(
    private val offlineRepo: PeterOfflineRepository,
    private val gitManager: GitAndProjectManager,
    private val djangoRunner: DjangoRunnerManager,
    private val bridgeUrlProvider: () -> String = { "http://10.0.2.2:8090" }
) {
    fun parseToolDirective(response: String): Pair<String, List<String>>? {
        val match = Regex("""@tool:([a-zA-Z0-9_]+)\((.*?)\)""").find(response) ?: return null
        val toolName = match.groupValues[1].trim()
        val rawArgs = match.groupValues[2].trim()
        if (rawArgs.isEmpty()) return Pair(toolName, emptyList())

        val args = Regex(""""([^"]*)"|'([^']*)'|([^,]+)""").findAll(rawArgs).map { m ->
            when {
                m.groupValues[1].isNotEmpty() -> m.groupValues[1]
                m.groupValues[2].isNotEmpty() -> m.groupValues[2]
                else -> m.groupValues[3].trim().trim('"', '\'')
            }
        }.toList()
        return Pair(toolName, args)
    }

    suspend fun buildOneTimeSessionInitPrompt(): String = withContext(Dispatchers.IO) {
        val sitemap = offlineRepo.getProjectSitemapSummary()
        buildString {
            append("You are Peter, an Antigravity-grade Google Gemini Coding Agent & Django IDE Architect.\n")
            append("$sitemap\n\n")
            append("You have autonomous local IDE tools on this phone. Emit a `@tool:...` command on its own line whenever you need to read, search, create, edit, run Git, or run Django:\n")
            append("  @tool:read_file(\"verification/views.py\", \"1\", \"140\")\n")
            append("  @tool:write_file(\"app_farm/helpers.py\", \"def helper():\\n    return True\")\n")
            append("  @tool:edit_file(\"verification/views.py\", \"old_code\", \"new_code\")\n")
            append("  @tool:grep_files(\"keyword\")\n")
            append("  @tool:list_dir(\"verification\")\n")
            append("  @tool:inspect_symbol(\"symbol_name\")\n")
            append("  @tool:inspect_table(\"table_name\")\n")
            append("  @tool:git_status()\n")
            append("  @tool:git_pull()\n")
            append("  @tool:git_push(\"commit message\")\n")
            append("  @tool:run_django(\"check\")\n\n")
            append("RULES:\n")
            append("1. Keep conversation stateful — do not repeat system instructions.\n")
            append("2. Structure every response like the Antigravity Coding Agent IDE:\n")
            append("   - Use clear `###` section headers (e.g. `### 🔍 Architecture & Flow`, `### 📄 Source Implementation`).\n")
            append("   - Always place Python, Django, SQL, or JSON code inside properly indented ```python or ```sql fenced blocks.\n")
            append("   - Cite exact file paths (`module/file.py:start-end`), function names, and PostgreSQL tables in `backticks`.\n")
            append("3. Answer strictly based on the project directory evidence provided.")
        }
    }

    /**
     * Immediately executes direct IDE commands (`git status`, `git pull`, `git push`, `manage.py ...`)
     * on the phone so they never need to round-trip through an external LLM.
     */
    suspend fun tryExecuteDirectIdeCommand(userMessage: String): Pair<String, List<String>>? =
        withContext(Dispatchers.IO) {
            val qTrim = userMessage.trim()
            val qLow = qTrim.lowercase()

            if (qLow == "git status" || qLow == "status" || qLow.contains("@tool:git_status")) {
                val (badge, out) = executeToolCall("git_status", emptyList())
                val formatted = "### 🌿 Working Tree Git Status (`${gitManager.gitBranch}`)\n```text\n$out\n```"
                return@withContext Pair(formatted, listOf(badge))
            }
            if (qLow == "git pull" || qLow.startsWith("git pull ") || qLow.contains("@tool:git_pull")) {
                val (badge, out) = executeToolCall("git_pull", emptyList())
                return@withContext Pair("### ⬇️ Git Pull Result\n$out", listOf(badge))
            }
            if (qLow.startsWith("git push") || qLow.contains("@tool:git_push")) {
                val msg = qTrim.removePrefix("git push").trim().ifBlank { "Update from Peter Coding Agent" }
                val (badge, out) = executeToolCall("git_push", listOf(msg))
                return@withContext Pair("### ⬆️ Git Push Result\n$out", listOf(badge))
            }
            if (qLow.startsWith("runserver") || qLow.startsWith("manage.py ") || qLow.startsWith("python manage.py") || qLow.contains("@tool:run_django")) {
                val sub = qTrim.removePrefix("python ").removePrefix("manage.py ").trim().ifBlank { "check" }
                val (badge, out) = executeToolCall("run_django", listOf(sub))
                return@withContext Pair("### 🚀 Django Runner (`manage.py $sub`)\n$out", listOf(badge))
            }
            null
        }

    /**
     * Builds a turn message grounded in the app's local `aryashakti` project directory
     * (`offlineRepo.investigateProjectDirectory`) so Gemini always has the exact files,
     * AST symbols, routes, and DB tables for the user's question!
     */
    suspend fun buildLightweightTurnMessage(userMessage: String): Triple<String, String, List<String>> =
        withContext(Dispatchers.IO) {
            val qTrim = userMessage.trim()
            val (projectReport, toolBadges) = offlineRepo.investigateProjectDirectory(qTrim)

            val turnPrompt = buildString {
                append("User Question: $qTrim\n\n")
                append("=== VERIFIED PROJECT DIRECTORY EVIDENCE (`${offlineRepo.activeWorkspaceId}`) ===\n")
                append(projectReport.take(4800))
                append("\n\nAnswer the user's question thoroughly using the exact files, line numbers, functions, routes, and DB tables above.")
            }
            Triple(turnPrompt, projectReport, toolBadges)
        }

    suspend fun executeToolCall(
        toolName: String,
        args: List<String>
    ): Pair<String, String> = withContext(Dispatchers.IO) {
        PeterLogger.tool("AgentTool", "Executing tool: $toolName(${args.joinToString()})")
        when (toolName.lowercase()) {
            "read_file", "view_file" -> {
                val pathArg = args.getOrNull(0)?.trim() ?: return@withContext Pair("📄 Read File", "Missing path")
                val startLine = args.getOrNull(1)?.trim()?.toIntOrNull() ?: 1
                val endLine = args.getOrNull(2)?.trim()?.toIntOrNull() ?: (startLine + 140)
                val rec = offlineRepo.readProjectFile(pathArg)
                    ?: return@withContext Pair("📄 Not Found: `$pathArg`", "File '$pathArg' not found.")
                val lines = rec.content.lines()
                val sIdx = (startLine - 1).coerceIn(0, (lines.size - 1).coerceAtLeast(0))
                val eIdx = (endLine - 1).coerceIn(sIdx, (lines.size - 1).coerceAtLeast(0))
                val numbered = (sIdx..eIdx).joinToString("\n") { i -> "${i + 1}: ${lines[i]}" }
                Pair(
                    "📄 Viewed `${rec.relPath}` (L${sIdx + 1}–${eIdx + 1})",
                    "File `${rec.relPath}` (lines ${sIdx + 1}-${eIdx + 1} of ${rec.lineCount}):\n```python\n$numbered\n```"
                )
            }

            "write_file", "create_file" -> {
                val pathArg = args.getOrNull(0)?.trim() ?: return@withContext Pair("📝 Write Failed", "Missing path")
                val content = args.getOrNull(1) ?: ""
                val ok = offlineRepo.saveProjectFileOffline(pathArg, content, markModified = true)
                if (ok) {
                    Pair("📝 Wrote `$pathArg` (${content.lines().size} lines)", "Successfully wrote `$pathArg`.")
                } else {
                    Pair("📝 Write Failed `$pathArg`", "Could not write `$pathArg`.")
                }
            }

            "edit_file" -> {
                val pathArg = args.getOrNull(0)?.trim() ?: return@withContext Pair("✏️ Edit Failed", "Missing file path")
                val targetStr = args.getOrNull(1) ?: ""
                val replacementStr = args.getOrNull(2) ?: ""
                val rec = offlineRepo.readProjectFile(pathArg)
                    ?: return@withContext Pair("✏️ Edit Failed", "File '$pathArg' not found.")
                if (targetStr.isNotEmpty() && rec.content.contains(targetStr)) {
                    val updated = rec.content.replaceFirst(targetStr, replacementStr)
                    offlineRepo.saveProjectFileOffline(rec.relPath, updated, markModified = true)
                    Pair(
                        "✏️ Edited `${rec.relPath}`",
                        "Updated `${rec.relPath}` (${updated.lines().size} lines). Check 🌿 Git tab for diff."
                    )
                } else {
                    Pair("✏️ Edit Skipped `${rec.relPath}`", "Target snippet not found verbatim in `${rec.relPath}`.")
                }
            }

            "grep_files", "grep_search" -> {
                val kw = args.getOrNull(0)?.trim() ?: ""
                val hits = offlineRepo.searchProjectFiles(kw, limit = 10)
                val out = if (hits.isEmpty()) "No files matched '$kw'." else {
                    hits.joinToString("\n\n") { f -> "File `${f.relPath}` (${f.lineCount} lines):\n${f.matchedSnippet}" }
                }
                Pair("🔍 Grepped `$kw` (${hits.size} files)", out)
            }

            "list_dir" -> {
                val dir = args.getOrNull(0)?.trim() ?: ""
                val (folders, files) = offlineRepo.listDirectoryHierarchy(dir)
                val out = buildString {
                    append("Directory `/$dir`:\n")
                    folders.forEach { append("  📁 ${it.folderName}/ (${it.fileCount} files)\n") }
                    files.forEach { append("  📄 ${it.relPath.substringAfterLast('/')} (${it.lineCount} lines)\n") }
                }
                Pair("📁 Listed `/$dir` (${folders.size} dirs, ${files.size} files)", out)
            }

            "inspect_symbol" -> {
                val sym = args.getOrNull(0)?.trim() ?: ""
                Pair("🧩 Inspected symbol `$sym`", offlineRepo.askOffline(sym))
            }

            "inspect_table" -> {
                val tbl = args.getOrNull(0)?.trim() ?: ""
                Pair("🗄️ Inspected table `$tbl`", offlineRepo.askOffline(tbl))
            }

            "git_status", "git_diff" -> {
                val statusList = gitManager.getGitStatus()
                val out = if (statusList.isEmpty()) {
                    "On branch ${gitManager.gitBranch}\nworking tree clean (0 modified files in ${offlineRepo.activeWorkspaceId})."
                } else {
                    statusList.joinToString("\n\n") { s ->
                        "${s.statusType}: ${s.relPath} (+${s.addedLines} / -${s.removedLines})\n${s.unifiedDiff}"
                    }
                }
                Pair("🌿 Git Status (${statusList.size} modified)", out)
            }

            "git_pull" -> {
                val res = gitManager.gitPull(bridgeUrlProvider())
                val msg = res.getOrElse { "Git pull note: ${it.message}" }
                Pair("⬇️ Git Pull", msg)
            }

            "git_push" -> {
                val commitMsg = args.getOrNull(0)?.ifBlank { "Update from Peter Agent" } ?: "Update from Peter Agent"
                val res = gitManager.gitCommitAndPush(commitMsg, bridgeUrlProvider())
                val msg = res.getOrElse { "Git push note: ${it.message}" }
                Pair("⬆️ Git Push", msg)
            }

            "run_django" -> {
                val cmd = args.getOrNull(0)?.ifBlank { "check" } ?: "check"
                if (cmd.contains("runserver")) {
                    djangoRunner.startEmbeddedDjangoServer()
                    Pair("🚀 Started Django Server (`127.0.0.1:${djangoRunner.serverPort}`)", "Django development server running at http://127.0.0.1:${djangoRunner.serverPort}/")
                } else {
                    val res = djangoRunner.runManagePyCommand(cmd, bridgeUrlProvider())
                    Pair("🚀 Ran `manage.py $cmd` (${res.elapsedMs}ms)", "```text\n${res.outputText}\n```")
                }
            }

            else -> Pair("⚙️ Tool `$toolName`", "Unknown tool '$toolName'")
        }
    }
}
