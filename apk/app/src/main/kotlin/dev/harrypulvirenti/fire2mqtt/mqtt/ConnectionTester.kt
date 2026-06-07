package dev.harrypulvirenti.fire2mqtt.mqtt

import com.hivemq.client.mqtt.mqtt5.Mqtt5Client
import dev.harrypulvirenti.fire2mqtt.data.SettingsRepository.MqttSettings
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.koin.core.annotation.Factory
import java.util.UUID
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

/** Result of a one-shot connection probe. */
sealed interface TestResult {
    /** Successfully connected and cleanly disconnected. */
    data class Connected(val host: String, val port: Int) : TestResult

    /** TCP connect timed out (5 s). */
    data class TimedOut(val host: String, val port: Int) : TestResult

    /** Connection attempt threw an unexpected exception. */
    data class Failed(val reason: String) : TestResult

    /** Host field is blank — nothing to probe. */
    object NoHost : TestResult

    /** Host did not resolve to a private/LAN address. */
    data class BadHost(val host: String) : TestResult
}

/**
 * Probes an MQTT broker with a short-lived MQTT 5 client.
 * All network work is dispatched to [Dispatchers.IO] internally.
 */
@Factory
class ConnectionTester {

    suspend fun test(settings: MqttSettings): TestResult = withContext(Dispatchers.IO) {
        val host     = settings.host
        val port     = settings.port
        val username = settings.username
        val password = settings.password

        if (host.isBlank()) return@withContext TestResult.NoHost

        val resolvedHost = BrokerHostValidator.resolveToPrivateAddress(host)
            ?: return@withContext TestResult.BadHost(host)

        val builder = Mqtt5Client.builder()
            .identifier("fire2mqtt_probe_${UUID.randomUUID()}")
            .serverHost(resolvedHost)
            .serverPort(port)

        if (username.isNotBlank()) {
            val auth = builder.simpleAuth().username(username)
            if (password.isNotBlank()) auth.password(password.toByteArray())
            auth.applySimpleAuth()
        }

        val client = builder.buildAsync()
        try {
            client.connectWith().cleanStart(true).send().get(5, TimeUnit.SECONDS)
            runCatching { client.disconnectWith().send() }
            TestResult.Connected(host, port)
        } catch (e: TimeoutException) {
            runCatching { client.disconnectWith().send() }
            TestResult.TimedOut(host, port)
        } catch (e: Exception) {
            runCatching { client.disconnectWith().send() }
            TestResult.Failed(e.cause?.message ?: e.message ?: "unknown error")
        }
    }
}
