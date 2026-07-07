package dev.harrypulvirenti.fire2mqtt.data

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class SettingsRepositoryTest {

    @Test fun `slugify lowercases and collapses non-alphanumerics to underscore`() {
        assertEquals("living_room_tv", "Living Room TV".slugify())
    }

    @Test fun `slugify strips leading and trailing separators`() {
        assertEquals("fire_tv", "  Fire TV!! ".slugify())
    }

    @Test fun `slugify is a no-op on an already-valid slug`() {
        assertEquals("living_room_fire_tv", "living_room_fire_tv".slugify())
    }
}
