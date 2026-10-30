package dev.harrypulvirenti.fire2mqtt.system

import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class SecureSettingsManagerTest {

    private val ours = "dev.harrypulvirenti.fire2mqtt/.commands.Fire2MqttAccessibilityService"
    private val other = "com.example/.OtherService"

    @Test fun `toggle removes then re-adds our component and keeps others`() = runTest {
        var setting = setOf(other, ours)
        val events = mutableListOf<String>()

        SecureSettingsManager.toggleComponent(
            component = ours,
            read = { setting },
            write = { setting = it; events += "write $it" },
            pause = { events += "pause" },
        )

        assertEquals(listOf("write ${setOf(other)}", "pause", "write ${setOf(other, ours)}"), events)
        assertEquals(setOf(other, ours), setting)
    }

    @Test fun `toggle with only our component empties the list in between`() = runTest {
        var setting = setOf(ours)
        val writes = mutableListOf<Set<String>>()

        SecureSettingsManager.toggleComponent(
            component = ours,
            read = { setting },
            write = { setting = it; writes += it },
            pause = {},
        )

        assertEquals(listOf(emptySet(), setOf(ours)), writes)
    }
}
