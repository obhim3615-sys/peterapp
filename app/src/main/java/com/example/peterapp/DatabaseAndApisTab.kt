package com.example.peterapp

import android.annotation.SuppressLint
import android.webkit.CookieManager
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.window.Dialog
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Modular Symbols, PostgreSQL Tables & API Routes Explorer + Diagnostic Modals (`DatabaseAndApisTab.kt`).
 */
@Composable
fun DatabaseAndApisTab(
    repository: PeterOfflineRepository
) {
    val scope = rememberCoroutineScope()
    var subTab by remember { mutableIntStateOf(0) } // 0=Symbols, 1=DB Tables, 2=API Routes
    var query by remember { mutableStateOf("") }

    var symbols by remember { mutableStateOf<List<SymbolRecord>>(emptyList()) }
    var tables by remember { mutableStateOf<List<DbTableRecord>>(emptyList()) }
    var routes by remember { mutableStateOf<List<ApiRouteRecord>>(emptyList()) }

    LaunchedEffect(subTab, query) {
        scope.launch {
            when (subTab) {
                0 -> symbols = withContext(Dispatchers.IO) { repository.searchSymbols(query) }
                1 -> tables = withContext(Dispatchers.IO) { repository.searchTables(query) }
                2 -> routes = withContext(Dispatchers.IO) { repository.searchRoutes(query) }
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B0F19))
            .padding(10.dp)
    ) {
        // Sub-tab selector
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            listOf("🧩 Symbols (3,170)", "🗄️ DB Tables (230)", "🌐 APIs (537)").forEachIndexed { idx, title ->
                val active = subTab == idx
                Surface(
                    color = if (active) Color(0xFF0284C7) else Color(0xFF131C2E),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier
                        .weight(1f)
                        .clickable { subTab = idx }
                ) {
                    Text(
                        text = title,
                        color = Color.White,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(vertical = 8.dp, horizontal = 8.dp)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            placeholder = {
                Text("🔎 Filter symbols, PostgreSQL tables, or Django routes...", fontSize = 12.sp)
            },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White
            )
        )

        Spacer(modifier = Modifier.height(8.dp))

        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            when (subTab) {
                0 -> items(symbols) { sym ->
                    var expanded by remember { mutableStateOf(false) }
                    Surface(
                        color = Color(0xFF131C2E),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { expanded = !expanded }
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = "${sym.symbolName} (${sym.symbolType})",
                                        color = Color(0xFF38BDF8),
                                        fontSize = 13.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Text(
                                        text = "📄 ${sym.relPath}:${sym.startLine}-${sym.endLine}",
                                        color = Color(0xFF34D399),
                                        fontSize = 11.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                                Text(
                                    text = if (expanded) "🔼 Hide Code" else "🔽 View Code",
                                    color = Color(0xFF7DD3FC),
                                    fontSize = 11.sp
                                )
                            }
                            if (sym.walkthrough.isNotBlank()) {
                                Spacer(modifier = Modifier.height(6.dp))
                                AntigravityMarkdownView(markdown = sym.walkthrough.take(if (expanded) 1500 else 260))
                            }
                            if (expanded && sym.sourceCode.isNotBlank()) {
                                Spacer(modifier = Modifier.height(8.dp))
                                IdeCodeBlockCard(
                                    code = sym.sourceCode,
                                    language = "python",
                                    startLineNumber = sym.startLine,
                                    headerTitle = sym.relPath
                                )
                            }
                        }
                    }
                }
                1 -> items(tables) { tbl ->
                    var expanded by remember { mutableStateOf(false) }
                    Surface(
                        color = Color(0xFF131C2E),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { expanded = !expanded }
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "🗄️ ${tbl.tableName} (${tbl.rowCount} rows • ${tbl.colCount} cols)",
                                    color = Color(0xFFFBBF24),
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = if (expanded) "🔼" else "🔽 Schema",
                                    color = Color(0xFF38BDF8),
                                    fontSize = 11.sp
                                )
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            AntigravityMarkdownView(
                                markdown = if (expanded) tbl.fullMarkdown else tbl.columnsText.take(300)
                            )
                        }
                    }
                }
                2 -> items(routes) { rt ->
                    var expanded by remember { mutableStateOf(false) }
                    Surface(
                        color = Color(0xFF131C2E),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { expanded = !expanded }
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text(
                                text = "🌐 [${rt.method}] /${rt.routePath.trimStart('/')}",
                                color = Color(0xFFA78BFA),
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                text = "Handler: ${rt.handler} • Source: ${rt.sourceInfo}",
                                color = Color(0xFF94A3B8),
                                fontSize = 11.sp
                            )
                            if (expanded && rt.fullMarkdown.isNotBlank()) {
                                Spacer(modifier = Modifier.height(6.dp))
                                AntigravityMarkdownView(markdown = rt.fullMarkdown)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun LiveDiagnosticLogsModal(
    onDismiss: () -> Unit,
    onRunSelfTest: () -> Unit
) {
    val logEntries = PeterLogger.logs
    Dialog(onDismissRequest = onDismiss) {
        Surface(
            color = Color(0xFF0F172A),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier
                .fillMaxWidth()
                .fillMaxHeight(0.85f)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "📡 Live Gemini & Agent Logs (${logEntries.size})",
                        color = Color(0xFF38BDF8),
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Button(
                            onClick = onRunSelfTest,
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF059669)),
                            contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text("⚡ Ping Test", fontSize = 11.sp)
                        }
                        OutlinedButton(
                            onClick = { PeterLogger.clear() },
                            contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text("Clear", fontSize = 11.sp, color = Color.White)
                        }
                        TextButton(onClick = onDismiss) {
                            Text("✖", color = Color.White)
                        }
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    items(logEntries) { entry ->
                        val color = when (entry.level) {
                            "OK" -> Color(0xFF4ADE80)
                            "ERROR" -> Color(0xFFF87171)
                            "WARN" -> Color(0xFFFBBF24)
                            "TOOL" -> Color(0xFFA78BFA)
                            else -> Color(0xFF93C5FD)
                        }
                        SelectionContainer {
                            Text(
                                text = "[${entry.timestamp}] [${entry.level}/${entry.tag}] ${entry.message}",
                                color = color,
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }
            }
        }
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun GoogleSignInWebModal(
    onDismiss: () -> Unit,
    onSignedIn: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Surface(
            color = Color(0xFF131C2E),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier
                .fillMaxWidth()
                .fillMaxHeight(0.85f)
        ) {
            Column {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("🔐 Google Account Gemini Session", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    Button(onClick = onSignedIn) {
                        Text("Done", fontSize = 11.sp)
                    }
                }
                AndroidView(
                    modifier = Modifier.fillMaxSize(),
                    factory = { ctx ->
                        WebView(ctx).apply {
                            CookieManager.getInstance().setAcceptCookie(true)
                            CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)
                            settings.javaScriptEnabled = true
                            settings.domStorageEnabled = true
                            webViewClient = WebViewClient()
                            loadUrl("https://gemini.google.com/app")
                        }
                    }
                )
            }
        }
    }
}
