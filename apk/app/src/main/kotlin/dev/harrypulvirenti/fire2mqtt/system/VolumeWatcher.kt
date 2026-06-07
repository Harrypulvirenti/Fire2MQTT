package dev.harrypulvirenti.fire2mqtt.system

import android.content.Context
import android.database.ContentObserver
import android.media.AudioManager
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import dev.harrypulvirenti.fire2mqtt.mqtt.VolumePayload
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import org.koin.core.annotation.Factory

@Factory
class VolumeWatcher(private val context: Context) {

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
        awaitClose { context.contentResolver.unregisterContentObserver(observer) }
    }
}
