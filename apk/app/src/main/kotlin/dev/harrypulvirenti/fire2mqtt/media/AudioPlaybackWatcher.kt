package dev.harrypulvirenti.fire2mqtt.media

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.AudioPlaybackConfiguration
import android.os.Handler
import android.os.Looper
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import org.koin.core.annotation.Factory

/**
 * Reports whether media-type audio is actively playing, independent of any MediaSession.
 *
 * Some streaming apps (notably F1 TV) never publish a MediaSession, so [MediaSessionWatcher]
 * sees nothing while they play. AudioManager's playback-configuration callback fires whenever
 * any app starts or stops an audio track, giving a session-independent "is media playing"
 * signal that state-detection rules can key on via the payload's `audio_state` field.
 *
 * Only [PLAYING]/[IDLE] are distinguishable: a paused AudioTrack drops out of the active
 * configuration list, so a pause is indistinguishable from a stop here.
 */
@Factory
class AudioPlaybackWatcher(private val context: Context) {

    private val audio = context.getSystemService(AudioManager::class.java)

    fun audioStateFlow(): Flow<String> = callbackFlow {
        val callback = object : AudioManager.AudioPlaybackCallback() {
            override fun onPlaybackConfigChanged(configs: MutableList<AudioPlaybackConfiguration>) {
                trySend(stateOf(configs))
            }
        }

        trySend(stateOf(audio.activePlaybackConfigurations))
        audio.registerAudioPlaybackCallback(callback, Handler(Looper.getMainLooper()))
        awaitClose { audio.unregisterAudioPlaybackCallback(callback) }
    }.distinctUntilChanged()

    companion object {
        const val PLAYING = "playing"
        const val IDLE = "idle"

        // System sounds, alarms and notifications also create playback configs; only
        // media/game usages should count as "the app is playing something".
        private val MEDIA_USAGES = setOf(
            AudioAttributes.USAGE_MEDIA,
            AudioAttributes.USAGE_GAME,
        )

        private fun stateOf(configs: List<AudioPlaybackConfiguration>): String =
            if (configs.any { it.audioAttributes.usage in MEDIA_USAGES }) PLAYING else IDLE
    }
}
