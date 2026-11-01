package dev.harrypulvirenti.fire2mqtt.system

import dev.harrypulvirenti.fire2mqtt.system.UsageStatsForegroundSource.Companion.latestForeground
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

private const val OWN = "dev.harrypulvirenti.fire2mqtt"

class UsageStatsForegroundSourceTest {

    @Test fun `newest foreground event wins`() {
        val events = listOf("com.netflix" to 100L, "com.hbo" to 300L, "com.amazon.tv.launcher" to 200L)
        assertEquals("com.hbo", latestForeground(events, OWN))
    }

    @Test fun `our own UI is skipped`() {
        val events = listOf("com.netflix" to 100L, OWN to 200L)
        assertEquals("com.netflix", latestForeground(events, OWN))
    }

    @Test fun `nothing new yields null`() {
        assertNull(latestForeground(emptyList(), OWN))
        assertNull(latestForeground(listOf(OWN to 1L, "" to 2L), OWN))
    }
}
