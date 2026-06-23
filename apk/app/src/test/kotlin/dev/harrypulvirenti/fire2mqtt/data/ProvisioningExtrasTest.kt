package dev.harrypulvirenti.fire2mqtt.data

import dev.harrypulvirenti.fire2mqtt.data.ProvisioningExtras.EXTRA_BROKER_HOST
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningExtras.EXTRA_BROKER_PASSWORD
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningExtras.EXTRA_BROKER_PORT
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningExtras.EXTRA_BROKER_USERNAME
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningExtras.EXTRA_DEVICE_ID
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningExtras.EXTRA_TOPIC_PREFIX
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningExtras.EXTRA_USE_TLS
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class ProvisioningExtrasTest {

    @Test fun `returns null when no broker extras present`() {
        assertNull(ProvisioningExtras.parse(emptyMap()))
        assertNull(ProvisioningExtras.parse(mapOf("unrelated" to "x")))
    }

    @Test fun `parses all provided fields`() {
        val cfg = ProvisioningExtras.parse(
            mapOf(
                EXTRA_BROKER_HOST to "192.168.1.10",
                EXTRA_BROKER_PORT to "8883",
                EXTRA_BROKER_USERNAME to "user",
                EXTRA_BROKER_PASSWORD to "pass",
                EXTRA_DEVICE_ID to "living_room",
                EXTRA_TOPIC_PREFIX to "fire2mqtt",
                EXTRA_USE_TLS to "true",
            )
        )!!
        assertEquals("192.168.1.10", cfg.host)
        assertEquals(8883, cfg.port)
        assertEquals("user", cfg.username)
        assertEquals("pass", cfg.password)
        assertEquals("living_room", cfg.deviceId)
        assertEquals("fire2mqtt", cfg.topicPrefix)
        assertEquals(true, cfg.useTls)
    }

    @Test fun `absent fields stay null when only some extras are present`() {
        val cfg = ProvisioningExtras.parse(mapOf(EXTRA_BROKER_HOST to "h"))!!
        assertEquals("h", cfg.host)
        assertNull(cfg.port)
        assertNull(cfg.username)
        assertNull(cfg.useTls)
    }

    @Test fun `invalid port becomes null rather than throwing`() {
        val cfg = ProvisioningExtras.parse(
            mapOf(EXTRA_BROKER_HOST to "h", EXTRA_BROKER_PORT to "notanumber")
        )!!
        assertNull(cfg.port)
    }

    @Test fun `use_tls parses case-insensitively and defaults non-true to false`() {
        assertEquals(true, ProvisioningExtras.parse(mapOf(EXTRA_USE_TLS to "TRUE"))!!.useTls)
        assertEquals(false, ProvisioningExtras.parse(mapOf(EXTRA_USE_TLS to "false"))!!.useTls)
        assertEquals(false, ProvisioningExtras.parse(mapOf(EXTRA_USE_TLS to "garbage"))!!.useTls)
    }
}
