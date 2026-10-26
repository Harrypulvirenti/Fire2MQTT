package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.media.AudioManager
import dev.harrypulvirenti.fire2mqtt.system.VolumeChangeSignal
import org.koin.core.annotation.Factory

@Factory
class VolumeController(context: Context, private val changeSignal: VolumeChangeSignal) {
    private val audio = context.getSystemService(AudioManager::class.java)

    fun set(level: Int) = changed {
        val clamped = level.coerceIn(0, audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC))
        audio.setStreamVolume(AudioManager.STREAM_MUSIC, clamped, 0)
    }

    fun stepUp() = changed {
        audio.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, 0)
    }

    fun stepDown() = changed {
        audio.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_LOWER, 0)
    }

    fun mute() = changed {
        audio.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0)
    }

    fun unmute() = changed {
        audio.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0)
    }

    // Republish state/volume after every command, whether or not the system notices the change.
    private inline fun changed(action: () -> Unit) {
        action()
        changeSignal.notifyChanged()
    }
}
