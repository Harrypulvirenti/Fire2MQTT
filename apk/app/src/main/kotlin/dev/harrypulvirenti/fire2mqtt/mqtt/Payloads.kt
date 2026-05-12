package dev.harrypulvirenti.fire2mqtt.mqtt

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PlaybackPayload(
    @SerialName("media_session_state") val mediaSessionState: Int,
    val app: String = "",
    val title: String? = null,
    val artist: String? = null,
    val album: String? = null,
    @SerialName("duration_ms") val durationMs: Long? = null,
    @SerialName("position_ms") val positionMs: Long? = null,
    val ts: Long = System.currentTimeMillis(),
)

@Serializable
data class AppPayload(
    val `package`: String,
    val name: String,
    val ts: Long = System.currentTimeMillis(),
)

@Serializable
data class ScreenPayload(
    val on: Boolean,
    val ts: Long = System.currentTimeMillis(),
)

@Serializable
data class VolumePayload(
    val level: Int,
    val max: Int,
    val mute: Boolean,
    val ts: Long = System.currentTimeMillis(),
)

@Serializable
data class DevicePayload(
    val model: String,
    @SerialName("fire_os") val fireOs: String,
    val ip: String,
    val mac: String,
    @SerialName("schema_version") val schemaVersion: Int = TopicSchema.SCHEMA_VERSION,
)

@Serializable
data class VolumeCommandPayload(
    val action: String,   // "set" | "up" | "down" | "mute" | "unmute"
    val level: Int? = null,
)
