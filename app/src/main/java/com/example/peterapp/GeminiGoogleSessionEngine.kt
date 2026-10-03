package com.example.peterapp

import android.annotation.SuppressLint
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.webkit.CookieManager
import android.webkit.WebView
import android.webkit.WebViewClient
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
import kotlin.coroutines.resume

/**
 * Stateful Phone-Native Gemini Coding Agent Session Engine (`GeminiGoogleSessionEngine.kt`).
 *
 * Key Fixes for True Antigravity Coding Agent Behavior & Structured Code Output:
 * 1. Primes the coding session ONCE (`isSessionPrimed = true`) with `oneTimeInitPrompt`,
 *    and sends lightweight per-turn messages on subsequent turns.
 * 2. Preserves full Markdown & Code structure from Gemini's HTML DOM via `domNodeToMarkdown(lastNode)`:
 *    converts `<pre><code>` / `<code-block>` into fenced ```python ... ``` blocks with 100% intact
 *    indentation, converts `<h1>..<h4>` into `###` headers, `<li>` into `- ` bullets, `<strong>` into
 *    `**bold**`, and inline `<code>` into `` `code` `` pills (while stripping "Copy code" / "Use code with caution" UI chrome).
 */
@SuppressLint("SetJavaScriptEnabled")
class GeminiGoogleSessionEngine(private val context: Context) {

    private val mainHandler = Handler(Looper.getMainLooper())
    private var backgroundWebView: WebView? = null
    var isPageLoaded = false
        private set

    var isSessionPrimed = false
        private set

    fun hasGoogleSessionCookies(): Boolean {
        val cookies = CookieManager.getInstance().getCookie("https://gemini.google.com")
            ?: CookieManager.getInstance().getCookie("https://accounts.google.com")
            ?: ""
        return cookies.contains("SID") || cookies.contains("__Secure")
    }

    fun resetSession() {
        isSessionPrimed = false
        PeterLogger.info("GeminiWebView", "Resetting stateful coding agent session (isSessionPrimed=false)")
        mainHandler.post {
            backgroundWebView?.loadUrl("https://gemini.google.com/app")
        }
    }

