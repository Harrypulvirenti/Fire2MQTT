package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.media.AudioManager
import android.view.KeyEvent
import dev.harrypulvirenti.fire2mqtt.mqtt.TopicSchema
import io.mockk.every
import io.mockk.just
import io.mockk.mockk
import io.mockk.mockkConstructor
import io.mockk.mockkObject
import io.mockk.runs
import io.mockk.unmockkAll
import io.mockk.verify
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.CsvSource
import org.junit.jupiter.params.provider.ValueSource

private const val PREFIX = "home"
private const val DEVICE_ID = "firestick"

class CommandRouterTest {

    private lateinit var router: CommandRouter

    @BeforeEach
    fun setUp() {
        mockkConstructor(AppLauncher::class)
        mockkConstructor(VolumeController::class)
        mockkObject(Fire2MqttAccessibilityService.Companion)

        every { anyConstructed<AppLauncher>().launch(any()) } returns true
        every { anyConstructed<VolumeController>().set(any()) } just runs
        every { anyConstructed<VolumeController>().stepUp() } just runs
        every { anyConstructed<VolumeController>().stepDown() } just runs
        every { anyConstructed<VolumeController>().mute() } just runs
        every { anyConstructed<VolumeController>().unmute() } just runs
        every { Fire2MqttAccessibilityService.sendKey(any()) } returns true

        // VolumeController's real constructor calls context.getSystemService(AudioManager) —
        // provide a proper mock so the cast succeeds (mockkConstructor runs the constructor body).
        val audioManager = mockk<AudioManager>(relaxed = true)
        val context = mockk<Context>(relaxed = true)
        every { context.getSystemService(AudioManager::class.java) } returns audioManager
        router = CommandRouter(context, PREFIX, DEVICE_ID)
    }

    @AfterEach
    fun tearDown() = unmockkAll()

    // --- cmdLaunch ---

    @Test fun `cmdLaunch routes package name to AppLauncher`() {
        router.route(TopicSchema.cmdLaunch(PREFIX, DEVICE_ID), "com.example.app")
        verify { anyConstructed<AppLauncher>().launch("com.example.app") }
    }

    @Test fun `cmdLaunch trims whitespace from payload`() {
        router.route(TopicSchema.cmdLaunch(PREFIX, DEVICE_ID), "  com.example.app  ")
        verify { anyConstructed<AppLauncher>().launch("com.example.app") }
    }

    // --- cmdKey ---

    @ParameterizedTest
    @CsvSource(
        "HOME, ${KeyEvent.KEYCODE_HOME}",
        "BACK, ${KeyEvent.KEYCODE_BACK}",
        "DPAD_UP, ${KeyEvent.KEYCODE_DPAD_UP}",
        "DPAD_DOWN, ${KeyEvent.KEYCODE_DPAD_DOWN}",
        "DPAD_LEFT, ${KeyEvent.KEYCODE_DPAD_LEFT}",
        "DPAD_RIGHT, ${KeyEvent.KEYCODE_DPAD_RIGHT}",
        "DPAD_CENTER, ${KeyEvent.KEYCODE_DPAD_CENTER}",
        "MEDIA_PLAY_PAUSE, ${KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE}",
    )
    fun `cmdKey dispatches correct keycode`(keyName: String, expectedCode: Int) {
        router.route(TopicSchema.cmdKey(PREFIX, DEVICE_ID), keyName)
        verify { Fire2MqttAccessibilityService.sendKey(expectedCode) }
    }

    @ParameterizedTest
    @ValueSource(strings = ["home", "Home", "hOmE"])
    fun `cmdKey is case-insensitive`(keyName: String) {
        router.route(TopicSchema.cmdKey(PREFIX, DEVICE_ID), keyName)
        verify { Fire2MqttAccessibilityService.sendKey(KeyEvent.KEYCODE_HOME) }
    }

    @Test fun `cmdKey with unknown name does not dispatch`() {
        router.route(TopicSchema.cmdKey(PREFIX, DEVICE_ID), "UNKNOWN_KEY")
        verify(exactly = 0) { Fire2MqttAccessibilityService.sendKey(any()) }
    }

