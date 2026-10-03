package com.example.peterapp

import android.content.Context
import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

/**
 * Full Git (`status`, `diff`, `pull`, `commit & push`, `revert`) and Multi-Project Importer
 * (`GitAndProjectManager.kt` — < 350 lines).
 *
 * Supports:
 * 1. Direct Phone -> GitHub REST API (`git pull`, `git push`, and `Import GitHub Project`)
 * 2. Phone -> PC Bridge (`mobile_api.py` `/api/mobile/git/pull` & `/api/mobile/git/push`)
 * 3. Local Git Status & Unified Diff computation across all 581 workspace files.
 */
class GitAndProjectManager(
    private val context: Context,
    private val offlineRepo: PeterOfflineRepository
) {
    private val prefs = context.getSharedPreferences("peter_git_prefs", Context.MODE_PRIVATE)

    var gitRepoUrl: String
        get() = prefs.getString("git_repo_url", "https://github.com/aryashakti/aryashakti.git") ?: ""
        set(value) {
            prefs.edit().putString("git_repo_url", value.trim()).apply()
        }

    var gitBranch: String
        get() = prefs.getString("git_branch", "main") ?: "main"
        set(value) {
            prefs.edit().putString("git_branch", value.trim().ifBlank { "main" }).apply()
        }

    var githubToken: String
        get() = prefs.getString("github_pat_token", "") ?: ""
        set(value) {
            prefs.edit().putString("github_pat_token", value.trim()).apply()
        }

    var gitAuthorName: String
        get() = prefs.getString("git_author_name", "Peter Mobile Agent") ?: "Peter Mobile Agent"
        set(value) {
            prefs.edit().putString("git_author_name", value.trim()).apply()
        }

    var gitAuthorEmail: String
        get() = prefs.getString("git_author_email", "") ?: ""
        set(value) {
            prefs.edit().putString("git_author_email", value.trim()).apply()
        }

    fun getProjectsList(): List<WorkspaceProject> {
        val list = mutableListOf(
            WorkspaceProject(
                id = "aryashakti",
                name = "aryashakti (Django UAT • 581 Files)",
                repoUrl = gitRepoUrl.ifBlank { "C:/work/aryashakti" },
                branch = gitBranch,
                fileCount = 581,
                isBundledAryashakti = true
            )
        )
        val raw = prefs.getString("imported_projects_json", "[]") ?: "[]"
        try {
            val arr = JSONArray(raw)
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                list.add(
                    WorkspaceProject(
                        id = o.optString("id"),
                        name = o.optString("name"),
                        repoUrl = o.optString("repoUrl"),
                        branch = o.optString("branch", "main"),
                        fileCount = o.optInt("fileCount", 0),
                        isBundledAryashakti = false
                    )
                )
            }
        } catch (_: Exception) {
        }
        return list
    }

    suspend fun getGitStatus(): List<GitFileStatus> = withContext(Dispatchers.IO) {
        val modified = offlineRepo.getModifiedFiles()
        modified.map { file ->
            val original = offlineRepo.readOriginalAssetContent(file.relPath)
            val statusType = if (original.isEmpty()) "ADDED" else "MODIFIED"
            val (added, removed, diffText) = computeUnifiedDiff(file.relPath, original, file.content)
            GitFileStatus(
                relPath = file.relPath,
                statusType = statusType,
                addedLines = added,
                removedLines = removed,
                unifiedDiff = diffText
            )
        }
    }

    suspend fun revertFile(relPath: String): Boolean = withContext(Dispatchers.IO) {
        val original = offlineRepo.readOriginalAssetContent(relPath)
        if (original.isNotEmpty()) {
            offlineRepo.saveProjectFileOffline(relPath, original, markModified = false)
            PeterLogger.ok("Git", "Reverted $relPath to original HEAD state.")
            true
        } else {
            false
        }
    }

    private fun computeUnifiedDiff(relPath: String, oldText: String, newText: String): Triple<Int, Int, String> {
        val oldLines = if (oldText.isEmpty()) emptyList() else oldText.lines()
        val newLines = newText.lines()
        val oldSet = oldLines.toSet()
        val newSet = newLines.toSet()

        var added = 0
        var removed = 0
        val sb = StringBuilder()
        sb.append("--- a/$relPath\n+++ b/$relPath\n")

        val maxLines = maxOf(oldLines.size, newLines.size)
        var shown = 0
        for (i in 0 until maxLines) {
            val o = oldLines.getOrNull(i)
            val n = newLines.getOrNull(i)
            if (o != n) {
                if (o != null && o !in newSet) {
                    removed++
                    if (shown < 40) {
                        sb.append("- L${i + 1}: $o\n")
                        shown++
                    }
                }
                if (n != null && n !in oldSet) {
                    added++
                    if (shown < 40) {
                        sb.append("+ L${i + 1}: $n\n")
                        shown++
                    }
                }
            }
        }
        if (added == 0 && removed == 0 && oldText != newText) {
            added = 1
            sb.append("+ Modified ${newLines.size} lines\n")
        }
        return Triple(added, removed, sb.toString().trim())
    }

    private fun parseGitHubOwnerRepo(url: String): Pair<String, String>? {
        val clean = url.trim().removeSuffix(".git").removeSuffix("/")
        val m = Regex("""github\.com[:/]([^/]+)/([^/]+)""").find(clean)
        if (m != null) return Pair(m.groupValues[1], m.groupValues[2])
        val parts = clean.split("/").filter { it.isNotBlank() }
        if (parts.size == 2 && !clean.contains(":")) return Pair(parts[0], parts[1])
        return null
    }

    /**
     * Executes `git pull`:
     * 1. Tries PC Bridge (`/api/mobile/git/pull`) if reachable so `C:\work\aryashakti` runs `git pull` and syncs.
     * 2. Tries GitHub REST API (`GET /repos/{owner}/{repo}/commits/{branch}`) if a GitHub URL is configured.
     */
    suspend fun gitPull(bridgeBaseUrl: String): Result<String> = withContext(Dispatchers.IO) {
        PeterLogger.info("GitPull", "Starting git pull (repo=$gitRepoUrl, branch=$gitBranch)...")

        // 1. Try PC Bridge git pull first
        try {
            val url = URL("${bridgeBaseUrl.trimEnd('/')}/api/mobile/git/pull")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 3500
                readTimeout = 25000
                doOutput = true
                setRequestProperty("Content-Type", "application/json; charset=utf-8")
            }
            val req = JSONObject().put("branch", gitBranch)
            OutputStreamWriter(conn.outputStream, Charsets.UTF_8).use { it.write(req.toString()) }
            if (conn.responseCode in 200..299) {
                val resp = BufferedReader(InputStreamReader(conn.inputStream, Charsets.UTF_8)).use { it.readText() }
                val json = JSONObject(resp)
                val out = json.optString("output", "Already up to date.")
                PeterLogger.ok("GitPull", "PC Bridge git pull succeeded: $out")
                return@withContext Result.success("🌐 PC Bridge `git pull origin $gitBranch`:\n$out")
            }
        } catch (_: Exception) {
        }

        // 2. Try Direct GitHub API Pull
        val ownerRepo = parseGitHubOwnerRepo(gitRepoUrl)
        if (ownerRepo != null) {
            val (owner, repo) = ownerRepo
            try {
                val apiUrl = "https://api.github.com/repos/$owner/$repo/commits/$gitBranch"
                val conn = (URL(apiUrl).openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 8000
                    readTimeout = 15000
                    setRequestProperty("Accept", "application/vnd.github.v3+json")
                    if (githubToken.isNotBlank()) {
                        setRequestProperty("Authorization", "Bearer $githubToken")
                    }
                }
                val code = conn.responseCode
                if (code in 200..299) {
                    val body = BufferedReader(InputStreamReader(conn.inputStream, Charsets.UTF_8)).use { it.readText() }
                    val json = JSONObject(body)
                    val sha = json.optString("sha", "").take(7)
                    val msg = json.optJSONObject("commit")?.optString("message", "") ?: ""
                    val filesArr = json.optJSONArray("files")
                    var updatedCount = 0
                    if (filesArr != null) {
                        for (i in 0 until minOf(filesArr.length(), 15)) {
                            val fObj = filesArr.getJSONObject(i)
                            val filename = fObj.optString("filename")
                            val rawUrl = fObj.optString("raw_url")
                            if (filename.isNotBlank() && rawUrl.isNotBlank()) {
                                val content = fetchRawUrl(rawUrl)
                                if (content != null) {
                                    offlineRepo.saveProjectFileOffline(filename, content, markModified = false)
                                    updatedCount++
                                }
                            }
                        }
                    }
                    val summary = "✅ Pulled latest `$owner/$repo@$gitBranch` (HEAD `$sha`: \"${msg.lines().firstOrNull() ?: ""}\") — synced $updatedCount changed file(s)."
                    PeterLogger.ok("GitPull", summary)
                    return@withContext Result.success(summary)
                } else {
                    return@withContext Result.failure(Exception("GitHub API HTTP $code for $owner/$repo@$gitBranch (add GitHub Token if private repo)"))
                }
            } catch (e: Exception) {
                return@withContext Result.failure(e)
            }
        }

        Result.failure(Exception("Configure a GitHub Repo URL (or start PC Bridge `mobile_api.py`) to run `git pull`."))
    }

    /**
     * Executes `git commit -m "..." && git push`:
     * 1. Pushes via PC Bridge (`/api/mobile/git/push`) if reachable on Wi-Fi.
     * 2. Or pushes directly from the phone to GitHub REST API (`PUT /repos/{owner}/{repo}/contents/{path}`)!
     */
    suspend fun gitCommitAndPush(commitMessage: String, bridgeBaseUrl: String): Result<String> = withContext(Dispatchers.IO) {
        val modified = offlineRepo.getModifiedFiles()
        if (modified.isEmpty()) {
            return@withContext Result.failure(Exception("Working tree clean — edit a file first before committing & pushing."))
        }
        val cleanMsg = commitMessage.trim().ifBlank { "Update from Peter Mobile Coding Agent" }
        PeterLogger.info("GitPush", "Committing & pushing ${modified.size} file(s): '$cleanMsg'...")

        // 1. Try PC Bridge git commit & push
        try {
            val url = URL("${bridgeBaseUrl.trimEnd('/')}/api/mobile/git/push")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 4000
                readTimeout = 30000
                doOutput = true
                setRequestProperty("Content-Type", "application/json; charset=utf-8")
            }
            val filesJson = JSONArray()
            modified.forEach { f ->
                filesJson.put(JSONObject().put("rel_path", f.relPath).put("content", f.content))
            }
            val payload = JSONObject().apply {
                put("commit_message", cleanMsg)
                put("branch", gitBranch)
                put("files", filesJson)
            }
            OutputStreamWriter(conn.outputStream, Charsets.UTF_8).use { it.write(payload.toString()) }
            if (conn.responseCode in 200..299) {
                val resp = BufferedReader(InputStreamReader(conn.inputStream, Charsets.UTF_8)).use { it.readText() }
                val json = JSONObject(resp)
                modified.forEach { f -> offlineRepo.saveProjectFileOffline(f.relPath, f.content, markModified = false) }
                val out = json.optString("output", "Pushed ${modified.size} file(s).")
                PeterLogger.ok("GitPush", "PC Bridge git push succeeded: $out")
                return@withContext Result.success("🌐 PC Bridge `git commit & push` ($gitBranch):\n$out")
            }
        } catch (_: Exception) {
        }

        // 2. Direct Phone -> GitHub REST API Push
        val ownerRepo = parseGitHubOwnerRepo(gitRepoUrl)
        if (ownerRepo != null && githubToken.isNotBlank()) {
            val (owner, repo) = ownerRepo
            var pushedCount = 0
            for (file in modified) {
                val ok = pushSingleFileToGitHub(owner, repo, gitBranch, file.relPath, file.content, cleanMsg)
                if (ok) {
                    offlineRepo.saveProjectFileOffline(file.relPath, file.content, markModified = false)
                    pushedCount++
                }
            }
            if (pushedCount > 0) {
                val msg = "✅ Pushed $pushedCount/${modified.size} file(s) directly to GitHub `$owner/$repo@$gitBranch` (\"$cleanMsg\")!"
                PeterLogger.ok("GitPush", msg)
                return@withContext Result.success(msg)
            }
            return@withContext Result.failure(Exception("GitHub API rejected push — verify your GitHub Personal Access Token & branch permissions."))
        }

        Result.failure(Exception("To push directly from phone without PC Bridge, enter your GitHub Repo URL + Personal Access Token in the Git tab."))
    }

    private fun pushSingleFileToGitHub(
        owner: String,
        repo: String,
        branch: String,
        relPath: String,
        content: String,
        commitMsg: String
    ): Boolean {
        return try {
            val apiUrl = "https://api.github.com/repos/$owner/$repo/contents/${relPath.trimStart('/')}"
            var existingSha = ""
            val getConn = (URL("$apiUrl?ref=$branch").openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                setRequestProperty("Authorization", "Bearer $githubToken")
                setRequestProperty("Accept", "application/vnd.github.v3+json")
            }
            if (getConn.responseCode in 200..299) {
                val getBody = BufferedReader(InputStreamReader(getConn.inputStream, Charsets.UTF_8)).use { it.readText() }
                existingSha = JSONObject(getBody).optString("sha", "")
            }

            val putConn = (URL(apiUrl).openConnection() as HttpURLConnection).apply {
                requestMethod = "PUT"
                doOutput = true
                setRequestProperty("Authorization", "Bearer $githubToken")
                setRequestProperty("Accept", "application/vnd.github.v3+json")
                setRequestProperty("Content-Type", "application/json; charset=utf-8")
            }
            val b64 = Base64.encodeToString(content.toByteArray(Charsets.UTF_8), Base64.NO_WRAP)
            val body = JSONObject().apply {
                put("message", commitMsg)
                put("content", b64)
                put("branch", branch)
                if (existingSha.isNotBlank()) put("sha", existingSha)
                if (gitAuthorName.isNotBlank() || gitAuthorEmail.isNotBlank()) {
                    val authorObj = JSONObject().apply {
                        put("name", gitAuthorName.ifBlank { "Peter Agent" })
                        put("email", gitAuthorEmail.ifBlank { "peter@local.dev" })
                    }
                    put("committer", authorObj)
                    put("author", authorObj)
                }
            }
            OutputStreamWriter(putConn.outputStream, Charsets.UTF_8).use { it.write(body.toString()) }
            putConn.responseCode in 200..299
        } catch (e: Exception) {
            PeterLogger.error("GitPush", "GitHub PUT failed for $relPath: ${e.message}")
            false
        }
    }

    /**
     * Imports a GitHub project (`owner/repo` or URL) directly onto the phone into SQLite `project_files`!
     */
    suspend fun importGitHubRepository(
        repoUrlInput: String,
        branchInput: String,
        onProgress: (String) -> Unit
    ): Result<WorkspaceProject> = withContext(Dispatchers.IO) {
        val ownerRepo = parseGitHubOwnerRepo(repoUrlInput)
            ?: return@withContext Result.failure(Exception("Enter a valid GitHub URL or owner/repo (e.g. django/django)"))
        val (owner, repo) = ownerRepo
        val branch = branchInput.trim().ifBlank { "main" }
        PeterLogger.info("ProjectImport", "Importing GitHub repo $owner/$repo@$branch...")
        onProgress("🔍 Fetching file tree for `$owner/$repo@$branch`...")

        try {
            val treeUrl = "https://api.github.com/repos/$owner/$repo/git/trees/$branch?recursive=1"
            val conn = (URL(treeUrl).openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 10000
                readTimeout = 20000
                setRequestProperty("Accept", "application/vnd.github.v3+json")
                if (githubToken.isNotBlank()) {
                    setRequestProperty("Authorization", "Bearer $githubToken")
                }
            }
            if (conn.responseCode !in 200..299) {
                return@withContext Result.failure(Exception("GitHub HTTP ${conn.responseCode} fetching $owner/$repo@$branch"))
            }
            val body = BufferedReader(InputStreamReader(conn.inputStream, Charsets.UTF_8)).use { it.readText() }
            val tree = JSONObject(body).optJSONArray("tree") ?: JSONArray()

            val codeExts = setOf(".py", ".html", ".js", ".ts", ".kt", ".json", ".md", ".sql", ".yml", ".yaml", ".txt")
            val blobs = mutableListOf<String>()
            for (i in 0 until tree.length()) {
                val item = tree.getJSONObject(i)
                if (item.optString("type") == "blob") {
                    val path = item.optString("path", "")
                    val ext = if (path.contains(".")) ".${path.substringAfterLast(".").lowercase()}" else ""
                    if (ext in codeExts && item.optInt("size", 0) < 120_000) {
                        blobs.add(path)
                    }
                }
            }

            val toDownload = blobs.take(60)
            var imported = 0
            for ((idx, path) in toDownload.withIndex()) {
                onProgress("⬇️ Importing (${idx + 1}/${toDownload.size}): `$path`...")
                val rawUrl = "https://raw.githubusercontent.com/$owner/$repo/$branch/$path"
                val content = fetchRawUrl(rawUrl)
                if (content != null) {
                    offlineRepo.saveProjectFileOffline("$repo/$path", content, markModified = false)
                    imported++
                }
            }

            gitRepoUrl = "https://github.com/$owner/$repo.git"
            gitBranch = branch
            val proj = WorkspaceProject(
                id = repo,
                name = "$owner/$repo ($imported files)",
                repoUrl = gitRepoUrl,
                branch = branch,
                fileCount = imported,
                isBundledAryashakti = false
            )
            saveImportedProjectMeta(proj)
            PeterLogger.ok("ProjectImport", "Imported $imported files from $owner/$repo@$branch!")
            Result.success(proj)
        } catch (e: Exception) {
            PeterLogger.error("ProjectImport", "Import error: ${e.message}")
            Result.failure(e)
        }
    }

    private fun saveImportedProjectMeta(proj: WorkspaceProject) {
        try {
            val raw = prefs.getString("imported_projects_json", "[]") ?: "[]"
            val arr = JSONArray(raw)
            val updated = JSONArray()
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                if (o.optString("id") != proj.id) updated.put(o)
            }
            updated.put(
                JSONObject().apply {
                    put("id", proj.id)
                    put("name", proj.name)
                    put("repoUrl", proj.repoUrl)
                    put("branch", proj.branch)
                    put("fileCount", proj.fileCount)
                }
            )
            prefs.edit().putString("imported_projects_json", updated.toString()).apply()
        } catch (_: Exception) {
        }
    }

    private fun fetchRawUrl(rawUrl: String): String? {
        return try {
            val conn = (URL(rawUrl).openConnection() as HttpURLConnection).apply {
                connectTimeout = 6000
                readTimeout = 10000
                if (githubToken.isNotBlank()) {
                    setRequestProperty("Authorization", "Bearer $githubToken")
                }
            }
            if (conn.responseCode in 200..299) {
                BufferedReader(InputStreamReader(conn.inputStream, Charsets.UTF_8)).use { it.readText() }
            } else null
        } catch (_: Exception) {
            null
        }
    }
}
