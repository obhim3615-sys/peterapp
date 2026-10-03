package com.example.peterapp

import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.compose.runtime.mutableStateListOf
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class DiagnosticLogEntry(
    val id: Long,
    val timestamp: String,
    val tag: String,
    val level: String, // "INFO", "NET", "TOOL", "OK", "WARN", "ERROR"
    val message: String
)

/**
 * Global Diagnostic Logger (`PeterLogger.kt`):
 * 1. Writes every event to Android Studio Logcat under tag `PeterGemini` so you can filter by
 *    `PeterGemini` in Android Studio's Logcat window.
 * 2. Streams every log line live into the in-app `📡 Logs` console AND the live status box inside the Chat tab!
 */
object PeterLogger {
    private const val LOGCAT_TAG = "PeterGemini"
    private val mainHandler = Handler(Looper.getMainLooper())
    private val timeFmt = SimpleDateFormat("HH:mm:ss.SSS", Locale.US)
    private var nextId = 1L

    val logs = mutableStateListOf<DiagnosticLogEntry>()

    fun info(tag: String, msg: String) = append(tag, "INFO", msg)
    fun net(tag: String, msg: String) = append(tag, "NET", msg)
    fun tool(tag: String, msg: String) = append(tag, "TOOL", msg)
    fun ok(tag: String, msg: String) = append(tag, "OK", msg)
    fun warn(tag: String, msg: String) = append(tag, "WARN", msg)
    fun error(tag: String, msg: String) = append(tag, "ERROR", msg)

    private fun append(tag: String, level: String, msg: String) {
        val ts = synchronized(timeFmt) { timeFmt.format(Date()) }
        val formatted = "[$ts][$level][$tag] $msg"
        when (level) {
            "ERROR" -> Log.e(LOGCAT_TAG, formatted)
            "WARN" -> Log.w(LOGCAT_TAG, formatted)
            else -> Log.d(LOGCAT_TAG, formatted)
        }
        mainHandler.post {
            val entry = DiagnosticLogEntry(
                id = nextId++,
                timestamp = ts,
                tag = tag,
                level = level,
                message = msg
            )
            logs.add(0, entry) // newest first
            if (logs.size > 250) {
                logs.removeRange(250, logs.size)
            }
        }
    }

    fun clear() {
        mainHandler.post {
            logs.clear()
        }
    }
}
