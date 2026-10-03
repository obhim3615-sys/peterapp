package com.example.peterapp

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Stateful Antigravity Coding Agent Tab (`ChatAgentTab.kt`).
 *
 * - Keeps chat history in `MainActivity` state + SharedPreferences so switching tabs never clears chat.
 * - Uses `PeterOnlineBridge` + `AgentToolExecutor` so the system prompt is sent ONCE per session
 *   and subsequent messages are lightweight turns with autonomous `@tool:...` calls.
 */
@Composable
fun ChatAgentTab(
    chatHistory: MutableList<ChatTurn>,
    onPersistChat: (List<ChatTurn>) -> Unit,
    onResetAgentSession: () -> Unit,
    repository: PeterOfflineRepository,
    onlineBridge: PeterOnlineBridge,
    gitManager: GitAndProjectManager,
    isOnlineMode: Boolean,
    googleEmail: String,
    onOpenGoogleSignIn: () -> Unit,
    onOpenLogsModal: () -> Unit
) {
    val scope = rememberCoroutineScope()
    var inputQuestion by remember { mutableStateOf("") }
    var isThinking by remember { mutableStateOf(false) }
    var streamingProgress by remember { mutableStateOf("") }

    val quickPrompts = listOf(
        "🌿 git status",
        "🚀 manage.py check",
        "🔍 Read verification/views.py and explain add_soil_test_plot_data",
        "💳 Trace payment_order table and Razorpay webhook flow",
        "📂 List root folders and explain the aryashakti architecture"
    )

    fun sendQuestion(q: String) {
        val trimmed = q.trim()
        if (trimmed.isEmpty() || isThinking) return
        chatHistory.add(ChatTurn(isUser = true, text = trimmed))
        onPersistChat(chatHistory)
        inputQuestion = ""
        isThinking = true
        streamingProgress = "⚡ Preparing lightweight Coding Agent turn..."

        scope.launch {
            if (isOnlineMode) {
                val res = onlineBridge.askOnlineWithGoogleAccount(
                    question = trimmed,
                    chatHistory = chatHistory.toList(),
                    onStreamingUpdate = { partial ->
                        streamingProgress = partial
                    }
                )
                chatHistory.add(
                    ChatTurn(
                        isUser = false,
                        text = res.answer,
                        badge = res.sourceLabel
                    )
                )
            } else {
                val ans = withContext(Dispatchers.IO) {
                    repository.askOffline(trimmed)
                }
                chatHistory.add(
                    ChatTurn(
                        isUser = false,
                        text = ans,
                        badge = "📴 Offline SQLite Agent"
                    )
                )
            }
            onPersistChat(chatHistory)
            isThinking = false
            streamingProgress = ""
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B0F19))
            .padding(10.dp)
    ) {
        // Session Status & Active Project Header
        Surface(
            color = Color(0xFF131C2E),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 10.dp, vertical = 7.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "🤖 Workspace: ${repository.activeWorkspaceId} (${gitManager.gitBranch})",
                        color = Color(0xFF38BDF8),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = if (onlineBridge.geminiEngine.isSessionPrimed)
                            "🟢 Stateful Session Primed (Lightweight per-turn messages active)"
                        else
                            "⚡ Ready — Session initializes once on first message",
                        color = Color(0xFF94A3B8),
                        fontSize = 10.sp
                    )
                }

                Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                    Surface(
                        color = if (onlineBridge.geminiEngine.hasGoogleSessionCookies()) Color(0xFF065F46) else Color(0xFF1E3A8A),
                        shape = RoundedCornerShape(6.dp),
                        modifier = Modifier.clickable { onOpenGoogleSignIn() }
                    ) {
                        Text(
                            text = if (onlineBridge.geminiEngine.hasGoogleSessionCookies()) "✨ Gemini OK" else "✨ Gemini Sign-In",
                            color = Color.White,
                            fontSize = 10.5.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 7.dp, vertical = 5.dp)
                        )
                    }
                    Surface(
                        color = Color(0xFF1E293B),
                        shape = RoundedCornerShape(6.dp),
                        modifier = Modifier.clickable { onOpenLogsModal() }
                    ) {
                        Text(
                            text = "📡 Logs",
                            color = Color(0xFF7DD3FC),
                            fontSize = 10.5.sp,
                            modifier = Modifier.padding(horizontal = 7.dp, vertical = 5.dp)
                        )
                    }
                    Surface(
                        color = Color(0xFF3F1D2B),
                        shape = RoundedCornerShape(6.dp),
                        modifier = Modifier.clickable { onResetAgentSession() }
                    ) {
                        Text(
                            text = "🗑️ Reset",
                            color = Color(0xFFFDA4AF),
                            fontSize = 10.5.sp,
                            modifier = Modifier.padding(horizontal = 7.dp, vertical = 5.dp)
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(6.dp))

        // Quick-Action Coding Agent Chips
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            quickPrompts.forEach { chip ->
                Surface(
                    color = Color(0xFF1E293B),
                    shape = RoundedCornerShape(14.dp),
                    modifier = Modifier.clickable { sendQuestion(chip.substringAfter(" ")) }
                ) {
                    Text(
                        text = chip,
                        color = Color(0xFFE2E8F0),
                        fontSize = 11.sp,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Conversation Feed
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            items(chatHistory) { turn ->
                val bgColor = if (turn.isUser) Color(0xFF1E3A8A) else Color(0xFF111827)
                val align = if (turn.isUser) Alignment.End else Alignment.Start
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = align
                ) {
                    Surface(
                        color = bgColor,
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.fillMaxWidth(if (turn.isUser) 0.86f else 0.98f)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = if (turn.isUser) "👤 You (${googleEmail.ifBlank { "Local" }})" else "🤖 Antigravity Coding Agent",
                                    color = if (turn.isUser) Color(0xFF93C5FD) else Color(0xFF34D399),
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                if (turn.badge.isNotBlank()) {
                                    Text(
                                        text = turn.badge,
                                        color = Color(0xFF94A3B8),
                                        fontSize = 10.sp
                                    )
                                }
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            if (turn.isUser) {
                                SelectionContainer {
                                    Text(
                                        text = turn.text,
                                        color = Color(0xFFF1F5F9),
                                        fontSize = 13.sp,
                                        lineHeight = 19.sp
                                    )
                                }
                            } else {
                                AntigravityMarkdownView(markdown = turn.text)
                            }
                        }
                    }
                }
            }

            if (isThinking) {
                item {
                    Surface(
                        color = Color(0xFF1E293B),
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(16.dp),
                                    strokeWidth = 2.dp,
                                    color = Color(0xFF38BDF8)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = "Coding Agent Executing...",
                                    color = Color(0xFF38BDF8),
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                            if (streamingProgress.isNotBlank()) {
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = streamingProgress.takeLast(600),
                                    color = Color(0xFFCBD5E1),
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Input Composer
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = inputQuestion,
                onValueChange = { inputQuestion = it },
                placeholder = {
                    Text(
                        "Ask Coding Agent to read/edit files, git pull/push, or run Django...",
                        fontSize = 12.sp,
                        color = Color(0xFF64748B)
                    )
                },
                modifier = Modifier.weight(1f),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = Color(0xFF38BDF8),
                    unfocusedBorderColor = Color(0xFF334155)
                ),
                maxLines = 3
            )
            Spacer(modifier = Modifier.width(8.dp))
            Button(
                onClick = { sendQuestion(inputQuestion) },
                enabled = !isThinking && inputQuestion.isNotBlank(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7)),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 14.dp)
            ) {
                Text("Send", fontWeight = FontWeight.Bold)
            }
        }
    }
}
