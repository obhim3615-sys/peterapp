package com.example.peterapp

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
import kotlinx.coroutines.launch

/**
 * Git Pull, Git Push, Diff Viewer & Project Importer Tab (`GitWorkspaceTab.kt`).
 *
 * Allows the user to:
 * 1. Switch between `aryashakti` and any imported GitHub project, or import a new GitHub repo (`owner/repo`).
 * 2. Configure Git remote (`owner/repo`), branch, and GitHub Personal Access Token (`ghp_...`).
 * 3. Run `git pull`, `git status` (with unified `+`/`-` diff viewer), `git commit & push`, and `revert`.
 */
@Composable
fun GitWorkspaceTab(
    repository: PeterOfflineRepository,
    gitManager: GitAndProjectManager,
    bridgeServerUrl: String,
    onProjectChanged: (String) -> Unit
) {
    val scope = rememberCoroutineScope()
    var repoUrl by remember { mutableStateOf(gitManager.gitRepoUrl) }
    var branch by remember { mutableStateOf(gitManager.gitBranch) }
    var token by remember { mutableStateOf(gitManager.githubToken) }
    var authorName by remember { mutableStateOf(gitManager.gitAuthorName) }
    var authorEmail by remember { mutableStateOf(gitManager.gitAuthorEmail) }
    var commitMessage by remember { mutableStateOf("Update from Antigravity Mobile Coding Agent") }

    var importRepoInput by remember { mutableStateOf("") }
    var importBranchInput by remember { mutableStateOf("main") }
    var showImportModal by remember { mutableStateOf(false) }

    var projects by remember { mutableStateOf<List<WorkspaceProject>>(gitManager.getProjectsList()) }
    var gitStatuses by remember { mutableStateOf<List<GitFileStatus>>(emptyList()) }
    var selectedDiffFile by remember { mutableStateOf<GitFileStatus?>(null) }
    var isBusy by remember { mutableStateOf(false) }
    var gitConsoleOutput by remember { mutableStateOf("🌿 Ready for Git Pull, Git Push, or GitHub Project Import.") }

    fun refreshStatus() {
        scope.launch {
            projects = gitManager.getProjectsList()
            gitStatuses = gitManager.getGitStatus()
        }
    }

    LaunchedEffect(Unit) {
        refreshStatus()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B0F19))
            .padding(10.dp)
    ) {
        // 1. Active Workspace Project Switcher + Import Project Button
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
                            text = "📦 Active Project: ${repository.activeWorkspaceId}",
                            color = Color(0xFF38BDF8),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "${projects.size} project(s) on phone • Tap a project below to switch",
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp
                        )
                    }
                    Button(
                        onClick = { showImportModal = true },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED)),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Text("📥 Import GitHub Repo", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))

                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    for (proj in projects) {
                        val isCurrent = proj.id == repository.activeWorkspaceId
                        Surface(
                            color = if (isCurrent) Color(0xFF0284C7) else Color(0xFF1E293B),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.clickable {
                                repository.activeWorkspaceId = proj.id
                                repoUrl = proj.repoUrl
                                branch = proj.branch
                                gitManager.gitRepoUrl = proj.repoUrl
                                gitManager.gitBranch = proj.branch
                                onProjectChanged(proj.id)
                                refreshStatus()
                                gitConsoleOutput = "✅ Switched workspace to project `${proj.name}` (${proj.fileCount} files)"
                            }
                        ) {
                            Text(
                                text = "${proj.id} (${proj.fileCount} files)",
                                color = Color.White,
                                fontSize = 11.sp,
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // 2. Git Remote & Pull / Push Controls
        Surface(
            color = Color(0xFF131C2E),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(10.dp)) {
                Text(
                    text = "🌿 Git Remote Configuration & Operations",
                    color = Color(0xFF34D399),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(6.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutlinedTextField(
                        value = repoUrl,
                        onValueChange = {
                            repoUrl = it
                            gitManager.gitRepoUrl = it
                        },
                        label = { Text("GitHub Repo (owner/repo)", fontSize = 10.sp) },
                        modifier = Modifier.weight(1.6f),
                        singleLine = true,
                        textStyle = LocalTextStyle.current.copy(fontSize = 11.sp, color = Color.White)
                    )
                    OutlinedTextField(
                        value = branch,
                        onValueChange = {
                            branch = it
                            gitManager.gitBranch = it
                        },
                        label = { Text("Branch", fontSize = 10.sp) },
                        modifier = Modifier.weight(0.8f),
                        singleLine = true,
                        textStyle = LocalTextStyle.current.copy(fontSize = 11.sp, color = Color.White)
                    )
                }

                Spacer(modifier = Modifier.height(6.dp))

                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutlinedTextField(
                        value = token,
                        onValueChange = {
                            token = it
                            gitManager.githubToken = it
                        },
                        label = { Text("GitHub PAT Token (ghp_...)", fontSize = 10.sp) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        textStyle = LocalTextStyle.current.copy(fontSize = 11.sp, color = Color.White)
                    )
                    OutlinedTextField(
                        value = commitMessage,
                        onValueChange = { commitMessage = it },
                        label = { Text("Commit Message", fontSize = 10.sp) },
                        modifier = Modifier.weight(1.2f),
                        singleLine = true,
                        textStyle = LocalTextStyle.current.copy(fontSize = 11.sp, color = Color.White)
                    )
                }

                Spacer(modifier = Modifier.height(6.dp))

                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutlinedTextField(
                        value = authorName,
                        onValueChange = {
                            authorName = it
                            gitManager.gitAuthorName = it
                        },
                        label = { Text("Git Author Name", fontSize = 10.sp) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        textStyle = LocalTextStyle.current.copy(fontSize = 11.sp, color = Color.White)
                    )
                    OutlinedTextField(
                        value = authorEmail,
                        onValueChange = {
                            authorEmail = it
                            gitManager.gitAuthorEmail = it
                        },
                        label = { Text("Git Author Email", fontSize = 10.sp) },
                        modifier = Modifier.weight(1.2f),
                        singleLine = true,
                        textStyle = LocalTextStyle.current.copy(fontSize = 11.sp, color = Color.White)
                    )
                }

                Text(
                    text = "💡 Git auth is independent: Use any GitHub account or PAT here while keeping your Gemini user ID unchanged.",
                    color = Color(0xFF64748B),
                    fontSize = 10.sp,
                    modifier = Modifier.padding(top = 4.dp, bottom = 4.dp)
                )

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Button(
                        onClick = {
                            isBusy = true
                            gitConsoleOutput = "⬇️ Running git pull origin $branch..."
                            scope.launch {
                                val res = gitManager.gitPull(bridgeServerUrl)
                                isBusy = false
                                gitConsoleOutput = res.getOrElse { "❌ Git Pull Error: ${it.message}" }
                                refreshStatus()
                            }
                        },
                        enabled = !isBusy,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7)),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("⬇️ Git Pull", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }

                    Button(
                        onClick = {
                            isBusy = true
                            gitConsoleOutput = "⬆️ Running git commit & push to $branch..."
                            scope.launch {
                                val res = gitManager.gitCommitAndPush(commitMessage, bridgeServerUrl)
                                isBusy = false
                                gitConsoleOutput = res.getOrElse { "❌ Git Push Error: ${it.message}" }
                                refreshStatus()
                            }
                        },
                        enabled = !isBusy,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF059669)),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("⬆️ Commit & Push", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }

                    OutlinedButton(
                        onClick = { refreshStatus() },
                        enabled = !isBusy
                    ) {
                        Text("🔄 Status (${gitStatuses.size})", fontSize = 11.sp, color = Color.White)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // 3. Git Console Output Banner
        Surface(
            color = Color(0xFF0F172A),
            shape = RoundedCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            SelectionContainer {
                Text(
                    text = gitConsoleOutput,
                    color = Color(0xFF7DD3FC),
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(10.dp)
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // 4. Modified Working Tree Files & Unified Diff Viewer
        if (selectedDiffFile != null) {
            val df = selectedDiffFile!!
            val diffLines = df.unifiedDiff.lines()
            Surface(
                color = Color(0xFF131C2E),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) {
                Column(modifier = Modifier.padding(10.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "🔍 Diff: ${df.relPath} (+${df.addedLines} / -${df.removedLines})",
                            color = Color(0xFF38BDF8),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Button(
                                onClick = {
                                    scope.launch {
                                        gitManager.revertFile(df.relPath)
                                        selectedDiffFile = null
                                        refreshStatus()
                                        gitConsoleOutput = "⏪ Reverted `${df.relPath}` to HEAD."
                                    }
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFDC2626)),
                                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
                            ) {
                                Text("⏪ Revert File", fontSize = 11.sp)
                            }
                            OutlinedButton(
                                onClick = { selectedDiffFile = null },
                                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
                            ) {
                                Text("Close", fontSize = 11.sp, color = Color.White)
                            }
                        }
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    LazyColumn(modifier = Modifier.fillMaxSize()) {
                        item {
                            IdeCodeBlockCard(
                                code = df.unifiedDiff,
                                language = "diff",
                                headerTitle = "${df.relPath} (+${df.addedLines} / -${df.removedLines})",
                                maxVisibleLines = 250
                            )
                        }
                    }
                }
            }
        } else {
            Text(
                text = "📋 Working Tree Modified Files (${gitStatuses.size})",
                color = Color(0xFFE2E8F0),
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                if (gitStatuses.isEmpty()) {
                    item {
                        Text(
                            text = "✨ Working tree clean — edit any file in 📂 Files or via 🤖 Coding Agent to inspect diffs & push.",
                            color = Color(0xFF64748B),
                            fontSize = 12.sp,
                            modifier = Modifier.padding(vertical = 12.dp)
                        )
                    }
                } else {
                    items(gitStatuses) { st ->
                        Surface(
                            color = Color(0xFF131C2E),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { selectedDiffFile = st }
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(12.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = "[${st.statusType}] ${st.relPath}",
                                        color = Color(0xFFFBBF24),
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Text(
                                        text = "+${st.addedLines} additions • -${st.removedLines} deletions (Tap to view diff)",
                                        color = Color(0xFF94A3B8),
                                        fontSize = 11.sp
                                    )
                                }
                                Text("Diff ➔", color = Color(0xFF38BDF8), fontSize = 11.sp)
                            }
                        }
                    }
                }
            }
        }
    }

    if (showImportModal) {
        AlertDialog(
            onDismissRequest = { if (!isBusy) showImportModal = false },
            containerColor = Color(0xFF131C2E),
            title = {
                Text("📥 Import Project from GitHub", color = Color.White, fontSize = 15.sp, fontWeight = FontWeight.Bold)
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        "Import any Django/Python/Kotlin GitHub repository directly onto your phone:",
                        color = Color(0xFFCBD5E1),
                        fontSize = 12.sp
                    )
                    OutlinedTextField(
                        value = importRepoInput,
                        onValueChange = { importRepoInput = it },
                        label = { Text("GitHub owner/repo or URL") },
                        placeholder = { Text("e.g. encode/django-rest-framework") },
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )
                    OutlinedTextField(
                        value = importBranchInput,
                        onValueChange = { importBranchInput = it },
                        label = { Text("Branch (default: main)") },
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if (importRepoInput.isBlank() || isBusy) return@Button
                        isBusy = true
                        scope.launch {
                            val res = gitManager.importGitHubRepository(
                                repoUrlInput = importRepoInput,
                                branchInput = importBranchInput
                            ) { prog ->
                                gitConsoleOutput = prog
                            }
                            isBusy = false
                            showImportModal = false
                            res.onSuccess { wp ->
                                repository.activeWorkspaceId = wp.id
                                repoUrl = wp.repoUrl
                                branch = wp.branch
                                onProjectChanged(wp.id)
                                refreshStatus()
                                gitConsoleOutput = "✅ Imported project `${wp.name}` (${wp.fileCount} files) from GitHub!"
                            }.onFailure { err ->
                                gitConsoleOutput = "❌ Import failed: ${err.message}"
                            }
                        }
                    }
                ) {
                    Text(if (isBusy) "Importing..." else "Import Repo")
                }
            },
            dismissButton = {
                TextButton(onClick = { showImportModal = false }) {
                    Text("Cancel", color = Color(0xFF94A3B8))
                }
            }
        )
    }
}
