package dev.harrypulvirenti.fire2mqtt.mqtt

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class PayloadsTest {

    @Test fun `device payload serializes the app version wire keys`() {
        val json = Json.encodeToString(
            DevicePayload(
                model = "Fire TV Stick 4K",
                fireOs = "8.2.2.1",
                ip = "10.0.0.50",
                mac = "de:ad:be:ef:00:01",
                appVersion = "0.2.0-beta5",
                appVersionCode = 2,
            )
        )
        // These keys are the wire contract HA's update entity reads — keep them stable.
        assertTrue(json.contains("\"app_version\":\"0.2.0-beta5\""), json)
        assertTrue(json.contains("\"app_version_code\":2"), json)
    }

    @Test fun `installed apps payload serializes its packages`() {
        val json = Json.encodeToString(
            InstalledAppsPayload(packages = listOf("com.netflix.ninja", "org.jellyfin.androidtv"), ts = 1)
        )
        assertTrue(json.contains("\"packages\":[\"com.netflix.ninja\",\"org.jellyfin.androidtv\"]"), json)
    }

    @Test fun `wire json always writes schema_version and ts`() {
        // Plain Json drops values equal to their default — schema_version always, and ts when
        // encoding lands in the same millisecond as construction.
        val device = WireJson.encodeToString(
            DevicePayload(model = "m", fireOs = "14", ip = "10.0.0.2", mac = "unknown")
        )
        assertTrue(device.contains("\"schema_version\":${TopicSchema.SCHEMA_VERSION}"), device)

        val app = WireJson.encodeToString(AppPayload(`package` = "com.netflix.ninja", name = "Netflix"))
        assertTrue(app.contains("\"ts\":"), app)
    }

    @Test fun `wire json still omits absent optional fields`() {
        val playback = WireJson.encodeToString(PlaybackPayload(mediaSessionState = 0))
        assertFalse(playback.contains("title"), playback)
        assertFalse(playback.contains("null"), playback)
    }
}
