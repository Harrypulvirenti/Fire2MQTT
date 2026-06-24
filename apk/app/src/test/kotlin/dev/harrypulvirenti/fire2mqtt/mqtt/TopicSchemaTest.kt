package dev.harrypulvirenti.fire2mqtt.mqtt

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class TopicSchemaTest {

    private val prefix = "home"
    private val deviceId = "firestick"

    @Test fun schemaVersion() = assertEquals(2, TopicSchema.SCHEMA_VERSION)

    @Test fun status() = assertEquals("home/firestick/status", TopicSchema.status(prefix, deviceId))
    @Test fun stateDevice() = assertEquals("home/firestick/state/device", TopicSchema.stateDevice(prefix, deviceId))
    @Test fun statePlayback() = assertEquals("home/firestick/state/playback", TopicSchema.statePlayback(prefix, deviceId))
    @Test fun stateApp() = assertEquals("home/firestick/state/app", TopicSchema.stateApp(prefix, deviceId))
    @Test fun stateApps() = assertEquals("home/firestick/state/apps", TopicSchema.stateApps(prefix, deviceId))
    @Test fun stateScreen() = assertEquals("home/firestick/state/screen", TopicSchema.stateScreen(prefix, deviceId))
    @Test fun stateVolume() = assertEquals("home/firestick/state/volume", TopicSchema.stateVolume(prefix, deviceId))

    @Test fun cmdLaunch() = assertEquals("home/firestick/cmd/launch", TopicSchema.cmdLaunch(prefix, deviceId))
    @Test fun cmdKey() = assertEquals("home/firestick/cmd/key", TopicSchema.cmdKey(prefix, deviceId))
    @Test fun cmdVolume() = assertEquals("home/firestick/cmd/volume", TopicSchema.cmdVolume(prefix, deviceId))
    @Test fun cmdPower() = assertEquals("home/firestick/cmd/power", TopicSchema.cmdPower(prefix, deviceId))
    @Test fun cmdMedia() = assertEquals("home/firestick/cmd/media", TopicSchema.cmdMedia(prefix, deviceId))

    @Test fun `nested prefix segments are preserved`() {
        assertEquals("ha/living/room/tv/state/screen", TopicSchema.stateScreen("ha/living/room", "tv"))
    }
}
