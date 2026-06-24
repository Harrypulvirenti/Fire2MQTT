package dev.harrypulvirenti.fire2mqtt.media

import android.content.ComponentName
import android.content.Context
import android.media.MediaMetadata
import android.media.session.MediaController
import android.media.session.MediaSessionManager
import android.media.session.PlaybackState
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.mqtt.PlaybackPayload
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn

private val logger = Logger.withTag("Fire2MQTT/MediaSession")

class MediaSessionWatcher(
    private val context: Context,
    private val notificationListenerComponent: ComponentName,
) {
    private val manager = context.getSystemService(MediaSessionManager::class.java)

    fun playbackEvents(): Flow<PlaybackPayload> = callbackFlow {
        val callbacks = mutableMapOf<MediaController, MediaController.Callback>()
        var controllers: List<MediaController> = emptyList()

        // Fire TV usually has several active sessions at once (the streaming app plus
        // Alexa/Vizzini media players). They all share one state/playback topic, so we must
        // publish only the *primary* one — otherwise a background session at STATE_NONE
        // clobbers the app you're actually watching (e.g. Crunchyroll playing → reported idle).
        fun emitPrimary() {
            trySend(buildPayload(selectPrimary(controllers)))
        }

        fun detachAll() {
            callbacks.forEach { (ctrl, cb) -> ctrl.unregisterCallback(cb) }
            callbacks.clear()
        }

        fun attach(active: List<MediaController>) {
            detachAll()
            controllers = active
            active.forEach { controller ->
                val cb = object : MediaController.Callback() {
                    // Any session changing re-selects the primary, so a background session's
                    // update can no longer overwrite the foreground app's playback.
                    override fun onPlaybackStateChanged(state: PlaybackState?) = emitPrimary()
                    override fun onMetadataChanged(metadata: MediaMetadata?) = emitPrimary()
                }
                controller.registerCallback(cb)
                callbacks[controller] = cb
            }
            emitPrimary()
        }

        val sessionListener = MediaSessionManager.OnActiveSessionsChangedListener { active ->
            attach(active ?: emptyList())
        }

        try {
            manager.addOnActiveSessionsChangedListener(sessionListener, notificationListenerComponent)
            attach(manager.getActiveSessions(notificationListenerComponent))
        } catch (e: SecurityException) {
            logger.e(e) { "Missing NotificationListener permission: ${e.message}" }
        }

        awaitClose {
            detachAll()
            manager.removeOnActiveSessionsChangedListener(sessionListener)
        }
    }.flowOn(Dispatchers.Main)

    private fun buildPayload(controller: MediaController?): PlaybackPayload {
        val state = controller?.playbackState
        val metadata = controller?.metadata
        return PlaybackPayload(
            mediaSessionState = PlaybackStateMapper.toSchemaInt(
                state?.state ?: PlaybackState.STATE_NONE
            ),
            app = controller?.packageName ?: "",
            title = metadata?.getString(MediaMetadata.METADATA_KEY_TITLE),
            artist = metadata?.getString(MediaMetadata.METADATA_KEY_ARTIST)
                ?: metadata?.getString(MediaMetadata.METADATA_KEY_ALBUM_ARTIST),
            album = metadata?.getString(MediaMetadata.METADATA_KEY_ALBUM),
            durationMs = metadata?.getLong(MediaMetadata.METADATA_KEY_DURATION)
                ?.takeIf { it > 0 },
            positionMs = state?.position?.takeIf { it >= 0 },
        )
    }

    companion object {
        /**
         * The session to report when several are active: the most "playing" one. A background
         * player sitting at STATE_NONE/STOPPED must never outrank the app actually playing.
         */
        internal fun selectPrimary(controllers: List<MediaController>): MediaController? =
            controllers.maxByOrNull { statePriority(it.playbackState?.state) }

        internal fun statePriority(state: Int?): Int = when (state) {
            PlaybackState.STATE_PLAYING,
            PlaybackState.STATE_BUFFERING,
            PlaybackState.STATE_FAST_FORWARDING,
            PlaybackState.STATE_REWINDING -> 3
            PlaybackState.STATE_PAUSED -> 2
            PlaybackState.STATE_STOPPED -> 1
            else -> 0
        }
    }
}
