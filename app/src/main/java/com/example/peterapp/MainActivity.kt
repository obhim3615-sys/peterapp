package com.example.peterapp

import android.accounts.AccountManager
import android.app.Activity
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Antigravity Mobile Coding Agent & IDE (`MainActivity.kt`).
 *
 * Modular Architecture (every file strictly < 480 lines):
 * - `Models.kt` — Data classes & chat persistence
 * - `PeterLogger.kt` — Real-time diagnostic logger (`📡 Logs`)
 * - `PeterOfflineRepository.kt` — SQLite & file system repository
 * - `GitAndProjectManager.kt` — Git status/diff, Git Pull, Git Push, and GitHub Project Importer
 * - `DjangoRunnerManager.kt` — On-device Django HTTP server (`127.0.0.1:8085`) & `manage.py` runner
 * - `AgentToolExecutor.kt` — One-time session initialization + lightweight per-turn messages + `@tool:...` executor
 * - `GeminiGoogleSessionEngine.kt` — Stateful Gemini session engine (`isSessionPrimed`)
 * - `GoogleOAuthGeminiClient.kt` — OAuth 2.0 & ReAct Coding Agent client
 * - `PeterOnlineBridge.kt` — Online coding agent orchestrator
 * - `ChatAgentTab.kt`, `FileExplorerEditorTab.kt`, `GitWorkspaceTab.kt`, `DjangoRunnerTab.kt`, `DatabaseAndApisTab.kt`
 */
class MainActivity : ComponentActivity() {

    private lateinit var repository: PeterOfflineRepository
    private lateinit var gitManager: GitAndProjectManager
    private lateinit var djangoRunner: DjangoRunnerManager
    private lateinit var agentToolExecutor: AgentToolExecutor
    private lateinit var geminiEngine: GeminiGoogleSessionEngine
    private lateinit var oauthClient: GoogleOAuthGeminiClient
    private lateinit var onlineBridge: PeterOnlineBridge

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        repository = PeterOfflineRepository(applicationContext)
        gitManager = GitAndProjectManager(applicationContext, repository)
        djangoRunner = DjangoRunnerManager(repository)
        agentToolExecutor = AgentToolExecutor(
            offlineRepo = repository,
            gitManager = gitManager,
            djangoRunner = djangoRunner,
            bridgeUrlProvider = { if (::onlineBridge.isInitialized) onlineBridge.bridgeServerUrl else "http://10.0.2.2:8090" }
        )
        geminiEngine = GeminiGoogleSessionEngine(applicationContext)
        oauthClient = GoogleOAuthGeminiClient(applicationContext, agentToolExecutor)
        onlineBridge = PeterOnlineBridge(
            context = applicationContext,
            offlineRepository = repository,
            agentToolExecutor = agentToolExecutor,
            geminiEngine = geminiEngine,
            oauthClient = oauthClient
        )

        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                PeterMobileCodingIdeApp(
                    repository = repository,
                    gitManager = gitManager,
                    djangoRunner = djangoRunner,
                    onlineBridge = onlineBridge
                )
            }
        }
    }
}