    fun ensureInitialized() {
        mainHandler.post {
            if (backgroundWebView == null) {
                PeterLogger.info("GeminiWebView", "Initializing background Gemini WebView (https://gemini.google.com/app)...")
                val wv = WebView(context).apply {
                    CookieManager.getInstance().setAcceptCookie(true)
                    CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)
                    settings.javaScriptEnabled = true
                    settings.domStorageEnabled = true
                    settings.userAgentString =
                        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
                    webViewClient = object : WebViewClient() {
                        override fun onPageFinished(view: WebView?, url: String?) {
                            super.onPageFinished(view, url)
                            PeterLogger.net("GeminiWebView", "onPageFinished: url=$url | cookies=${hasGoogleSessionCookies()}")
                            if (url != null && url.contains("gemini.google.com")) {
                                isPageLoaded = true
                            }
                        }
                    }
                    loadUrl("https://gemini.google.com/app")
                }
                backgroundWebView = wv
            }
        }
    }

    suspend fun sendCodingAgentTurn(
        lightweightTurnPrompt: String,
        oneTimeSessionInitPrompt: String,
        onStreamingUpdate: ((String) -> Unit)? = null
    ): String? {
        val payloadToSend = if (!isSessionPrimed) {
            PeterLogger.info("GeminiWebView", "First turn in session -> priming session ONCE with Coding Agent instructions.")
            "$oneTimeSessionInitPrompt\n\n=== USER MESSAGE ===\n$lightweightTurnPrompt"
        } else {
            PeterLogger.info("GeminiWebView", "Session already primed -> sending lightweight turn (${lightweightTurnPrompt.length} chars)")
            lightweightTurnPrompt
        }

        val reply = sendRawPromptToGemini(payloadToSend, onStreamingUpdate)
        if (!reply.isNullOrBlank()) {
            isSessionPrimed = true
        }
        return reply
    }

    suspend fun sendRawPromptToGemini(
        prompt: String,
        onStreamingUpdate: ((String) -> Unit)? = null
    ): String? {
        ensureInitialized()
        val escapedPrompt = JSONObject.quote(prompt)

        return withTimeoutOrNull(45_000L) {
            suspendCancellableCoroutine { cont ->
                mainHandler.post {
                    val wv = backgroundWebView
                    if (wv == null) {
                        PeterLogger.error("GeminiWebView", "backgroundWebView is null!")
                        if (cont.isActive) cont.resume(null)
                        return@post
                    }

                    val injectJs = """
                        (function() {
                            const promptText = $escapedPrompt;
                            const countBefore = document.querySelectorAll('message-content, .model-response-text, [data-message-author-role="model"]').length;
                            window.__peterPrevCount = countBefore;
                            window.__peterLastText = "";
                            window.__peterStableTicks = 0;

                            const editor = document.querySelector('.ql-editor, [contenteditable="true"], textarea, rich-textarea div[contenteditable="true"]');
                            if (!editor) {
                                return "NO_EDITOR (url=" + window.location.href + ")";
                            }
                            editor.focus();
                            if (editor.tagName === 'TEXTAREA') {
                                editor.value = promptText;
                                editor.dispatchEvent(new Event('input', { bubbles: true }));
                            } else {
                                editor.innerText = promptText;
                                editor.dispatchEvent(new InputEvent('input', { bubbles: true, data: promptText }));
                            }

                            setTimeout(() => {
                                const sendBtn = document.querySelector('button.send-button, button[aria-label*="Send"], button[aria-label*="send"]');
                                if (sendBtn) {
                                    sendBtn.click();
                                } else {
                                    editor.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                                }
                            }, 250);
                            return "SENT (prevNodes=" + countBefore + ")";
                        })();
                    """.trimIndent()

                    wv.evaluateJavascript(injectJs) { status ->
                        PeterLogger.net("GeminiWebView", "JS Injection result: $status")
                        if (status == null || status.contains("NO_EDITOR")) {
                            PeterLogger.warn("GeminiWebView", "Gemini editor DOM not ready ($status). Reloading gemini.google.com/app...")
                            isSessionPrimed = false
                            wv.loadUrl("https://gemini.google.com/app")
                            if (cont.isActive) cont.resume(null)
                            return@evaluateJavascript
                        }

                        var attempts = 0
                        val pollRunnable = object : Runnable {
                            override fun run() {
                                if (!cont.isActive) return
                                attempts++
                                val checkJs = """
                                    (function() {
                                        function domToMarkdown(node) {
                                            if (!node) return "";
                                            if (node.nodeType === 3) {
                                                return node.nodeValue || "";
                                            }
                                            if (node.nodeType !== 1) return "";
                                            const tag = (node.tagName || "").toLowerCase();
                                            const cls = (node.className && typeof node.className === "string") ? node.className.toLowerCase() : "";

                                            // Skip Gemini UI chrome buttons/headers inside code blocks
                                            if (tag === "button" || cls.includes("code-block-decoration") || cls.includes(" header") || cls.includes("footer") || cls.includes("disclaimer")) {
                                                return "";
                                            }

                                            // Multi-line Code Block (<pre> or <code-block>)
                                            if (tag === "pre" || tag === "code-block") {
                                                const codeEl = node.querySelector("code, pre") || node;
                                                const rawCode = (codeEl.textContent || "").replace(/\r\n/g, "\n").trimEnd();
                                                if (!rawCode) return "";
                                                let lang = "python";
                                                const langSpan = node.querySelector(".code-block-decoration span, [class*='language-']");
                                                if (langSpan && langSpan.textContent) {
                                                    lang = langSpan.textContent.trim().toLowerCase();
                                                }
                                                return "\n```" + lang + "\n" + rawCode + "\n```\n\n";
                                            }

                                            // Inline <code>
                                            if (tag === "code") {
                                                const txt = (node.textContent || "").trim();
                                                if (txt.includes("\n")) {
                                                    return "\n```python\n" + txt + "\n```\n\n";
                                                }
                                                return "`" + txt + "`";
                                            }

                                            let childrenMd = "";
                                            for (let i = 0; i < node.childNodes.length; i++) {
                                                childrenMd += domToMarkdown(node.childNodes[i]);
                                            }

                                            if (tag === "h1" || tag === "h2" || tag === "h3" || tag === "h4") {
                                                return "\n### " + childrenMd.trim() + "\n";
                                            }
                                            if (tag === "strong" || tag === "b") {
                                                return "**" + childrenMd.trim() + "**";
                                            }
                                            if (tag === "li") {
                                                return "\n- " + childrenMd.trim();
                                            }
                                            if (tag === "p" || tag === "div" || tag === "ul" || tag === "ol") {
                                                return childrenMd + "\n";
                                            }
                                            if (tag === "br") {
                                                return "\n";
                                            }
                                            return childrenMd;
                                        }

                                        const nodes = document.querySelectorAll('message-content, .model-response-text, [data-message-author-role="model"]');
                                        if (!nodes || nodes.length <= (window.__peterPrevCount || 0)) {
                                            return JSON.stringify({ state: "WAITING", text: "", count: nodes ? nodes.length : 0 });
                                        }
                                        const lastNode = nodes[nodes.length - 1];
                                        const txt = domToMarkdown(lastNode)
                                            .replace(/Use code with caution\.?/gi, "")
                                            .replace(/Copy code/gi, "")
                                            .replace(/\n{3,}/g, "\n\n")
                                            .trim();
                                        if (!txt) {
                                            return JSON.stringify({ state: "WAITING", text: "", count: nodes.length });
                                        }
                                        if (txt === window.__peterLastText && txt.length > 20) {
                                            window.__peterStableTicks = (window.__peterStableTicks || 0) + 1;
                                        } else {
                                            window.__peterLastText = txt;
                                            window.__peterStableTicks = 0;
                                        }
                                        const isGenerating = !!document.querySelector('button[aria-label*="Stop"], .loading-indicator');
                                        const done = (!isGenerating && window.__peterStableTicks >= 3) || window.__peterStableTicks >= 5;
                                        return JSON.stringify({ state: done ? "DONE" : "STREAMING", text: txt, count: nodes.length });
                                    })();
                                """.trimIndent()

                                wv.evaluateJavascript(checkJs) { rawRes ->
                                    try {
                                        val unquoted = if (rawRes != null && rawRes.startsWith("\"") && rawRes.endsWith("\"")) {
                                            JSONObject("{\"v\":$rawRes}").getString("v")
                                        } else {
                                            rawRes ?: "{}"
                                        }
                                        val obj = JSONObject(unquoted)
                                        val state = obj.optString("state", "WAITING")
                                        val txt = obj.optString("text", "")

                                        if (attempts % 4 == 0 || state == "DONE") {
                                            PeterLogger.net("GeminiWebView", "Poll #$attempts: state=$state | chars=${txt.length}")
                                        }

                                        if (txt.isNotBlank()) {
                                            onStreamingUpdate?.invoke(txt)
                                        }

                                        if (state == "DONE" && txt.isNotBlank()) {
                                            PeterLogger.ok("GeminiWebView", "Gemini structured markdown turn completed (${txt.length} chars)!")
                                            if (cont.isActive) cont.resume(txt)
                                            return@evaluateJavascript
                                        }
                                    } catch (e: Exception) {
                                        PeterLogger.warn("GeminiWebView", "Poll parse warning: ${e.message}")
                                    }

                                    if (attempts < 65) {
                                        mainHandler.postDelayed(this, 600L)
                                    } else {
                                        PeterLogger.error("GeminiWebView", "Timed out after 65 polls waiting for Gemini response.")
                                        if (cont.isActive) cont.resume(null)
                                    }
                                }
                            }
                        }
                        mainHandler.postDelayed(pollRunnable, 1200L)
                    }
                }
            }
        }
    }
}
