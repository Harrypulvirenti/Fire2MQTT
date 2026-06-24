package dev.harrypulvirenti.fire2mqtt.mqtt

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
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
        // (schema_version is omitted here because it equals its serialization default.)
        assertTrue(json.contains("\"app_version\":\"0.2.0-beta5\""), json)
        assertTrue(json.contains("\"app_version_code\":2"), json)
    }

    @Test fun `installed apps payload serializes its packages`() {
        val json = Json.encodeToString(
            InstalledAppsPayload(packages = listOf("com.netflix.ninja", "org.jellyfin.androidtv"), ts = 1)
        )
        assertTrue(json.contains("\"packages\":[\"com.netflix.ninja\",\"org.jellyfin.androidtv\"]"), json)
    }
}
