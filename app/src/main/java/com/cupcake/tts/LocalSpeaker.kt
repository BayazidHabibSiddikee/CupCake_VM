package com.cupcake.tts

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.util.concurrent.ConcurrentHashMap
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Plays the companion's voice on the phone speaker.
 *
 * TWO separate paths — never cross-wired:
 *
 *  1. [directSpeak] — phone speaker only. Calls [TtsManager.directSpeak] which is
 *     a plain tts.speak(QUEUE_ADD) call. Google TTS handles everything: language,
 *     audio focus, audio session, queueing. No WAV parsing, no AudioTrack, no race.
 *     This is what actually works on every Android device.
 *
 *  2. [streamForEsp] — ESP32 PCM streaming only. Calls [TtsManager.speakStreaming]
 *     which synthesizes to a file and reads the WAV chunks back. The AudioTrack path
 *     here is only used to mirror those same chunks to the phone speaker when the
 *     caller explicitly asks ([playLocally] = true).
 *
 * [isSpeaking] is set to true the moment [directSpeak] fires an utteranceId and
 * cleared when TtsManager calls onDone/onError for that utteranceId.
 */
@Singleton
class LocalSpeaker @Inject constructor(
    private val context: Context,
    private val ttsManager: TtsManager
) {

    private val scope = CoroutineScope(Dispatchers.IO + Job())

    /** Utterance IDs we started that have not yet received onDone/onError. */
    private val pendingUtterances = ConcurrentHashMap<String, Boolean>()

    /** True when at least one utterance is in-flight (started but not done). */
    @Volatile
    var isSpeaking: Boolean = false
        private set(value) {
            field = value
            globalIsSpeaking = value
        }

    // Register a TtsCallback so we can track speaking state per utteranceId.
    init {
        ttsManager.initialize(object : TtsManager.TtsCallback {
            override fun onStart(utteranceId: String) {
                if (pendingUtterances.containsKey(utteranceId)) {
                    isSpeaking = true
                    Log.d(TAG, "onStart: $utteranceId — isSpeaking=true")
                }
            }
            override fun onDone(utteranceId: String) {
                pendingUtterances.remove(utteranceId)
                if (pendingUtterances.isEmpty()) {
                    isSpeaking = false
                    Log.d(TAG, "onDone: $utteranceId — isSpeaking=false")
                }
            }
            override fun onError(utteranceId: String, errorCode: Int) {
                pendingUtterances.remove(utteranceId)
                if (pendingUtterances.isEmpty()) {
                    isSpeaking = false
                    Log.w(TAG, "onError: $utteranceId code=$errorCode — isSpeaking=false")
                }
            }
            override fun onAudioChunk(utteranceId: String, audioData: ByteArray, sampleRate: Int) {}
        })
    }

    /**
     * Speak [rawText] on the phone speaker using Google TTS directly.
     * This is the reliable, race-free path for local playback.
     */
    fun directSpeak(rawText: String, normalize: (String) -> String = { it }) {
        if (!VoiceSettings.isEnabled(context)) {
            Log.i(TAG, "voice disabled in settings — skipping")
            return
        }

        // Strip emojis and non-speech characters.
        val cleanedText = rawText
            .replace(Regex("[^a-zA-Z0-9\\s,.?!'\"-—\\u0980-\\u09FF]"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
        val text = normalize(cleanedText)
        if (text.isBlank()) return

        // Stop any in-flight utterances first so she doesn't speak over herself.
        stop()

        Log.i(TAG, "directSpeak: ${text.take(50)}")
        val uid = ttsManager.directSpeak(text)
        pendingUtterances[uid] = true
        isSpeaking = true   // pre-set; TtsCallback.onStart will re-confirm
    }

    /**
     * Legacy entry point — delegates to [directSpeak]. Keep signature identical
     * so callers that already call speak() don't need changes.
     */
    fun speak(rawText: String, normalize: (String) -> String = { it }) = directSpeak(rawText, normalize)

    /**
     * Synthesizes [rawText] and streams raw PCM chunks to [onChunk] (for the ESP32).
     * Also plays locally via AudioTrack when [playLocally] = true.
     *
     * This should NOT be used for phone-speaker playback — use [directSpeak] instead.
     */
    fun streamForEsp(
        rawText: String,
        playLocally: Boolean = false,
        onChunk: (ByteArray) -> Unit
    ) {
        if (rawText.isBlank()) return

        val cleanedText = rawText
            .replace(Regex("[^a-zA-Z0-9\\s,.?!'\"-—\\u0980-\\u09FF]"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
        if (cleanedText.isBlank()) return

        scope.launch {
            val player = if (playLocally) Player() else null
            try {
                val stream = ttsManager.speakStreaming(cleanedText) { chunk ->
                    onChunk(chunk)
                    if (player != null) feed(player, chunk)
                }
                for (_unit in stream) { /* wait */ }
            } catch (e: Exception) {
                Log.w(TAG, "streamForEsp failed: ${e.message}")
            } finally {
                player?.track?.let { t ->
                    runCatching { t.stop() }
                    runCatching { t.release() }
                }
            }
        }
    }

    fun stop() {
        ttsManager.stop()
        pendingUtterances.clear()
        isSpeaking = false
    }

    // ── AudioTrack helpers (used only by streamForEsp) ──────────────────────

    private class Player(
        @Volatile var track: AudioTrack? = null,
        @Volatile var header: ByteArrayOutputStream? = null,
        @Volatile var sampleRate: Int = 22050,
        @Volatile var channels: Int = 1,
        @Volatile var bitsPerSample: Int = 16,
        @Volatile var dataStart: Int = -1
    )

    private fun feed(player: Player, chunk: ByteArray) {
        if (player.dataStart < 0) {
            val buf = player.header ?: ByteArrayOutputStream(chunk.size + 1024).also { player.header = it }
            buf.write(chunk)
            val bytes = buf.toByteArray()
            if (!parseWavHeader(player, bytes)) return
            val start = player.dataStart
            if (start > bytes.size) return
            startTrack(player)
            writePcm(player, bytes, start, bytes.size - start)
            buf.reset()
        } else {
            writePcm(player, chunk, 0, chunk.size)
        }
    }

    private fun parseWavHeader(player: Player, bytes: ByteArray): Boolean {
        if (bytes.size < 12) return false
        var i = 12
        while (i + 8 <= bytes.size) {
            val id = String(bytes, i, 4, Charsets.US_ASCII)
            val size = readInt(bytes, i + 4)
            when (id) {
                "fmt " -> {
                    if (i + 8 + 16 > bytes.size) return false
                    player.channels = readShort(bytes, i + 8 + 2)
                    player.sampleRate = readInt(bytes, i + 8 + 4)
                    player.bitsPerSample = readShort(bytes, i + 8 + 14)
                }
                "data" -> {
                    player.dataStart = i + 8
                    return true
                }
            }
            if (size <= 0) return false
            i += 8 + size + (size and 1)
        }
        return false
    }

    private fun startTrack(player: Player) {
        val chMask = if (player.channels == 2) AudioFormat.CHANNEL_OUT_STEREO else AudioFormat.CHANNEL_OUT_MONO
        val encoding = if (player.bitsPerSample == 8) AudioFormat.ENCODING_PCM_8BIT else AudioFormat.ENCODING_PCM_16BIT
        val minBuf = AudioTrack.getMinBufferSize(player.sampleRate, chMask, encoding).coerceAtLeast(4096)
        val track = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setSampleRate(player.sampleRate)
                    .setChannelMask(chMask)
                    .setEncoding(encoding)
                    .build()
            )
            .setTransferMode(AudioTrack.MODE_STREAM)
            .setBufferSizeInBytes(minBuf)
            .build()
        player.track = track
        track.play()
    }

    private fun writePcm(player: Player, bytes: ByteArray, off: Int, len: Int) {
        if (len <= 0) return
        val track = player.track ?: return
        var written = 0
        while (written < len) {
            written += track.write(bytes.copyOfRange(off + written, off + len), 0, len - written)
            if (written <= 0) break
        }
    }

    private fun readInt(b: ByteArray, o: Int): Int =
        (b[o].toInt() and 0xFF) or ((b[o + 1].toInt() and 0xFF) shl 8) or
            ((b[o + 2].toInt() and 0xFF) shl 16) or ((b[o + 3].toInt() and 0xFF) shl 24)

    private fun readShort(b: ByteArray, o: Int): Int =
        (b[o].toInt() and 0xFF) or ((b[o + 1].toInt() and 0xFF) shl 8)

    companion object {
        private const val TAG = "LocalSpeaker"

        /**
         * Global speaking flag — updated by the singleton instance.
         * Read by [ShimejiPetService] (which is not Hilt-injected) so the sprite
         * mouth animation syncs with phone TTS without any DI plumbing in the service.
         */
        @Volatile
        var globalIsSpeaking: Boolean = false
            internal set
    }
}
