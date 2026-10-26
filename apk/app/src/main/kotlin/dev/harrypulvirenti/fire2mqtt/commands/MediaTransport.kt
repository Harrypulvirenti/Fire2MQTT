package dev.harrypulvirenti.fire2mqtt.commands

import android.content.ComponentName
import android.content.Context
import android.media.session.MediaController
import android.media.session.MediaSessionManager
import android.view.KeyEvent
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.media.MediaSessionWatcher

private val logger = Logger.withTag("Fire2MQTT/MediaTransport")

/**
 * Delivers media transport commands (play, pause, stop, skip, …) to the session the user is
 * actually looking at, via [MediaController.TransportControls].
 *
 * Dispatching media key events instead lets the framework pick the target — the "media button
 * session" — which isn't necessarily the foreground app. On Google TV the built-in Cast receiver
 * keeps its own session and grabs the media button as soon as the foreground app pauses, so a
 * PLAY key after a PAUSE went to Cast and the paused app never resumed. Picking the session
 * ourselves avoids that; key dispatch remains the fallback when no session can be read.
 */
class MediaTransport(
    context: Context,
    private val notificationListenerComponent: ComponentName,
    private val foregroundPackage: () -> String? = {
        Fire2MqttAccessibilityService.foregroundPackages.replayCache.lastOrNull()
    },
) {
    private val manager = context.getSystemService(MediaSessionManager::class.java)

    /** Sends [keyCode] (a KEYCODE_MEDIA_*) to the target session; false if nothing handled it. */
    fun send(keyCode: Int): Boolean {
        val controllers = try {
            manager.getActiveSessions(notificationListenerComponent)
        } catch (e: SecurityException) {
            // Notification listener not bound: no session access, let key dispatch try.
            logger.w { "Can't read media sessions (${e.message}); falling back to key dispatch" }
            return false
        }
        val target = selectTarget(controllers, foregroundPackage()) ?: run {
            logger.d { "No active media session for key $keyCode; falling back to key dispatch" }
            return false
        }
        val applied = applyTo(target.transportControls, target.playbackState?.state, keyCode)
        if (applied) logger.i { "Media key $keyCode → ${target.packageName}" }
        return applied
    }

    companion object {
        /** The transport keys [applyTo] understands. */
        internal val MEDIA_KEYS = setOf(
            KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,
            KeyEvent.KEYCODE_MEDIA_PLAY,
            KeyEvent.KEYCODE_MEDIA_PAUSE,
            KeyEvent.KEYCODE_MEDIA_STOP,
            KeyEvent.KEYCODE_MEDIA_REWIND,
            KeyEvent.KEYCODE_MEDIA_FAST_FORWARD,
            KeyEvent.KEYCODE_MEDIA_NEXT,
            KeyEvent.KEYCODE_MEDIA_PREVIOUS,
        )

        /**
         * The session a media command should go to: the foreground app's own session when it
         * has one (so a paused app resumes even while a background Cast session idles), else the
         * most "playing" session overall (e.g. music playing behind the launcher). Pure for testing.
         */
        internal fun selectTarget(
            controllers: List<MediaController>,
            foregroundPackage: String?,
        ): MediaController? {
            val foreground = controllers.filter { it.packageName == foregroundPackage }
            return MediaSessionWatcher.selectPrimary(foreground.ifEmpty { controllers })
        }

        /** Maps [keyCode] onto [controls]; false for keys with no transport equivalent. */
        internal fun applyTo(
            controls: MediaController.TransportControls,
            state: Int?,
            keyCode: Int,
        ): Boolean {
            when (keyCode) {
                KeyEvent.KEYCODE_MEDIA_PLAY -> controls.play()
                KeyEvent.KEYCODE_MEDIA_PAUSE -> controls.pause()
                KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE ->
                    if (MediaSessionWatcher.statePriority(state) >= 3) controls.pause() else controls.play()
                KeyEvent.KEYCODE_MEDIA_STOP -> controls.stop()
                KeyEvent.KEYCODE_MEDIA_NEXT -> controls.skipToNext()
                KeyEvent.KEYCODE_MEDIA_PREVIOUS -> controls.skipToPrevious()
                KeyEvent.KEYCODE_MEDIA_FAST_FORWARD -> controls.fastForward()
                KeyEvent.KEYCODE_MEDIA_REWIND -> controls.rewind()
                else -> return false
            }
            return true
        }
    }
}
