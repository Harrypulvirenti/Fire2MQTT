package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.media.AudioManager

class VolumeController(context: Context) {
    private val audio = context.getSystemService(AudioManager::class.java)

    fun set(level: Int) {
        val clamped = level.coerceIn(0, audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC))
        audio.setStreamVolume(AudioManager.STREAM_MUSIC, clamped, 0)
    }

    fun stepUp() = audio.adjustStreamVolume(
        AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, 0
    )

    fun stepDown() = audio.adjustStreamVolume(
        AudioManager.STREAM_MUSIC, AudioManager.ADJUST_LOWER, 0
    )

    fun mute() = audio.adjustStreamVolume(
        AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0
    )

    fun unmute() = audio.adjustStreamVolume(
        AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0
    )
}
