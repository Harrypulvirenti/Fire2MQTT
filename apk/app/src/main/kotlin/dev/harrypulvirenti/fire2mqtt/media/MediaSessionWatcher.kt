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

        fun attachCallbacks(controllers: List<MediaController>) {
            controllers.forEach { controller ->
                if (controller in callbacks) return@forEach
                val cb = object : MediaController.Callback() {
                    override fun onPlaybackStateChanged(state: PlaybackState?) {
                        trySend(buildPayload(controller, state))
                    }
                    override fun onMetadataChanged(metadata: MediaMetadata?) {
                        val state = controller.playbackState
                        trySend(buildPayload(controller, state, metadata))
                    }
                }
                controller.registerCallback(cb)
                callbacks[controller] = cb
                // Emit current state on attach
                trySend(buildPayload(controller, controller.playbackState, controller.metadata))
            }
        }

        fun detachAll() {
            callbacks.forEach { (ctrl, cb) -> ctrl.unregisterCallback(cb) }
            callbacks.clear()
        }

        val sessionListener = MediaSessionManager.OnActiveSessionsChangedListener { controllers ->
            detachAll()
            if (controllers != null) attachCallbacks(controllers)
        }

        try {
            manager.addOnActiveSessionsChangedListener(sessionListener, notificationListenerComponent)
            attachCallbacks(manager.getActiveSessions(notificationListenerComponent))
        } catch (e: SecurityException) {
            logger.e(e) { "Missing NotificationListener permission: ${e.message}" }
        }

        awaitClose {
            detachAll()
            manager.removeOnActiveSessionsChangedListener(sessionListener)
        }
    }.flowOn(Dispatchers.Main)

    private fun buildPayload(
        controller: MediaController,
        state: PlaybackState?,
        metadata: MediaMetadata? = controller.metadata,
    ): PlaybackPayload {
        val schemaState = PlaybackStateMapper.toSchemaInt(
            state?.state ?: PlaybackState.STATE_NONE
        )
        return PlaybackPayload(
            mediaSessionState = schemaState,
            app = controller.packageName,
            title = metadata?.getString(MediaMetadata.METADATA_KEY_TITLE),
            artist = metadata?.getString(MediaMetadata.METADATA_KEY_ARTIST)
                ?: metadata?.getString(MediaMetadata.METADATA_KEY_ALBUM_ARTIST),
            album = metadata?.getString(MediaMetadata.METADATA_KEY_ALBUM),
            durationMs = metadata?.getLong(MediaMetadata.METADATA_KEY_DURATION)
                ?.takeIf { it > 0 },
            positionMs = state?.position?.takeIf { it >= 0 },
        )
    }
}
