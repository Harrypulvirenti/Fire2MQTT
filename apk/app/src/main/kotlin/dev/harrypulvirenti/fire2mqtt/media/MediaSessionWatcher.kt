package dev.harrypulvirenti.fire2mqtt.media

import android.content.ComponentName
import android.content.Context
import android.media.MediaMetadata
import android.media.session.MediaController
import android.media.session.MediaSessionManager
import android.media.session.PlaybackState
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.mqtt.PlaybackPayload
import dev.harrypulvirenti.fire2mqtt.system.SecureSettingsManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

private val logger = Logger.withTag("Fire2MQTT/MediaSession")

// The binding can change under us — the framework can drop it mid-session (Fire OS resetting it),
// or the HA integration / a reboot can restore it — so a one-time check at flow start isn't enough.
// We re-verify periodically for the life of the pipeline and (re)register whenever it's bound.
private const val NOTIFICATION_LISTENER_RECHECK_INTERVAL_MS = 15 * 60 * 1000L

// On a fresh boot the framework may bind the listener slightly after our service starts (the
// BootReceiver races the system binding enabled listeners), so an immediate first attempt can lose.
// Retry briefly before giving up. This is NOT a rebind — the app cannot bind its own listener on
// Fire OS; it only re-attempts the registration in case the bind lands a moment later.
private const val LISTENER_STARTUP_RETRY_ATTEMPTS = 5
private const val LISTENER_STARTUP_RETRY_MS = 1_500L

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

        // Registers against MediaSessionManager. Returns false (rather than throwing) when the
        // listener isn't bound: being listed in enabled_notification_listeners is NOT enough — an
        // enabled-but-unbound listener (typical right after an in-place reinstall, and possibly
        // after a reboot on Fire OS) still makes getActiveSessions() throw SecurityException.
        fun startListening(): Boolean {
            runCatching { manager.removeOnActiveSessionsChangedListener(sessionListener) }
            return try {
                manager.addOnActiveSessionsChangedListener(sessionListener, notificationListenerComponent)
                attach(manager.getActiveSessions(notificationListenerComponent))
                true
            } catch (e: SecurityException) {
                false
            }
        }

        // Logs why we can't read media sessions, with enough detail to diagnose — in particular to
        // tell an enabled-but-unbound listener (grant present, just not bound) apart from a missing
        // grant, which is the key signal when triaging the reboot case.
        fun logUnbound(situation: String) {
            val enabledInSettings = SecureSettingsManager.isNotificationListenerEnabled(context)
            logger.w {
                "Media session listener not bound $situation " +
                    "(enabled_notification_listeners contains us=$enabledInSettings). Playback " +
                    "state stays unavailable until it is bound. The app cannot bind its own " +
                    "listener on Fire OS — run an ADB (re-)provision from the Home Assistant " +
                    "integration. If enabledInSettings=true right after a reboot, the OS did not " +
                    "auto-rebind the listener on boot (so a reboot alone won't recover it)."
            }
        }

        // The app cannot bind its own NotificationListenerService on Fire OS (that needs the
        // NotificationManagerService grant API over ADB, driven by the HA integration during
        // provisioning). All we do here is register once the listener IS bound, retrying briefly
        // to absorb a boot-time race where the framework binds slightly after our service starts.
        suspend fun ensureListening(): Boolean {
            repeat(LISTENER_STARTUP_RETRY_ATTEMPTS) { attempt ->
                if (startListening()) {
                    logger.i {
                        "Media session listener bound and watching" +
                            if (attempt > 0) " (after ${attempt + 1} attempts)" else ""
                    }
                    return true
                }
                delay(LISTENER_STARTUP_RETRY_MS)
            }
            logUnbound("at startup")
            return false
        }

        var listenerBound = false
        val bindJob = launch { listenerBound = ensureListening() }

        // Re-verify against the live session manager periodically: the binding can be dropped
        // mid-session (no exception on our side — the callback just goes quiet) or be restored
        // later by an ADB re-provision / reboot. Re-register when it comes back, and log only on
        // transitions so a healthy device stays quiet.
        val healJob = launch {
            while (isActive) {
                delay(NOTIFICATION_LISTENER_RECHECK_INTERVAL_MS)
                val nowBound = startListening()
                if (nowBound && !listenerBound) {
                    logger.i { "Media session listener re-bound — resumed watching" }
                } else if (!nowBound && listenerBound) {
                    logUnbound("on periodic recheck (binding dropped)")
                }
                listenerBound = nowBound
            }
        }

        awaitClose {
            bindJob.cancel()
            healJob.cancel()
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
