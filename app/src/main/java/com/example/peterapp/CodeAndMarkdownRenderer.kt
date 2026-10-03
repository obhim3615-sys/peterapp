package com.example.peterapp

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Antigravity IDE Code Syntax Highlighter & Structured Markdown Renderer
 * (`CodeAndMarkdownRenderer.kt` — < 380 lines).
 *
 * Makes code inside `peterApp` (both in Chat Agent responses, File Viewer, and DB/Symbol cards)
 * look and behave like the Antigravity Coding Agent IDE:
 * - VS Code / JetBrains Dark Modern syntax highlighting for Python, Django, SQL, JSON, and Diffs.
 * - Fixed line-number gutter (`1..N`) + horizontal scroll so indentation never wraps into messy text.
 * - One-tap `📋 Copy` and `📂 Open File` actions on code blocks.
 * - Structured Markdown rendering (headings, bullet lists, inline `code` pills, and collapsible tool traces).
 */

private val PY_KEYWORDS = setOf(
    "def", "class", "import", "from", "return", "yield", "async", "await",
    "if", "elif", "else", "for", "while", "break", "continue", "pass",
    "try", "except", "finally", "raise", "with", "as", "lambda", "in", "is",
    "not", "and", "or", "True", "False", "None", "self", "cls", "global",
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "INNER", "ORDER", "BY", "GROUP",
    "INSERT", "UPDATE", "DELETE", "CREATE", "TABLE", "PRIMARY", "KEY", "FOREIGN",
    "fun", "val", "var", "object", "interface", "package", "override", "suspend"
)

private val TOKEN_REGEX = Regex(
    """(#.*$|//.*$)|("{3}[\s\S]*?"{3}|'{3}[\s\S]*?'{3}|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|(@[A-Za-z_][A-Za-z0-9_.]*)|\b([A-Za-z_][A-Za-z0-9_]*)\b|\b(\d+(?:\.\d+)?)\b""",
    RegexOption.MULTILINE
)

fun highlightCodeLine(line: String, isDiff: Boolean = false): AnnotatedString {
    if (isDiff) {
        return buildAnnotatedString {
            when {
                line.startsWith("+") && !line.startsWith("+++") ->
                    withStyle(SpanStyle(color = Color(0xFF4ADE80), fontWeight = FontWeight.SemiBold)) { append(line) }
                line.startsWith("-") && !line.startsWith("---") ->
                    withStyle(SpanStyle(color = Color(0xFFF87171))) { append(line) }
                line.startsWith("@@") || line.startsWith("---") || line.startsWith("+++") ->
                    withStyle(SpanStyle(color = Color(0xFF38BDF8), fontWeight = FontWeight.Bold)) { append(line) }
                else ->
                    withStyle(SpanStyle(color = Color(0xFFE2E8F0))) { append(line) }
            }
        }
    }

    return buildAnnotatedString {
        var lastIdx = 0
        var prevKeyword = ""
        for (match in TOKEN_REGEX.findAll(line)) {
            if (match.range.first > lastIdx) {
                withStyle(SpanStyle(color = Color(0xFFE2E8F0))) {
                    append(line.substring(lastIdx, match.range.first))
                }
            }
            val full = match.value
            when {
                match.groups[1] != null -> {
                    // Comment
                    withStyle(SpanStyle(color = Color(0xFF6A9955), fontStyle = FontStyle.Italic)) {
                        append(full)
                    }
                }
                match.groups[2] != null -> {
                    // String literal
                    withStyle(SpanStyle(color = Color(0xFFCE9178))) {
                        append(full)
                    }
                }
                match.groups[3] != null -> {
                    // Decorator (@login_required, @tool, etc.)
                    withStyle(SpanStyle(color = Color(0xFFDCDCAA), fontWeight = FontWeight.SemiBold)) {
                        append(full)
                    }
                }
                match.groups[4] != null -> {
                    // Identifier or keyword
                    val word = match.groups[4]!!.value
                    val afterChar = line.getOrNull(match.range.last + 1)
                    val style = when {
                        word in PY_KEYWORDS -> {
                            prevKeyword = word
                            SpanStyle(color = Color(0xFFC586C0), fontWeight = FontWeight.Bold)
                        }
                        prevKeyword == "def" || prevKeyword == "fun" -> {
                            prevKeyword = ""
                            SpanStyle(color = Color(0xFFDCDCAA), fontWeight = FontWeight.Bold)
                        }
                        prevKeyword == "class" -> {
                            prevKeyword = ""
                            SpanStyle(color = Color(0xFF4EC9B0), fontWeight = FontWeight.Bold)
                        }
                        afterChar == '(' -> {
                            SpanStyle(color = Color(0xFFDCDCAA))
                        }
                        word.first().isUpperCase() -> {
                            SpanStyle(color = Color(0xFF4EC9B0))
                        }
                        else -> {
                            SpanStyle(color = Color(0xFF9CDCFE))
                        }
                    }
                    withStyle(style) { append(full) }
                }
                match.groups[5] != null -> {
                    // Numeric literal
                    withStyle(SpanStyle(color = Color(0xFFB5CEA8))) {
                        append(full)
                    }
                }
                else -> {
                    withStyle(SpanStyle(color = Color(0xFFE2E8F0))) { append(full) }
                }
            }
            lastIdx = match.range.last + 1
        }
        if (lastIdx < line.length) {
            withStyle(SpanStyle(color = Color(0xFFE2E8F0))) {
                append(line.substring(lastIdx))
            }
        }
    }
}

