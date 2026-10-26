package dev.harrypulvirenti.fire2mqtt.system

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.database.ContentObserver
import android.media.AudioManager
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import androidx.core.content.ContextCompat
import dev.harrypulvirenti.fire2mqtt.mqtt.VolumePayload
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.launch
import org.koin.core.annotation.Factory

// Hidden AudioManager broadcasts, sent by the system on every stream volume / mute change.
private const val VOLUME_CHANGED_ACTION = "android.media.VOLUME_CHANGED_ACTION"
private const val STREAM_MUTE_CHANGED_ACTION = "android.media.STREAM_MUTE_CHANGED_ACTION"

/**
 * Publishes the STREAM_MUSIC volume whenever it may have changed. Three triggers, because no
 * single one fires on every device: Settings.System changes (Fire OS persists volume there),
 * the system volume broadcasts, and [VolumeChangeSignal] pings after our own volume commands.
 */
@Factory
class VolumeWatcher(
    private val context: Context,
    private val changeSignal: VolumeChangeSignal,
) {

    private val audio = context.getSystemService(AudioManager::class.java)

    fun volumeFlow(): Flow<VolumePayload> = callbackFlow {
        fun snapshot() = VolumePayload(
            level = audio.getStreamVolume(AudioManager.STREAM_MUSIC),
            max = audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC),
            mute = audio.isStreamMute(AudioManager.STREAM_MUSIC),
        )

        trySend(snapshot())

        val observer = object : ContentObserver(Handler(Looper.getMainLooper())) {
            override fun onChange(selfChange: Boolean, uri: Uri?) {
                trySend(snapshot())
            }
        }
        context.contentResolver.registerContentObserver(
            Settings.System.CONTENT_URI,
            true,
            observer,
        )

        val receiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                trySend(snapshot())
            }
        }
        ContextCompat.registerReceiver(
            context,
            receiver,
            IntentFilter().apply {
                addAction(VOLUME_CHANGED_ACTION)
                addAction(STREAM_MUTE_CHANGED_ACTION)
            },
            ContextCompat.RECEIVER_NOT_EXPORTED,
        )

        launch { changeSignal.events.collect { trySend(snapshot()) } }

        awaitClose {
            context.contentResolver.unregisterContentObserver(observer)
            context.unregisterReceiver(receiver)
        }
    }
}
