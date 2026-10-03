package com.example.peterapp

import android.accounts.Account
import android.accounts.AccountManager
import android.app.Activity
import android.content.Context
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
 * Pure Google Gemini OAuth 2.0 Client (`GoogleOAuthGeminiClient.kt` — < 230 lines).
 *
 * Strictly calls ONLY official Google Gemini (`generativelanguage.googleapis.com` `gemini-2.0-flash` / `gemini-1.5-flash`).
 * Never calls ChatGPT / OpenAI / Pollinations (`gpt-oss-20b`), and never dumps raw HTTP JSON!
 */
class GoogleOAuthGeminiClient(
    private val context: Context,
    private val agentToolExecutor: AgentToolExecutor
) {
    private val prefs = context.getSharedPreferences("peter_oauth_prefs", Context.MODE_PRIVATE)

    companion object {
        const val OAUTH_SCOPE =
            "oauth2:https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/generative-language.retriever"
    }

    var cachedBearerToken: String
        get() = prefs.getString("google_oauth_bearer_token", "") ?: ""
        set(value) {
            prefs.edit().putString("google_oauth_bearer_token", value.trim()).apply()
        }

    var gcpProjectId: String
        get() = prefs.getString("gcp_project_id", "") ?: ""
        set(value) {
            prefs.edit().putString("gcp_project_id", value.trim()).apply()
        }

    suspend fun fetchGoogleAccountOAuthToken(
        activity: Activity,
        accountEmail: String
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            PeterLogger.info("GoogleOAuth", "Requesting Google OAuth 2.0 token for $accountEmail...")
            val am = AccountManager.get(context)
            val account = Account(accountEmail, "com.google")
            if (cachedBearerToken.isNotBlank()) {
                am.invalidateAuthToken("com.google", cachedBearerToken)
            }
            val bundle = am.getAuthToken(account, OAUTH_SCOPE, null, activity, null, null).result
            val token = bundle.getString(AccountManager.KEY_AUTHTOKEN) ?: ""
            if (token.isNotBlank()) {
                cachedBearerToken = token
                PeterLogger.ok("GoogleOAuth", "Obtained Google OAuth token (${token.take(10)}...) for $accountEmail")
                val discoveredProj = discoverGcpProjectId(token)
                if (discoveredProj.isNotBlank()) {
                    gcpProjectId = discoveredProj
                    PeterLogger.ok("GoogleOAuth", "Discovered GCP Project ID: $discoveredProj")
                }
                Result.success(token)
            } else {
                Result.failure(Exception("AccountManager returned empty token"))
            }
        } catch (e: Exception) {
            PeterLogger.error("GoogleOAuth", "OAuth token exception for $accountEmail: ${e.message}")
            Result.failure(e)
        }
    }

    private fun discoverGcpProjectId(bearerToken: String): String {
        return try {
            val conn = (URL("https://cloudresourcemanager.googleapis.com/v1/projects?pageSize=5").openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 5000
                readTimeout = 8000
                setRequestProperty("Authorization", "Bearer $bearerToken")
            }
            if (conn.responseCode in 200..299) {
                val body = BufferedReader(InputStreamReader(conn.inputStream, Charsets.UTF_8)).use { it.readText() }
                val projects = JSONObject(body).optJSONArray("projects")
                if (projects != null && projects.length() > 0) {
                    projects.getJSONObject(0).optString("projectId", "")
                } else ""
            } else ""
        } catch (_: Exception) {
            ""
        }
    }

    suspend fun generateWithOAuthAndTools(
        lightweightTurnMessage: String,
        chatHistory: List<ChatTurn>,
        preExecutedTools: List<String>,
        onStatusUpdate: ((String) -> Unit)? = null
    ): Pair<String, List<String>>? = withContext(Dispatchers.IO) {
        val token = cachedBearerToken
        if (token.isBlank()) {
            return@withContext null
        }

        val executedTools = preExecutedTools.toMutableList()
        val systemInitPrompt = agentToolExecutor.buildOneTimeSessionInitPrompt()

        PeterLogger.info("OAuthGemini", "Calling Official Google Gemini REST API with OAuth Bearer token...")
        onStatusUpdate?.invoke("✨ Calling Google Gemini 2.0 Flash API...")
        val geminiRes = tryGoogleOAuthGeminiApi(
            token = token,
            systemInitPrompt = systemInitPrompt,
            lightweightTurnMessage = lightweightTurnMessage,
            chatHistory = chatHistory,
            executedTools = executedTools,
            onStatusUpdate = onStatusUpdate
        )
        if (geminiRes != null) {
            PeterLogger.ok("OAuthGemini", "Google Gemini API succeeded (${geminiRes.length} chars)")
            return@withContext Pair(geminiRes, executedTools)
        }
        null
    }

    private suspend fun tryGoogleOAuthGeminiApi(
        token: String,
        systemInitPrompt: String,
        lightweightTurnMessage: String,
        chatHistory: List<ChatTurn>,
        executedTools: MutableList<String>,
        onStatusUpdate: ((String) -> Unit)?
    ): String? {
        val systemInstruction = JSONObject().put(
            "parts",
            JSONArray().put(JSONObject().put("text", systemInitPrompt))
        )
        val contents = JSONArray()
        for (turn in chatHistory.dropLast(1).takeLast(6)) {
            if (turn.text.contains("\"id\":\"pllns_") || turn.text.contains("\"gpt-oss-")) continue
            contents.put(
                JSONObject().apply {
                    put("role", if (turn.isUser) "user" else "model")
                    put("parts", JSONArray().put(JSONObject().put("text", turn.text.take(900))))
                }
            )
        }
        contents.put(
            JSONObject().apply {
                put("role", "user")
                put("parts", JSONArray().put(JSONObject().put("text", lightweightTurnMessage)))
            }
        )

        var step = 0
        var lastReply: String? = null
        while (step < 4) {
            step++
            val reqBody = JSONObject().apply {
                put("systemInstruction", systemInstruction)
                put("contents", contents)
                put(
                    "generationConfig",
                    JSONObject().apply {
                        put("temperature", 0.1)
                        put("maxOutputTokens", 2048)
                    }
                )
            }

            val respJson = callStatelessGeminiEndpoint(token, reqBody) ?: return lastReply
            val candidates = respJson.optJSONArray("candidates") ?: return lastReply
            if (candidates.length() == 0) return lastReply

            val contentObj = candidates.getJSONObject(0).optJSONObject("content") ?: return lastReply
            contents.put(contentObj)

            val parts = contentObj.optJSONArray("parts") ?: return lastReply
            val textBuilder = StringBuilder()
            for (i in 0 until parts.length()) {
                val p = parts.getJSONObject(i)
                if (p.has("text")) textBuilder.append(p.getString("text"))
            }
            val replyText = textBuilder.toString().trim()
            if (replyText.isBlank()) return lastReply
            lastReply = replyText

            val directive = agentToolExecutor.parseToolDirective(replyText) ?: return replyText
            val (toolName, toolArgs) = directive
            PeterLogger.tool("OAuthGemini", "Executing @tool:$toolName(${toolArgs.joinToString()})")
            onStatusUpdate?.invoke("⚙️ Gemini Tool Step $step: `@tool:$toolName(${toolArgs.firstOrNull() ?: ""})`...")
            val (badge, toolOutput) = agentToolExecutor.executeToolCall(toolName, toolArgs)
            executedTools.add(badge)

            contents.put(
                JSONObject().apply {
                    put("role", "user")
                    put(
                        "parts",
                        JSONArray().put(
                            JSONObject().put(
                                "text",
                                "Tool `@tool:$toolName` result:\n${toolOutput.take(3500)}\n\nContinue solving the user's request."
                            )
                        )
                    )
                }
            )
        }
        return lastReply
    }

    private fun callStatelessGeminiEndpoint(bearerToken: String, body: JSONObject): JSONObject? {
        val endpoints = listOf(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        )
        for (ep in endpoints) {
            try {
                val bodyStr = body.toString()
                val conn = (URL(ep).openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 8000
                    readTimeout = 30000
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json; charset=utf-8")
                    setRequestProperty("Authorization", "Bearer $bearerToken")
                    if (gcpProjectId.isNotBlank()) {
                        setRequestProperty("x-goog-user-project", gcpProjectId)
                    }
                }
                OutputStreamWriter(conn.outputStream, Charsets.UTF_8).use {
                    it.write(bodyStr)
                    it.flush()
                }
                val code = conn.responseCode
                if (code in 200..299) {
                    val respText = BufferedReader(InputStreamReader(conn.inputStream, Charsets.UTF_8)).use { it.readText() }
                    return JSONObject(respText)
                } else {
                    PeterLogger.warn("OAuthGemini", "Gemini REST HTTP $code from ${ep.substringAfterLast("/")}")
                }
            } catch (e: Exception) {
                PeterLogger.warn("OAuthGemini", "Endpoint error: ${e.message}")
            }
        }
        return null
    }
}