fun formatInlineMarkdown(text: String): AnnotatedString {
    val inlineRegex = Regex("""(`[^`]+`|\*\*[^*]+\*\*)""")
    return buildAnnotatedString {
        var cursor = 0
        for (m in inlineRegex.findAll(text)) {
            if (m.range.first > cursor) {
                append(text.substring(cursor, m.range.first))
            }
            val token = m.value
            if (token.startsWith("`") && token.endsWith("`") && token.length >= 2) {
                val inner = token.substring(1, token.length - 1)
                withStyle(
                    SpanStyle(
                        color = Color(0xFF38BDF8),
                        background = Color(0xFF1E293B),
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.SemiBold
                    )
                ) {
                    append(" $inner ")
                }
            } else if (token.startsWith("**") && token.endsWith("**") && token.length >= 4) {
                val inner = token.substring(2, token.length - 2)
                withStyle(SpanStyle(color = Color(0xFFF8FAFC), fontWeight = FontWeight.Bold)) {
                    append(inner)
                }
            } else {
                append(token)
            }
            cursor = m.range.last + 1
        }
        if (cursor < text.length) {
            append(text.substring(cursor))
        }
    }
}

/**
 * Antigravity IDE Code Block Card with Header, Copy Button, Line Numbers, Syntax Highlighting,
 * and Horizontal Scrolling so long code lines never wrap into unreadable text.
 */
