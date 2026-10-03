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
import kotlinx.coroutines.launch

/**
 * Modular Django Project Runner Tab (`DjangoRunnerTab.kt`).
 *
 * Allows the user to:
 * 1. Start/Stop the Embedded On-Device Django HTTP Server (`http://127.0.0.1:8085`) right on the phone.
 * 2. Run `python manage.py <command>` (`check`, `showmigrations`, `migrate`, `urls`, `inspectdb`, `test`).
 * 3. Test live HTTP `GET`/`POST` endpoints against the running Django project and inspect live server logs.
 */
@Composable
fun DjangoRunnerTab(
    djangoRunner: DjangoRunnerManager,
    bridgeServerUrl: String
) {
    val scope = rememberCoroutineScope()
    var serverRunning by remember { mutableStateOf(djangoRunner.isServerRunning) }
    var customCommand by remember { mutableStateOf("check") }
    var testEndpointPath by remember { mutableStateOf("/verification/") }
    var testMethod by remember { mutableStateOf("GET") }
    var isExecuting by remember { mutableStateOf(false) }

    var consoleTitle by remember { mutableStateOf("🐍 Django Runner Console") }
    var consoleOutput by remember {
        mutableStateOf(
            "Tap '▶️ Start Django Server' to launch `aryashakti` on http://127.0.0.1:${djangoRunner.serverPort}, or run any `manage.py` command below."
        )
    }

    val quickCommands = listOf(
        "check",
        "showmigrations",
        "migrate",
        "urls",
        "inspectdb",
        "test"
    )

    val sampleEndpoints = listOf(
        "/",
        "/verification/",
        "/payment/",
        "/app_farm/",
        "/warehouses/"
    )

    fun runCmd(cmd: String) {
        if (isExecuting) return
        isExecuting = true
        consoleTitle = "⏳ Running `python manage.py $cmd`..."
        scope.launch {
            val out = djangoRunner.runManagePyCommand(cmd, bridgeServerUrl)
            isExecuting = false
            serverRunning = djangoRunner.isServerRunning
            consoleTitle = "✅ `${out.command}` (${out.elapsedMs}ms • exit=${out.exitCode})"
            consoleOutput = out.outputText
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B0F19))
            .padding(10.dp)
    ) {
        // 1. Embedded On-Device Django Server Card
        Surface(
            color = Color(0xFF131C2E),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(10.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = if (serverRunning)
                                "🟢 Django Server RUNNING on http://127.0.0.1:${djangoRunner.serverPort}"
                            else
                                "⚪ Embedded Django HTTP Server (Stopped)",
                            color = if (serverRunning) Color(0xFF34D399) else Color(0xFF94A3B8),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "Serves all 537 `aryashakti` routes & live view handlers on-device",
                            color = Color(0xFF64748B),
                            fontSize = 11.sp
                        )
                    }

                    Button(
                        onClick = {
                            if (serverRunning) {
                                djangoRunner.stopEmbeddedDjangoServer()
                                serverRunning = djangoRunner.isServerRunning
                                consoleTitle = "🛑 Server Stopped"
                                consoleOutput = "Stopped Django development server at http://127.0.0.1:${djangoRunner.serverPort}/"
                            } else {
                                val ok = djangoRunner.startEmbeddedDjangoServer()
                                serverRunning = djangoRunner.isServerRunning
                                consoleTitle = if (ok) "🚀 Server Started (127.0.0.1:${djangoRunner.serverPort})" else "❌ Server Error"
                                consoleOutput = "Django development server running at http://127.0.0.1:${djangoRunner.serverPort}/"
                            }
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (serverRunning) Color(0xFFDC2626) else Color(0xFF059669)
                        )
                    ) {
                        Text(
                            text = if (serverRunning) "⏹️ Stop Server" else "▶️ Start Django Server",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // 2. manage.py Command Runner Card
        Surface(
            color = Color(0xFF131C2E),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(10.dp)) {
                Text(
                    text = "⚙️ Run `python manage.py` Commands",
                    color = Color(0xFF38BDF8),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(6.dp))

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    quickCommands.forEach { cmd ->
                        Surface(
                            color = Color(0xFF1E293B),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier.clickable {
                                customCommand = cmd
                                runCmd(cmd)
                            }
                        ) {
                            Text(
                                text = "manage.py $cmd",
                                color = Color(0xFFE2E8F0),
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedTextField(
                        value = customCommand,
                        onValueChange = { customCommand = it },
                        label = { Text("python manage.py ...", fontSize = 10.sp) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        textStyle = LocalTextStyle.current.copy(
                            fontFamily = FontFamily.Monospace,
                            fontSize = 12.sp,
                            color = Color.White
                        )
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Button(
                        onClick = { runCmd(customCommand) },
                        enabled = !isExecuting && customCommand.isNotBlank(),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7))
                    ) {
                        Text("▶️ Run", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // 3. Interactive HTTP Endpoint Tester
        Surface(
            color = Color(0xFF131C2E),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(10.dp)) {
                Text(
                    text = "🌐 Test Live Django Endpoint (http://127.0.0.1:${djangoRunner.serverPort})",
                    color = Color(0xFFA78BFA),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    sampleEndpoints.forEach { ep ->
                        Surface(
                            color = Color(0xFF1E293B),
                            shape = RoundedCornerShape(10.dp),
                            modifier = Modifier.clickable { testEndpointPath = ep }
                        ) {
                            Text(
                                text = ep,
                                color = Color(0xFFCBD5E1),
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.height(6.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Surface(
                        color = Color(0xFF1E293B),
                        shape = RoundedCornerShape(6.dp),
                        modifier = Modifier.clickable {
                            testMethod = if (testMethod == "GET") "POST" else "GET"
                        }
                    ) {
                        Text(
                            text = testMethod,
                            color = Color(0xFF38BDF8),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 10.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(6.dp))
                    OutlinedTextField(
                        value = testEndpointPath,
                        onValueChange = { testEndpointPath = it },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        textStyle = LocalTextStyle.current.copy(
                            fontFamily = FontFamily.Monospace,
                            fontSize = 12.sp,
                            color = Color.White
                        )
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Button(
                        onClick = {
                            scope.launch {
                                val resp = djangoRunner.testEndpointRequest(testMethod, testEndpointPath)
                                serverRunning = djangoRunner.isServerRunning
                                consoleTitle = "🌐 $testMethod $testEndpointPath"
                                consoleOutput = resp
                            }
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED))
                    ) {
                        Text("Send", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // 4. Console Output + Live Server Request Log
        Surface(
            color = Color(0xFF0F172A),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
        ) {
            Column(modifier = Modifier.padding(10.dp)) {
                Text(
                    text = consoleTitle,
                    color = Color(0xFF34D399),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(6.dp))
                LazyColumn(modifier = Modifier.fillMaxSize()) {
                    item {
                        SelectionContainer {
                            Text(
                                text = consoleOutput,
                                color = Color(0xFFF1F5F9),
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                lineHeight = 16.sp
                            )
                        }
                    }
                    if (djangoRunner.consoleLogs.isNotEmpty()) {
                        item {
                            Spacer(modifier = Modifier.height(10.dp))
                            Text(
                                text = "=== LIVE SERVER & RUNNER LOGS ===",
                                color = Color(0xFF38BDF8),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        items(djangoRunner.consoleLogs) { logLine ->
                            Text(
                                text = logLine,
                                color = Color(0xFF94A3B8),
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
