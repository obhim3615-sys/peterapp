package com.example.peterapp

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
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

private data class FileOutlineSymbol(
    val label: String,
    val lineIndex: Int,
    val isClass: Boolean
)

private fun extractFileOutline(code: String): List<FileOutlineSymbol> {
    val list = mutableListOf<FileOutlineSymbol>()
    val regex = Regex("""^\s*(class|def|async\s+def|fun)\s+([A-Za-z_][A-Za-z0-9_]*)""")
    code.lines().forEachIndexed { idx, line ->
        val m = regex.find(line)
        if (m != null) {
            val kind = m.groupValues[1]
            val name = m.groupValues[2]
            val isCls = kind == "class"
            list.add(
                FileOutlineSymbol(
                    label = "${if (isCls) "🏛️" else "⚡"} $name (L${idx + 1})",
                    lineIndex = idx,
                    isClass = isCls
                )
            )
        }
    }
    return list
}

/**
 * Antigravity IDE File Explorer, Structured Syntax-Highlighted Code Viewer & Code Editor Tab
 * (`FileExplorerEditorTab.kt` — < 460 lines).
 *
 * Features:
 * 1. **📖 IDE Code Viewer Mode (Default)**:
 *    - **Symbol Outline Jump Bar**: Lists all `class` and `def` declarations in the file (`🏛️ Class (L12)`, `⚡ func (L45)`); tapping any symbol scrolls directly to that line!
 *    - **In-File Search Bar (`🔎 Find in file`)**: Highlights matching lines in the gutter & code.
 *    - **60fps Virtualized Line-Numbered + Syntax-Highlighted Code View**: Fixed line-number gutter (`1 │ ...`) + horizontal scroll so code structure and indentation never wrap into unreadable text.
 * 2. **✏️ Edit Code Mode**:
 *    - Full editable code buffer + `✨ AI Edit` + `💾 Save` + `🔄 PC Sync`.
 */