@Composable
fun IdeCodeBlockCard(
    code: String,
    language: String = "python",
    startLineNumber: Int = 1,
    headerTitle: String = "",
    maxVisibleLines: Int = 85
) {
    val context = LocalContext.current
    var copied by remember { mutableStateOf(false) }
    var isExpanded by remember { mutableStateOf(false) }

    val rawLines = remember(code) {
        code.trimEnd().lines().map { line ->
            // Strip pre-numbered prefixes like "12: def foo" if already embedded so we don't double-number
            val stripped = Regex("""^\s*\d+:\s?(.*)$""").find(line)?.groupValues?.get(1) ?: line
            stripped
        }
    }
    val isDiff = language.equals("diff", ignoreCase = true)
    val displayLines = if (isExpanded || rawLines.size <= maxVisibleLines) rawLines else rawLines.take(maxVisibleLines)

    Surface(
        color = Color(0xFF090D16),
        shape = RoundedCornerShape(10.dp),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFF1E293B), RoundedCornerShape(10.dp))
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            // Top IDE Code Header Bar
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFF131C2E))
                    .padding(horizontal = 10.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Surface(
                        color = Color(0xFF1E293B),
                        shape = RoundedCornerShape(4.dp)
                    ) {
                        Text(
                            text = language.uppercase().ifBlank { "CODE" },
                            color = Color(0xFF38BDF8),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                    Text(
                        text = if (headerTitle.isNotBlank()) "$headerTitle • ${rawLines.size} lines" else "${rawLines.size} lines",
                        color = Color(0xFF94A3B8),
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Surface(
                    color = if (copied) Color(0xFF065F46) else Color(0xFF1E293B),
                    shape = RoundedCornerShape(6.dp),
                    modifier = Modifier.clickable {
                        val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
                        cm?.setPrimaryClip(ClipData.newPlainText("code", code))
                        copied = true
                    }
                ) {
                    Text(
                        text = if (copied) "✅ Copied" else "📋 Copy Code",
                        color = Color(0xFFE2E8F0),
                        fontSize = 10.sp,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }

            // Horizontally Scrollable Code Body with Fixed Line-Number Gutter
            val hScroll = rememberScrollState()
            SelectionContainer {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(hScroll)
                        .padding(vertical = 8.dp)
                ) {
                    // Line Numbers Gutter
                    Column(
                        modifier = Modifier
                            .padding(start = 8.dp, end = 6.dp),
                        horizontalAlignment = Alignment.End
                    ) {
                        displayLines.indices.forEach { idx ->
                            Text(
                                text = "${startLineNumber + idx}",
                                color = Color(0xFF475569),
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                lineHeight = 18.sp
                            )
                        }
                    }

                    // Subtle Vertical Gutter Divider
                    Box(
                        modifier = Modifier
                            .width(1.dp)
                            .height((displayLines.size * 18).dp)
                            .background(Color(0xFF1E293B))
                    )

                    // Syntax-Highlighted Code Lines
                    Column(
                        modifier = Modifier.padding(start = 10.dp, end = 16.dp)
                    ) {
                        displayLines.forEach { line ->
                            val highlighted = remember(line, isDiff) { highlightCodeLine(line, isDiff) }
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

            if (rawLines.size > maxVisibleLines) {
                Surface(
                    color = Color(0xFF131C2E),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { isExpanded = !isExpanded }
                ) {
                    Text(
                        text = if (isExpanded) "🔼 Collapse Code Block" else "🔽 Show All ${rawLines.size} Lines (+${rawLines.size - maxVisibleLines} more)",
                        color = Color(0xFF38BDF8),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                    )
                }
            }
        }
    }
}

private sealed class MarkdownSegment {
    data class ToolTraceBlock(val header: String, val steps: List<String>) : MarkdownSegment()
    data class CodeBlock(val language: String, val code: String) : MarkdownSegment()
    data class ProseBlock(val lines: List<String>) : MarkdownSegment()
}

private val CODE_LINE_START_REGEX = Regex(
    """^(\s{4,}\S.*|(?:def|class|async\s+def|from|import|return|yield|if|elif|else:|for|while|try:|except|finally:|with|@[A-Za-z_]|SELECT\s|INSERT\s|UPDATE\s|CREATE\s+TABLE)\b.*|[A-Za-z_][A-Za-z0-9_.]*\s*=\s*.+|\d+:\s+.*)$"""
)

private fun appendProseWithAutoCodeDetection(prose: String, out: MutableList<MarkdownSegment>) {
    val lines = prose.lines()
    val proseBuf = mutableListOf<String>()
    val codeBuf = mutableListOf<String>()

    fun flushProse() {
        if (proseBuf.isNotEmpty()) {
            out.add(MarkdownSegment.ProseBlock(proseBuf.toList()))
            proseBuf.clear()
        }
    }

    fun flushCode() {
        if (codeBuf.size >= 2) {
            out.add(MarkdownSegment.CodeBlock("python", codeBuf.joinToString("\n")))
        } else if (codeBuf.isNotEmpty()) {
            proseBuf.addAll(codeBuf)
        }
        codeBuf.clear()
    }

    for (line in lines) {
        val trimmed = line.trim()
        if (trimmed.equals("Python", ignoreCase = true) || trimmed.equals("Copy code", ignoreCase = true)) {
            continue
        }
        val looksLikeCode = CODE_LINE_START_REGEX.matches(line) ||
            (codeBuf.isNotEmpty() && (line.startsWith("  ") || trimmed.startsWith("#") || trimmed.endsWith(":") || trimmed.endsWith(")") || trimmed.endsWith("]") || trimmed.endsWith("}") || trimmed.isEmpty()))

        if (looksLikeCode) {
            if (codeBuf.isEmpty()) flushProse()
            codeBuf.add(line)
        } else {
            if (codeBuf.isNotEmpty()) flushCode()
            proseBuf.add(line)
        }
    }
    flushCode()
    flushProse()
}

private fun parseMarkdownSegments(raw: String): List<MarkdownSegment> {
    val segments = mutableListOf<MarkdownSegment>()
    var body = raw.trim()

    // Extract optional Antigravity Coding Agent Trace header block separated by "---"
    if (body.startsWith("**🛠️") && body.contains("\n---\n")) {
        val tracePart = body.substringBefore("\n---\n").trim()
        body = body.substringAfter("\n---\n").trim()
        val traceLines = tracePart.lines()
        val header = traceLines.firstOrNull()?.replace("**", "") ?: "🛠️ Coding Agent Actions"
        val steps = traceLines.drop(1).map { it.trim().removePrefix("•").trim() }.filter { it.isNotBlank() }
        segments.add(MarkdownSegment.ToolTraceBlock(header, steps))
    }

    val fenceRegex = Regex("```([a-zA-Z0-9_+-]*)\\s*\\n([\\s\\S]*?)```")
    var lastIdx = 0
    for (match in fenceRegex.findAll(body)) {
        if (match.range.first > lastIdx) {
            val prose = body.substring(lastIdx, match.range.first).trim()
            if (prose.isNotBlank()) {
                appendProseWithAutoCodeDetection(prose, segments)
            }
        }
        val lang = match.groupValues[1].ifBlank { "python" }
        val codeContent = match.groupValues[2]
        segments.add(MarkdownSegment.CodeBlock(lang, codeContent))
        lastIdx = match.range.last + 1
    }
    if (lastIdx < body.length) {
        val tail = body.substring(lastIdx).trim()
        if (tail.isNotBlank()) {
            appendProseWithAutoCodeDetection(tail, segments)
        }
    }
    return segments
}

/**
 * Renders an entire Coding Agent response with structured Tool Trace cards,
 * formatted Markdown headings/bullets, inline `code` badges, and IDE syntax-highlighted code blocks.
 */
@Composable
fun AntigravityMarkdownView(markdown: String) {
    val segments = remember(markdown) { parseMarkdownSegments(markdown) }

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        segments.forEach { seg ->
            when (seg) {
                is MarkdownSegment.ToolTraceBlock -> {
                    var showSteps by remember { mutableStateOf(true) }
                    Surface(
                        color = Color(0xFF0D1526),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, Color(0xFF1E3A5F), RoundedCornerShape(8.dp))
                            .clickable { showSteps = !showSteps }
                    ) {
                        Column(modifier = Modifier.padding(8.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = seg.header,
                                    color = Color(0xFF38BDF8),
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = if (showSteps) "▼" else "▶",
                                    color = Color(0xFF64748B),
                                    fontSize = 10.sp
                                )
                            }
                            if (showSteps && seg.steps.isNotEmpty()) {
                                Spacer(modifier = Modifier.height(4.dp))
                                seg.steps.forEach { step ->
                                    Text(
                                        text = "• $step",
                                        color = Color(0xFF94A3B8),
                                        fontSize = 10.5.sp,
                                        fontFamily = FontFamily.Monospace,
                                        modifier = Modifier.padding(vertical = 1.dp)
                                    )
                                }
                            }
                        }
                    }
                }

                is MarkdownSegment.CodeBlock -> {
                    IdeCodeBlockCard(
                        code = seg.code,
                        language = seg.language
                    )
                }

                is MarkdownSegment.ProseBlock -> {
                    SelectionContainer {
                        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            seg.lines.forEach { rawLine ->
                                val line = rawLine.trimEnd()
                                when {
                                    line.isBlank() -> Spacer(modifier = Modifier.height(2.dp))
                                    line.startsWith("### ") || line.startsWith("## ") || line.startsWith("# ") -> {
                                        val cleanHeading = line.trimStart('#', ' ')
                                        Text(
                                            text = formatInlineMarkdown(cleanHeading),
                                            color = Color(0xFF38BDF8),
                                            fontSize = 13.5.sp,
                                            fontWeight = FontWeight.Bold,
                                            modifier = Modifier.padding(top = 4.dp, bottom = 2.dp)
                                        )
                                    }
                                    line.trimStart().startsWith("- ") || line.trimStart().startsWith("• ") || line.trimStart().startsWith("* ") -> {
                                        val bulletText = line.trimStart().drop(2)
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            verticalAlignment = Alignment.Top
                                        ) {
                                            Text(
                                                text = "▸ ",
                                                color = Color(0xFF34D399),
                                                fontSize = 12.sp,
                                                fontWeight = FontWeight.Bold
                                            )
                                            Text(
                                                text = formatInlineMarkdown(bulletText),
                                                color = Color(0xFFF1F5F9),
                                                fontSize = 12.5.sp,
                                                lineHeight = 19.sp
                                            )
                                        }
                                    }
                                    else -> {
                                        Text(
                                            text = formatInlineMarkdown(line),
                                            color = Color(0xFFF1F5F9),
                                            fontSize = 12.5.sp,
                                            lineHeight = 19.sp
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
}
