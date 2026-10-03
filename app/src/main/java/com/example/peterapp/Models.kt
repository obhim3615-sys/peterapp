package com.example.peterapp

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

data class DbStats(
    val filesCount: Int = 581,
    val symbolsCount: Int = 3170,
    val qaCount: Int = 9894,
    val tablesCount: Int = 230,
    val routesCount: Int = 537,
    val dbSizeMb: String = "20.5 MB"
)

data class ProjectFileRecord(
    val relPath: String,
    val appModule: String,
    val fileExt: String,
    val lineCount: Int,
    val isModified: Boolean = false,
    val content: String = "",
    val matchedSnippet: String = ""
)

data class FolderEntry(
    val folderName: String,
    val fullRelPath: String,
    val fileCount: Int
)

data class SymbolRecord(
    val id: Int,
    val relPath: String,
    val symbolName: String,
    val symbolType: String,
    val parentClass: String,
    val startLine: Int,
    val endLine: Int,
    val walkthrough: String,
    val sourceCode: String
)

data class DbTableRecord(
    val tableName: String,
    val djangoModel: String,
    val rowCount: String,
    val colCount: Int,
    val columnsText: String,
    val relationshipsText: String,
    val fullMarkdown: String
)

data class ApiRouteRecord(
    val id: Int,
    val method: String,
    val routePath: String,
    val handler: String,
    val sourceInfo: String,
    val fullMarkdown: String
)

data class ChatTurn(
    val isUser: Boolean,
    val text: String,
    val badge: String = ""
)

data class GitFileStatus(
    val relPath: String,
    val statusType: String, // "MODIFIED", "ADDED"
    val addedLines: Int,
    val removedLines: Int,
    val unifiedDiff: String
)

data class WorkspaceProject(
    val id: String,
    val name: String,
    val repoUrl: String,
    val branch: String,
    val fileCount: Int,
    val isBundledAryashakti: Boolean = false
)

data class DjangoCommandOutput(
    val command: String,
    val exitCode: Int,
    val outputText: String,
    val elapsedMs: Long
)

data class OnlineBridgeResult(
    val success: Boolean,
    val answer: String,
    val sourceLabel: String,
    val needsGoogleSignIn: Boolean = false
)

fun defaultWelcomeTurn(): ChatTurn = ChatTurn(
    isUser = false,
    text = "👋 **Welcome to Peter Mobile Coding Agent & Django IDE**\n\n" +
        "• **🧠 Stateful Antigravity Agent**: No prompt re-creation per message! The agent keeps continuous session state and autonomously calls `@tool:read_file`, `@tool:edit_file`, `@tool:write_file`, `@tool:grep_files`, `@tool:git_status`, and `@tool:run_django` only when needed.\n" +
        "• **🌿 Git Pull, Git Push & Project Importer**: Open the **`🌿 Git`** tab to inspect diffs, pull latest changes, commit & push, or import any GitHub project!\n" +
        "• **🚀 Run Django Project**: Open the **`🚀 Run`** tab to start the embedded Django server (`127.0.0.1:8085`), run `manage.py` commands (`check`, `showmigrations`, `migrate`, `test`), and test live endpoints!",
    badge = "⚡ Stateful Coding Agent • Git + Django Runner"
)

fun loadPersistedChat(context: Context): List<ChatTurn> {
    return try {
        val prefs = context.getSharedPreferences("peter_chat_history_store", Context.MODE_PRIVATE)
        val raw = prefs.getString("turns_json", null) ?: return listOf(defaultWelcomeTurn())
        val arr = JSONArray(raw)
        if (arr.length() == 0) return listOf(defaultWelcomeTurn())
        val list = mutableListOf<ChatTurn>()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            val txt = o.optString("text", "")
            if (txt.contains("\"id\":\"pllns_") || txt.contains("\"gpt-oss-")) continue
            list.add(
                ChatTurn(
                    isUser = o.optBoolean("isUser", false),
                    text = txt,
                    badge = o.optString("badge", "")
                )
            )
        }
        if (list.isEmpty()) listOf(defaultWelcomeTurn()) else list
    } catch (_: Exception) {
        listOf(defaultWelcomeTurn())
    }
}

fun savePersistedChat(context: Context, turns: List<ChatTurn>) {
    try {
        val arr = JSONArray()
        turns.takeLast(50).forEach { t ->
            arr.put(
                JSONObject().apply {
                    put("isUser", t.isUser)
                    put("text", t.text)
                    put("badge", t.badge)
                }
            )
        }
        context.getSharedPreferences("peter_chat_history_store", Context.MODE_PRIVATE)
            .edit()
            .putString("turns_json", arr.toString())
            .apply()
    } catch (_: Exception) {
    }
}
