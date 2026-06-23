package dev.harrypulvirenti.fire2mqtt.ui

import android.app.Application
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.data.PermissionChecker
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningConfig
import dev.harrypulvirenti.fire2mqtt.data.SettingsRepository
import dev.harrypulvirenti.fire2mqtt.data.SettingsRepository.MqttSettings
import dev.harrypulvirenti.fire2mqtt.mqtt.ConnectionTester
import dev.harrypulvirenti.fire2mqtt.mqtt.TestResult
import dev.harrypulvirenti.fire2mqtt.service.Fire2MqttService
import io.mockk.Called
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import io.mockk.unmockkAll
import io.mockk.verify
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

private val SETTINGS = MqttSettings(
    host = "192.168.1.10",
    port = 1883,
    username = "user",
    password = "pass",
    deviceId = "fire_tv",
    topicPrefix = "fire2mqtt",
)

@OptIn(ExperimentalCoroutinesApi::class)
class SetupViewModelTest {

    private val dispatcher = StandardTestDispatcher()
    private lateinit var app: Application
    private lateinit var repository: SettingsRepository
    private lateinit var permissionChecker: PermissionChecker
    private lateinit var connectionTester: ConnectionTester

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(dispatcher)
        app = mockk(relaxed = true)
        repository = mockk(relaxed = true)
        coEvery { repository.load() } returns SETTINGS
        permissionChecker = mockk {
            every { hasWriteSecureSettings() } returns true
            every { enableAll() } returns true
            every { hasAccessibility() } returns true
            every { hasNotification() } returns true
        }
        connectionTester = mockk()
    }

    @AfterEach
    fun tearDown() {
        Fire2MqttService._running.value = false
        Dispatchers.resetMain()
        unmockkAll()
    }

    private fun vm() = SetupViewModel(app, repository, permissionChecker, connectionTester, dispatcher)

    // --- initial load ---

    @Test fun `initial load populates settings and permissions then flips ready`() = runTest(dispatcher) {
        val vm = vm()
        assertFalse(vm.state.value.ready)

        advanceUntilIdle()
        val s = vm.state.value
        assertEquals("192.168.1.10", s.host)
        assertEquals(1883, s.port)
        assertEquals("user", s.username)
        assertEquals("fire_tv", s.deviceId)
        assertEquals("fire2mqtt", s.topicPrefix)
        assertTrue(s.ready)
        assertTrue(s.perms.allGranted)
        assertTrue(s.writeSecureSettings)
        assertEquals(ConnState.Disconnected, s.connection)
        assertEquals(TextValue.TextResource(R.string.msg_not_tested), s.connectionMessage)
    }

    @Test fun `initial load with blank host shows no-broker message`() = runTest(dispatcher) {
        coEvery { repository.load() } returns SETTINGS.copy(host = "")
        val vm = vm()
        advanceUntilIdle()
        assertEquals(TextValue.TextResource(R.string.msg_no_broker), vm.state.value.connectionMessage)
    }

    @Test fun `held WRITE_SECURE_SETTINGS triggers self-enable on load`() = runTest(dispatcher) {
        vm()
        advanceUntilIdle()
        verify { permissionChecker.enableAll() }
    }

    // --- field setters ---

    @Test fun `updateHost persists and resets connection state`() = runTest(dispatcher) {
        val vm = vm()
        advanceUntilIdle()

        vm.updateHost("10.0.0.5")
        val s = vm.state.value
        assertEquals("10.0.0.5", s.host)
        assertEquals(ConnState.Disconnected, s.connection)
        assertEquals(TextValue.TextResource(R.string.msg_not_tested), s.connectionMessage)

        advanceUntilIdle()
        coVerify { repository.setHost("10.0.0.5") }
    }

    @Test fun `clearing host shows no-broker message`() = runTest(dispatcher) {
        val vm = vm()
        advanceUntilIdle()
        vm.updateHost("")
        assertEquals(TextValue.TextResource(R.string.msg_no_broker), vm.state.value.connectionMessage)
    }

    @Test fun `updatePort persists the new value`() = runTest(dispatcher) {
        val vm = vm()
        advanceUntilIdle()
        vm.updatePort(8883)
        assertEquals(8883, vm.state.value.port)
        advanceUntilIdle()
        coVerify { repository.setPort(8883) }
    }

    @Test fun `updateUseTls persists and resets connection state`() = runTest(dispatcher) {
        val vm = vm()
        advanceUntilIdle()
        vm.updateUseTls(true)
        assertTrue(vm.state.value.useTls)
        assertEquals(ConnState.Disconnected, vm.state.value.connection)
        advanceUntilIdle()
        coVerify { repository.setUseTls(true) }
    }

    // --- applyProvisioning (HA ADB credential injection) ---

    @Test fun `applyProvisioning persists config and reflects it in state`() = runTest(dispatcher) {
        val provisioned = SETTINGS.copy(
            host = "10.0.0.9", port = 8883, useTls = true, deviceId = "den_tv",
        )
        coEvery { repository.load() } returnsMany listOf(SETTINGS, provisioned)
        val vm = vm()
        advanceUntilIdle()

        val config = ProvisioningConfig(
            host = "10.0.0.9", port = 8883, useTls = true, deviceId = "den_tv",
        )
        vm.applyProvisioning(config)
        advanceUntilIdle()

        coVerify { repository.applyProvisioning(config) }
        val s = vm.state.value
        assertEquals("10.0.0.9", s.host)
        assertEquals(8883, s.port)
        assertTrue(s.useTls)
        assertEquals("den_tv", s.deviceId)
    }

    // --- testConnection ---

    @Test fun `testConnection success maps to Connected`() = runTest(dispatcher) {
        coEvery { connectionTester.test(any()) } returns TestResult.Connected("192.168.1.10", 1883)
        val vm = vm()
        advanceUntilIdle()

        vm.testConnection()
        assertEquals(ConnState.Testing, vm.state.value.connection)

        advanceUntilIdle()
        val s = vm.state.value
        assertEquals(ConnState.Connected, s.connection)
        assertEquals(
            TextValue.TextResource(R.string.msg_connected, listOf("192.168.1.10", 1883)),
            s.connectionMessage,
        )
    }

    @Test fun `testConnection timeout maps to Failed with timed-out message`() = runTest(dispatcher) {
        coEvery { connectionTester.test(any()) } returns TestResult.TimedOut("192.168.1.10", 1883)
        val vm = vm()
        advanceUntilIdle()
        vm.testConnection()
        advanceUntilIdle()
        assertEquals(ConnState.Failed, vm.state.value.connection)
        assertEquals(
            TextValue.TextResource(R.string.msg_timed_out, listOf("192.168.1.10", 1883)),
            vm.state.value.connectionMessage,
        )
    }

    @Test fun `testConnection bad host maps to Failed with bad-host message`() = runTest(dispatcher) {
        coEvery { connectionTester.test(any()) } returns TestResult.BadHost("192.168.1.10")
        val vm = vm()
        advanceUntilIdle()
        vm.testConnection()
        advanceUntilIdle()
        assertEquals(ConnState.Failed, vm.state.value.connection)
        assertEquals(
            TextValue.TextResource(R.string.msg_bad_host, listOf("192.168.1.10")),
            vm.state.value.connectionMessage,
        )
    }

    @Test fun `testConnection error maps to Failed with reason`() = runTest(dispatcher) {
        coEvery { connectionTester.test(any()) } returns TestResult.Failed("connection refused")
        val vm = vm()
        advanceUntilIdle()
        vm.testConnection()
        advanceUntilIdle()
        assertEquals(ConnState.Failed, vm.state.value.connection)
        assertEquals(
            TextValue.TextResource(R.string.msg_failed, listOf("connection refused")),
            vm.state.value.connectionMessage,
        )
    }

    @Test fun `testConnection with blank host fails fast without probing`() = runTest(dispatcher) {
        coEvery { repository.load() } returns SETTINGS.copy(host = "")
        val vm = vm()
        advanceUntilIdle()

        vm.testConnection()
        advanceUntilIdle()
        assertEquals(ConnState.Failed, vm.state.value.connection)
        assertEquals(TextValue.TextResource(R.string.msg_no_host), vm.state.value.connectionMessage)
        coVerify(exactly = 0) { connectionTester.test(any()) }
    }

    // --- service state ---

    @Test fun `service running flow drives connection state both ways`() = runTest(dispatcher) {
        val vm = vm()
        advanceUntilIdle()

        Fire2MqttService._running.value = true
        advanceUntilIdle()
        var s = vm.state.value
        assertTrue(s.isServiceRunning)
        assertEquals(ConnState.Running, s.connection)
        assertEquals(TextValue.TextResource(R.string.msg_publishing), s.connectionMessage)

        Fire2MqttService._running.value = false
        advanceUntilIdle()
        s = vm.state.value
        assertFalse(s.isServiceRunning)
        assertEquals(ConnState.Connected, s.connection)
        assertEquals(TextValue.TextResource(R.string.msg_service_stopped), s.connectionMessage)
    }

    @Test fun `service already running at startup survives the initial load`() = runTest(dispatcher) {
        Fire2MqttService._running.value = true
        val vm = vm()
        advanceUntilIdle()
        assertTrue(vm.state.value.isServiceRunning)
        assertEquals(ConnState.Running, vm.state.value.connection)
        assertTrue(vm.state.value.ready)
    }

    @Test fun `startService is a no-op while canStart is false`() = runTest(dispatcher) {
        val vm = vm()
        advanceUntilIdle()

        assertFalse(vm.state.value.canStart) // never tested -> Disconnected
        vm.startService()
        verify { app wasNot Called }
    }

    // --- contract ---

    @Test fun `canStart requires a reachable broker and both permissions`() {
        val ok = SetupUiState(connection = ConnState.Connected, perms = Perms(true, true))
        assertTrue(ok.canStart)
        assertTrue(ok.copy(connection = ConnState.Running).canStart)
        assertFalse(ok.copy(connection = ConnState.Disconnected).canStart)
        assertFalse(ok.copy(connection = ConnState.Failed).canStart)
        assertFalse(ok.copy(perms = Perms(accessibility = true, notification = false)).canStart)
        assertFalse(ok.copy(perms = Perms(accessibility = false, notification = true)).canStart)
    }
}
