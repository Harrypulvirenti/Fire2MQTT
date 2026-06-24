package dev.harrypulvirenti.fire2mqtt.mqtt

/** Single source of truth for MQTT topic patterns. Must stay in sync with docs/mqtt-schema.md */
object TopicSchema {
    const val SCHEMA_VERSION = 2

    fun status(prefix: String, deviceId: String) = "$prefix/$deviceId/status"
    fun stateDevice(prefix: String, deviceId: String) = "$prefix/$deviceId/state/device"
    fun statePlayback(prefix: String, deviceId: String) = "$prefix/$deviceId/state/playback"
    fun stateApp(prefix: String, deviceId: String) = "$prefix/$deviceId/state/app"
    fun stateApps(prefix: String, deviceId: String) = "$prefix/$deviceId/state/apps"
    fun stateScreen(prefix: String, deviceId: String) = "$prefix/$deviceId/state/screen"
    fun stateVolume(prefix: String, deviceId: String) = "$prefix/$deviceId/state/volume"

    fun cmdLaunch(prefix: String, deviceId: String) = "$prefix/$deviceId/cmd/launch"
    fun cmdKey(prefix: String, deviceId: String) = "$prefix/$deviceId/cmd/key"
    fun cmdVolume(prefix: String, deviceId: String) = "$prefix/$deviceId/cmd/volume"
    fun cmdPower(prefix: String, deviceId: String) = "$prefix/$deviceId/cmd/power"
    fun cmdMedia(prefix: String, deviceId: String) = "$prefix/$deviceId/cmd/media"
}