    // --- cmdVolume ---

    @Test fun `cmdVolume set calls VolumeController set with level`() {
        router.route(TopicSchema.cmdVolume(PREFIX, DEVICE_ID), """{"action":"set","level":10}""")
        verify { anyConstructed<VolumeController>().set(10) }
    }

    @Test fun `cmdVolume up calls stepUp`() {
        router.route(TopicSchema.cmdVolume(PREFIX, DEVICE_ID), """{"action":"up"}""")
        verify { anyConstructed<VolumeController>().stepUp() }
    }

    @Test fun `cmdVolume down calls stepDown`() {
        router.route(TopicSchema.cmdVolume(PREFIX, DEVICE_ID), """{"action":"down"}""")
        verify { anyConstructed<VolumeController>().stepDown() }
    }

    @Test fun `cmdVolume mute calls mute`() {
        router.route(TopicSchema.cmdVolume(PREFIX, DEVICE_ID), """{"action":"mute"}""")
        verify { anyConstructed<VolumeController>().mute() }
    }

    @Test fun `cmdVolume unmute calls unmute`() {
        router.route(TopicSchema.cmdVolume(PREFIX, DEVICE_ID), """{"action":"unmute"}""")
        verify { anyConstructed<VolumeController>().unmute() }
    }

    @Test fun `cmdVolume malformed JSON does not crash`() {
        router.route(TopicSchema.cmdVolume(PREFIX, DEVICE_ID), "not-json")
        verify(exactly = 0) { anyConstructed<VolumeController>().set(any()) }
        verify(exactly = 0) { anyConstructed<VolumeController>().stepUp() }
    }

    // --- cmdPower ---

    @Test fun `cmdPower sleep dispatches KEYCODE_SLEEP`() {
        router.route(TopicSchema.cmdPower(PREFIX, DEVICE_ID), "sleep")
        verify { Fire2MqttAccessibilityService.sendKey(KeyEvent.KEYCODE_SLEEP) }
    }

    @Test fun `cmdPower wake dispatches KEYCODE_WAKEUP`() {
        router.route(TopicSchema.cmdPower(PREFIX, DEVICE_ID), "wake")
        verify { Fire2MqttAccessibilityService.sendKey(KeyEvent.KEYCODE_WAKEUP) }
    }

    @Test fun `cmdPower unknown payload does nothing`() {
        router.route(TopicSchema.cmdPower(PREFIX, DEVICE_ID), "reboot")
        verify(exactly = 0) { Fire2MqttAccessibilityService.sendKey(any()) }
    }

    // --- cmdMedia ---

    @ParameterizedTest
    @CsvSource(
        "play, ${KeyEvent.KEYCODE_MEDIA_PLAY}",
        "pause, ${KeyEvent.KEYCODE_MEDIA_PAUSE}",
        "play_pause, ${KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE}",
        "next, ${KeyEvent.KEYCODE_MEDIA_NEXT}",
        "prev, ${KeyEvent.KEYCODE_MEDIA_PREVIOUS}",
        "stop, ${KeyEvent.KEYCODE_MEDIA_STOP}",
    )
    fun `cmdMedia dispatches correct keycode`(command: String, expectedCode: Int) {
        router.route(TopicSchema.cmdMedia(PREFIX, DEVICE_ID), command)
        verify { Fire2MqttAccessibilityService.sendKey(expectedCode) }
    }

    @Test fun `cmdMedia unknown command does nothing`() {
        router.route(TopicSchema.cmdMedia(PREFIX, DEVICE_ID), "skip")
        verify(exactly = 0) { Fire2MqttAccessibilityService.sendKey(any()) }
    }

    // --- unknown topic ---

    @Test fun `unknown topic is silently ignored`() {
        router.route("totally/unknown/topic", "payload")
        verify(exactly = 0) { anyConstructed<AppLauncher>().launch(any()) }
        verify(exactly = 0) { Fire2MqttAccessibilityService.sendKey(any()) }
    }
}