@Composable
fun FileExplorerEditorTab(
    repository: PeterOfflineRepository,
    onlineBridge: PeterOnlineBridge,
    activeProjectName: String
) {
    val scope = rememberCoroutineScope()
    var currentFolder by remember { mutableStateOf("") }
    var searchQuery by remember { mutableStateOf("") }
    var subFolders by remember { mutableStateOf<List<FolderEntry>>(emptyList()) }
    var filesInFolder by remember { mutableStateOf<List<ProjectFileRecord>>(emptyList()) }
    var searchResults by remember { mutableStateOf<List<ProjectFileRecord>>(emptyList()) }

    var openedFile by remember { mutableStateOf<ProjectFileRecord?>(null) }
    var editorText by remember { mutableStateOf("") }
    var isEditMode by remember { mutableStateOf(false) }
    var inFileSearch by remember { mutableStateOf("") }
    var highlightedLineIdx by remember { mutableIntStateOf(-1) }

    var aiEditInstruction by remember { mutableStateOf("") }
    var isAiEditing by remember { mutableStateOf(false) }
    var statusBanner by remember { mutableStateOf("") }

    val codeListState = rememberLazyListState()
    val codeHScrollState = rememberScrollState()

    fun refreshTree() {
        scope.launch {
            if (searchQuery.isBlank()) {
                val (folders, files) = withContext(Dispatchers.IO) {
                    repository.listDirectoryHierarchy(currentFolder)
                }
                subFolders = folders
                filesInFolder = files
            } else {
                val results = withContext(Dispatchers.IO) {
                    repository.searchProjectFiles(searchQuery)
                }
                searchResults = results
            }
        }
    }

    LaunchedEffect(currentFolder, searchQuery, activeProjectName) {
        refreshTree()
    }

    fun openFileInEditor(relPath: String) {
        scope.launch {
            val rec = withContext(Dispatchers.IO) {
                repository.readProjectFile(relPath)
            }
            if (rec != null) {
                openedFile = rec
                editorText = rec.content
                isEditMode = false
                inFileSearch = ""
                highlightedLineIdx = -1
                statusBanner = "📄 Opened `${rec.relPath}` (${rec.lineCount} lines)"
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B0F19))
            .padding(10.dp)
    ) {
        if (openedFile != null) {
            val file = openedFile!!
            val codeLines = remember(editorText) { editorText.lines() }
            val outlineSymbols = remember(editorText) { extractFileOutline(editorText) }

            // Top IDE File Header & Action Toolbar
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
                                text = "🐍 ${file.relPath}",
                                color = Color(0xFF38BDF8),
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                text = "App: ${file.appModule} • ${codeLines.size} lines • ${outlineSymbols.size} symbols",
                                color = Color(0xFF94A3B8),
                                fontSize = 10.5.sp
                            )
                        }

                        Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                            // Toggle between Structured IDE View and Raw Edit Mode
                            Surface(
                                color = if (isEditMode) Color(0xFFD97706) else Color(0xFF1E293B),
                                shape = RoundedCornerShape(6.dp),
                                modifier = Modifier.clickable { isEditMode = !isEditMode }
                            ) {
                                Text(
                                    text = if (isEditMode) "📖 IDE View" else "✏️ Edit",
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp)
                                )
                            }

                            Surface(
                                color = Color(0xFF059669),
                                shape = RoundedCornerShape(6.dp),
                                modifier = Modifier.clickable {
                                    scope.launch {
                                        val ok = withContext(Dispatchers.IO) {
                                            repository.saveProjectFileOffline(file.relPath, editorText)
                                        }
                                        statusBanner = if (ok) {
                                            "✅ Saved `${file.relPath}` & staged in Git!"
                                        } else {
                                            "❌ Failed to save `${file.relPath}`"
                                        }
                                    }
                                }
                            ) {
                                Text(
                                    text = "💾 Save",
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp)
                                )
                            }

                            Surface(
                                color = Color(0xFF0284C7),
                                shape = RoundedCornerShape(6.dp),
                                modifier = Modifier.clickable {
                                    scope.launch {
                                        val res = onlineBridge.pushFileEditToPcBridge(file.relPath, editorText)
                                        statusBanner = res.fold(
                                            onSuccess = { "🌐 Synced to PC: $it" },
                                            onFailure = { "⚠️ Saved on phone (PC offline)" }
                                        )
                                    }
                                }
                            ) {
                                Text(
                                    text = "🔄 PC",
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp)
                                )
                            }

                            Surface(
                                color = Color(0xFF334155),
                                shape = RoundedCornerShape(6.dp),
                                modifier = Modifier.clickable { openedFile = null }
                            ) {
                                Text(
                                    text = "⬅️",
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp)
                                )
                            }
                        }
                    }

                    if (statusBanner.isNotBlank()) {
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(text = statusBanner, color = Color(0xFF34D399), fontSize = 10.5.sp)
                    }

                    // Symbol Outline Jump Bar (Classes & Functions in this file)
                    if (outlineSymbols.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(6.dp))
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Outline:",
                                color = Color(0xFF64748B),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold
                            )
                            outlineSymbols.forEach { sym ->
                                Surface(
                                    color = if (highlightedLineIdx == sym.lineIndex) Color(0xFF0284C7) else Color(0xFF0F172A),
                                    shape = RoundedCornerShape(10.dp),
                                    modifier = Modifier
                                        .border(1.dp, Color(0xFF1E293B), RoundedCornerShape(10.dp))
                                        .clickable {
                                            isEditMode = false
                                            highlightedLineIdx = sym.lineIndex
                                            scope.launch {
                                                codeListState.animateScrollToItem(
                                                    (sym.lineIndex - 2).coerceAtLeast(0)
                                                )
                                            }
                                        }
                                ) {
                                    Text(
                                        text = sym.label,
                                        color = if (sym.isClass) Color(0xFF4EC9B0) else Color(0xFFDCDCAA),
                                        fontSize = 10.5.sp,
                                        fontFamily = FontFamily.Monospace,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(6.dp))

                    // AI Refactor + Find-in-File Row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        OutlinedTextField(
                            value = inFileSearch,
                            onValueChange = { q ->
                                inFileSearch = q
                                if (q.isNotBlank()) {
                                    val firstMatch = codeLines.indexOfFirst { it.contains(q, ignoreCase = true) }
                                    if (firstMatch >= 0) {
                                        highlightedLineIdx = firstMatch
                                        scope.launch {
                                            codeListState.animateScrollToItem((firstMatch - 2).coerceAtLeast(0))
                                        }
                                    }
                                }
                            },
                            placeholder = { Text("🔎 Find in file...", fontSize = 10.5.sp, color = Color(0xFF64748B)) },
                            modifier = Modifier.weight(0.9f),
                            singleLine = true,
                            textStyle = LocalTextStyle.current.copy(fontSize = 11.sp, color = Color.White)
                        )

                        OutlinedTextField(
                            value = aiEditInstruction,
                            onValueChange = { aiEditInstruction = it },
                            placeholder = { Text("✨ AI refactor instruction...", fontSize = 10.5.sp, color = Color(0xFF64748B)) },
                            modifier = Modifier.weight(1.3f),
                            singleLine = true,
                            textStyle = LocalTextStyle.current.copy(fontSize = 11.sp, color = Color.White)
                        )

                        Button(
                            onClick = {
                                if (aiEditInstruction.isBlank() || isAiEditing) return@Button
                                isAiEditing = true
                                statusBanner = "🤖 Coding Agent refactoring `${file.relPath}`..."
                                scope.launch {
                                    val updated = onlineBridge.askStatelessFileEdit(
                                        relPath = file.relPath,
                                        currentCode = editorText,
                                        instruction = aiEditInstruction
                                    )
                                    isAiEditing = false
                                    if (!updated.isNullOrBlank()) {
                                        val cleanCode = Regex("```(?:python|html|json|js)?\\s*([\\s\\S]*?)```")
                                            .find(updated)?.groupValues?.get(1)?.trim()
                                            ?: updated
                                        editorText = cleanCode
                                        statusBanner = "✨ AI Refactor applied! Tap 💾 Save to commit."
                                    } else {
                                        statusBanner = "⚠️ AI Refactor returned empty response."
                                    }
                                }
                            },
                            enabled = !isAiEditing && aiEditInstruction.isNotBlank(),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED)),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 10.dp)
                        ) {
                            Text(if (isAiEditing) "..." else "✨ AI", fontSize = 11.sp)
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            if (isEditMode) {
                // Editable Raw Code Buffer
                OutlinedTextField(
                    value = editorText,
                    onValueChange = { editorText = it },
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    textStyle = LocalTextStyle.current.copy(
                        fontFamily = FontFamily.Monospace,
                        fontSize = 12.sp,
                        color = Color(0xFFF8FAFC),
                        lineHeight = 18.sp
                    ),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = Color(0xFF090D16),
                        unfocusedContainerColor = Color(0xFF090D16),
                        focusedBorderColor = Color(0xFF38BDF8),
                        unfocusedBorderColor = Color(0xFF1E293B)
                    )
                )
            } else {
                // Antigravity IDE Structured Code Viewer (Line Numbers + Syntax Highlighting + Horizontal Scroll)
                Surface(
                    color = Color(0xFF090D16),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                        .border(1.dp, Color(0xFF1E293B), RoundedCornerShape(10.dp))
                ) {
                    SelectionContainer {
                        LazyColumn(
                            state = codeListState,
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(vertical = 6.dp)
                        ) {
                            itemsIndexed(codeLines) { idx, rawLine ->
                                val isMatch = inFileSearch.isNotBlank() && rawLine.contains(inFileSearch, ignoreCase = true)
                                val isJumpTarget = idx == highlightedLineIdx
                                val rowBg = when {
                                    isJumpTarget -> Color(0xFF1E3A5F)
                                    isMatch -> Color(0xFF2E2612)
                                    else -> Color.Transparent
                                }

                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .background(rowBg)
                                        .padding(horizontal = 6.dp, vertical = 0.5.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    // Fixed-Width Line Number Gutter
                                    Text(
                                        text = String.format("%4d", idx + 1),
                                        color = if (isJumpTarget || isMatch) Color(0xFF38BDF8) else Color(0xFF475569),
                                        fontSize = 11.sp,
                                        fontFamily = FontFamily.Monospace,
                                        lineHeight = 18.sp,
                                        modifier = Modifier.width(36.dp)
                                    )
                                    Text(
                                        text = "│ ",
                                        color = Color(0xFF1E293B),
                                        fontSize = 11.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    // Horizontally Scrollable Syntax-Highlighted Code Line
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .horizontalScroll(codeHScrollState)
                                    ) {
                                        val highlighted = remember(rawLine) { highlightCodeLine(rawLine) }
                                        Text(
                                            text = highlighted,
                                            fontSize = 11.5.sp,
                                            fontFamily = FontFamily.Monospace,
                                            lineHeight = 18.sp,
                                            softWrap = false
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else {
            // File Tree Browser Mode
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                placeholder = {
                    Text("🔎 Search files or grep code in $activeProjectName...", fontSize = 12.sp)
                },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "📂 /$activeProjectName/${currentFolder}",
                    color = Color(0xFF38BDF8),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                if (currentFolder.isNotEmpty()) {
                    TextButton(
                        onClick = {
                            currentFolder = currentFolder.substringBeforeLast('/', "").takeIf { currentFolder.contains('/') } ?: ""
                        }
                    ) {
                        Text("⬆️ Up Folder", color = Color(0xFF7DD3FC), fontSize = 12.sp)
                    }
                }
            }

            Spacer(modifier = Modifier.height(4.dp))

            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                if (searchQuery.isBlank()) {
                    items(subFolders) { folder ->
                        Surface(
                            color = Color(0xFF131C2E),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { currentFolder = folder.fullRelPath }
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(12.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                                    Text(text = "📁", fontSize = 16.sp)
                                    Spacer(modifier = Modifier.width(10.dp))
                                    Column {
                                        Text(
                                            text = folder.folderName,
                                            color = Color.White,
                                            fontSize = 13.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Text(
                                            text = "${folder.fileCount} files inside",
                                            color = Color(0xFF94A3B8),
                                            fontSize = 11.sp
                                        )
                                    }
                                }
                                Text(text = "Open ➔", color = Color(0xFF38BDF8), fontSize = 11.sp)
                            }
                        }
                    }

                    items(filesInFolder) { fileRec ->
                        Surface(
                            color = Color(0xFF131C2E),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { openFileInEditor(fileRec.relPath) }
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(12.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                                    Text(text = "🐍", fontSize = 16.sp)
                                    Spacer(modifier = Modifier.width(10.dp))
                                    Column {
                                        Text(
                                            text = fileRec.relPath.substringAfterLast('/'),
                                            color = if (fileRec.isModified) Color(0xFFFBBF24) else Color.White,
                                            fontSize = 13.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Text(
                                            text = "${fileRec.lineCount} lines • ${fileRec.appModule}",
                                            color = Color(0xFF94A3B8),
                                            fontSize = 11.sp
                                        )
                                    }
                                }
                                Text(text = "View Code ➔", color = Color(0xFF34D399), fontSize = 11.sp)
                            }
                        }
                    }
                } else {
                    items(searchResults) { rec ->
                        Surface(
                            color = Color(0xFF131C2E),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { openFileInEditor(rec.relPath) }
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = rec.relPath,
                                            color = Color(0xFF38BDF8),
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Text(
                                            text = "Module: ${rec.appModule} • ${rec.lineCount} lines",
                                            color = Color(0xFF94A3B8),
                                            fontSize = 11.sp
                                        )
                                    }
                                    Text("Open IDE ➔", color = Color(0xFF34D399), fontSize = 11.sp)
                                }
                                if (rec.matchedSnippet.isNotBlank()) {
                                    Spacer(modifier = Modifier.height(6.dp))
                                    IdeCodeBlockCard(
                                        code = rec.matchedSnippet,
                                        language = "python",
                                        headerTitle = "Matched Lines",
                                        maxVisibleLines = 6
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
