package dev.harrypulvirenti.fire2mqtt.commands

import android.view.KeyEvent
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.mqtt.TopicSchema
import dev.harrypulvirenti.fire2mqtt.mqtt.VolumeCommandPayload
import kotlinx.serialization.json.Json
import org.koin.core.annotation.Factory
import org.koin.core.annotation.InjectedParam

private val logger = Logger.withTag("Fire2MQTT/CommandRouter")

@Factory
class CommandRouter(
    @InjectedParam private val prefix: String,
    @InjectedParam private val deviceId: String,
    private val appLauncher: AppLauncher,
    private val volumeController: VolumeController,
) {

    private val keyMap = mapOf(
        "HOME" to KeyEvent.KEYCODE_HOME,
        "BACK" to KeyEvent.KEYCODE_BACK,
        "MENU" to KeyEvent.KEYCODE_MENU,
        "DPAD_UP" to KeyEvent.KEYCODE_DPAD_UP,
        "DPAD_DOWN" to KeyEvent.KEYCODE_DPAD_DOWN,
        "DPAD_LEFT" to KeyEvent.KEYCODE_DPAD_LEFT,
        "DPAD_RIGHT" to KeyEvent.KEYCODE_DPAD_RIGHT,
        "DPAD_CENTER" to KeyEvent.KEYCODE_DPAD_CENTER,
        "MEDIA_PLAY_PAUSE" to KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,
        "MEDIA_PLAY" to KeyEvent.KEYCODE_MEDIA_PLAY,
        "MEDIA_PAUSE" to KeyEvent.KEYCODE_MEDIA_PAUSE,
        "MEDIA_STOP" to KeyEvent.KEYCODE_MEDIA_STOP,
        "MEDIA_REWIND" to KeyEvent.KEYCODE_MEDIA_REWIND,
        "MEDIA_FAST_FORWARD" to KeyEvent.KEYCODE_MEDIA_FAST_FORWARD,
        "MEDIA_NEXT" to KeyEvent.KEYCODE_MEDIA_NEXT,
        "MEDIA_PREVIOUS" to KeyEvent.KEYCODE_MEDIA_PREVIOUS,
        "VOLUME_UP" to KeyEvent.KEYCODE_VOLUME_UP,
        "VOLUME_DOWN" to KeyEvent.KEYCODE_VOLUME_DOWN,
        "MUTE" to KeyEvent.KEYCODE_MUTE,
    )

    fun route(topic: String, payload: String) {
        when (topic) {
            TopicSchema.cmdLaunch(prefix, deviceId) -> {
                appLauncher.launch(payload.trim())
            }
            TopicSchema.cmdKey(prefix, deviceId) -> {
                val keyCode = keyMap[payload.trim().uppercase()]
                if (keyCode != null) {
                    Fire2MqttAccessibilityService.sendKey(keyCode)
                } else {
                    logger.w { "Unknown key: $payload" }
                }
            }
            TopicSchema.cmdVolume(prefix, deviceId) -> {
                runCatching {
                    val cmd = Json.decodeFromString<VolumeCommandPayload>(payload)
                    when (cmd.action) {
                        "set" -> cmd.level?.let { volumeController.set(it) }
                        "up" -> volumeController.stepUp()
                        "down" -> volumeController.stepDown()
                        "mute" -> volumeController.mute()
                        "unmute" -> volumeController.unmute()
                    }
                }.onFailure { logger.e(it) { "Volume command parse error: ${it.message}" } }
            }
            TopicSchema.cmdPower(prefix, deviceId) -> {
                when (payload.trim().lowercase()) {
                    "sleep" -> Fire2MqttAccessibilityService.sendKey(KeyEvent.KEYCODE_SLEEP)
                    "wake" -> Fire2MqttAccessibilityService.sendKey(KeyEvent.KEYCODE_WAKEUP)
                }
            }
            TopicSchema.cmdMedia(prefix, deviceId) -> {
                val keyCode = when (payload.trim().lowercase()) {
                    "play" -> KeyEvent.KEYCODE_MEDIA_PLAY
                    "pause" -> KeyEvent.KEYCODE_MEDIA_PAUSE
                    "play_pause" -> KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE
                    "next" -> KeyEvent.KEYCODE_MEDIA_NEXT
                    "prev" -> KeyEvent.KEYCODE_MEDIA_PREVIOUS
                    "stop" -> KeyEvent.KEYCODE_MEDIA_STOP
                    else -> null
                }
                keyCode?.let { Fire2MqttAccessibilityService.sendKey(it) }
                    ?: logger.w { "Unknown media command: $payload" }
            }
        }
    }
}