@Composable
fun PeterMobileCodingIdeApp(
    repository: PeterOfflineRepository,
    gitManager: GitAndProjectManager,
    djangoRunner: DjangoRunnerManager,
    onlineBridge: PeterOnlineBridge
) {
    val context = LocalContext.current
    val activity = context as? Activity
    val scope = rememberCoroutineScope()

    var isBootstrapping by remember { mutableStateOf(true) }
    var stats by remember { mutableStateOf(DbStats()) }
    var selectedTab by remember { mutableIntStateOf(0) }
    var activeProjectName by remember { mutableStateOf(repository.activeWorkspaceId) }

    var isOnlineMode by remember { mutableStateOf(onlineBridge.isOnlineMode) }
    var googleEmail by remember { mutableStateOf(onlineBridge.googleAccountEmail) }
    var showLogsModal by remember { mutableStateOf(false) }
    var showGoogleWebSignIn by remember { mutableStateOf(false) }

    // Chat state lifted to top-level + SharedPreferences so switching tabs never clears chat!
    val chatHistory = remember {
        mutableStateListOf<ChatTurn>().apply {
            addAll(loadPersistedChat(context))
        }
    }

    val accountPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val pickedEmail = result.data?.getStringExtra(AccountManager.KEY_ACCOUNT_NAME) ?: ""
            if (pickedEmail.isNotBlank()) {
                googleEmail = pickedEmail
                onlineBridge.googleAccountEmail = pickedEmail
                onlineBridge.isOnlineMode = true
                isOnlineMode = true
                if (activity != null) {
                    scope.launch {
                        onlineBridge.oauthClient.fetchGoogleAccountOAuthToken(
                            activity = activity,
                            accountEmail = pickedEmail
                        )
                    }
                }
            }
        }
    }

    LaunchedEffect(Unit) {
        withContext(Dispatchers.IO) {
            stats = repository.getStats()
        }
        onlineBridge.geminiEngine.ensureInitialized()
        isBootstrapping = false
    }

    Scaffold(
        topBar = {
            Surface(color = Color(0xFF0F172A)) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 8.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "⚡ Antigravity Coding Agent",
                                color = Color.White,
                                fontSize = 15.sp,
                                fontWeight = FontWeight.ExtraBold
                            )
                            Text(
                                text = "📦 $activeProjectName • ${stats.filesCount} files • ${stats.symbolsCount} symbols • ${stats.tablesCount} DB tables",
                                color = Color(0xFF38BDF8),
                                fontSize = 10.sp
                            )
                        }

                        Row(
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Account Picker Chip
                            Surface(
                                color = Color(0xFF1E293B),
                                shape = RoundedCornerShape(14.dp),
                                modifier = Modifier.clickable {
                                    try {
                                        val intent: Intent = AccountManager.newChooseAccountIntent(
                                            null,
                                            null,
                                            arrayOf("com.google"),
                                            null,
                                            null,
                                            null,
                                            null
                                        )
                                        accountPickerLauncher.launch(intent)
                                    } catch (_: Exception) {
                                        showGoogleWebSignIn = true
                                    }
                                }
                            ) {
                                Text(
                                    text = if (googleEmail.isNotBlank()) "🟢 ${googleEmail.substringBefore("@")}" else "🔑 Google Login",
                                    color = Color(0xFFE2E8F0),
                                    fontSize = 11.sp,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 5.dp)
                                )
                            }

                            // Online / Offline Toggle
                            Surface(
                                color = if (isOnlineMode) Color(0xFF059669) else Color(0xFF475569),
                                shape = RoundedCornerShape(14.dp),
                                modifier = Modifier.clickable {
                                    isOnlineMode = !isOnlineMode
                                    onlineBridge.isOnlineMode = isOnlineMode
                                }
                            ) {
                                Text(
                                    text = if (isOnlineMode) "🌐 Online" else "📴 Offline",
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 5.dp)
                                )
                            }
                        }
                    }
                }
            }
        },
        bottomBar = {
            NavigationBar(containerColor = Color(0xFF0F172A)) {
                val navItems = listOf(
                    "💬 Agent",
                    "📂 Files",
                    "🌿 Git",
                    "🚀 Run",
                    "🗄️ DB/APIs"
                )
                navItems.forEachIndexed { index, label ->
                    NavigationBarItem(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        icon = {
                            Text(
                                text = label.substringBefore(" "),
                                fontSize = 15.sp
                            )
                        },
                        label = {
                            Text(
                                text = label.substringAfter(" "),
                                fontSize = 11.sp,
                                fontWeight = if (selectedTab == index) FontWeight.Bold else FontWeight.Normal
                            )
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(Color(0xFF0B0F19))
        ) {
            if (isBootstrapping) {
                Column(
                    modifier = Modifier.align(Alignment.Center),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    CircularProgressIndicator(color = Color(0xFF38BDF8))
                    Spacer(modifier = Modifier.height(10.dp))
                    Text("Loading Aryashakti Coding Workspace...", color = Color.White, fontSize = 13.sp)
                }
            } else {
                when (selectedTab) {
                    0 -> ChatAgentTab(
                        chatHistory = chatHistory,
                        onPersistChat = { savePersistedChat(context, it) },
                        onResetAgentSession = {
                            onlineBridge.geminiEngine.resetSession()
                            chatHistory.clear()
                            chatHistory.add(defaultWelcomeTurn())
                            savePersistedChat(context, chatHistory)
                        },
                        repository = repository,
                        onlineBridge = onlineBridge,
                        gitManager = gitManager,
                        isOnlineMode = isOnlineMode,
                        googleEmail = googleEmail,
                        onOpenGoogleSignIn = { showGoogleWebSignIn = true },
                        onOpenLogsModal = { showLogsModal = true }
                    )
                    1 -> FileExplorerEditorTab(
                        repository = repository,
                        onlineBridge = onlineBridge,
                        activeProjectName = activeProjectName
                    )
                    2 -> GitWorkspaceTab(
                        repository = repository,
                        gitManager = gitManager,
                        bridgeServerUrl = onlineBridge.bridgeServerUrl,
                        onProjectChanged = { newProj ->
                            activeProjectName = newProj
                            onlineBridge.geminiEngine.resetSession()
                            scope.launch {
                                stats = withContext(Dispatchers.IO) { repository.getStats() }
                            }
                        }
                    )
                    3 -> DjangoRunnerTab(
                        djangoRunner = djangoRunner,
                        bridgeServerUrl = onlineBridge.bridgeServerUrl
                    )
                    4 -> DatabaseAndApisTab(
                        repository = repository
                    )
                }
            }
        }
    }

    if (showLogsModal) {
        LiveDiagnosticLogsModal(
            onDismiss = { showLogsModal = false },
            onRunSelfTest = {
                scope.launch {
                    onlineBridge.askOnlineWithGoogleAccount(
                        question = "Ping check: confirm Coding Agent is online.",
                        chatHistory = emptyList()
                    )
                }
            }
        )
    }

    if (showGoogleWebSignIn) {
        GoogleSignInWebModal(
            onDismiss = { showGoogleWebSignIn = false },
            onSignedIn = {
                showGoogleWebSignIn = false
                onlineBridge.geminiEngine.ensureInitialized()
            }
        )
    }
}
