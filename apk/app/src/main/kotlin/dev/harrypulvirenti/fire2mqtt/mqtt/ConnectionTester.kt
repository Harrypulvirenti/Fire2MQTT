package dev.harrypulvirenti.fire2mqtt.mqtt

import com.hivemq.client.mqtt.mqtt5.Mqtt5Client
import dev.harrypulvirenti.fire2mqtt.data.SettingsRepository.MqttSettings
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.future.await
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.koin.core.annotation.Factory
import java.util.UUID

private const val CONNECT_TIMEOUT_MS = 5_000L

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

        // Cleartext is LAN-only (so credentials can't leak to a public host); TLS encrypts
        // the connection, so any host is allowed and the original hostname is kept for cert
        // verification. Mirrors Fire2MqttService.startPipeline.
        val targetHost = if (settings.useTls) {
            host
        } else {
            BrokerHostValidator.resolveToPrivateAddress(host)
                ?: return@withContext TestResult.BadHost(host)
        }

        val builder = Mqtt5Client.builder()
            .identifier("fire2mqtt_probe_${UUID.randomUUID()}")
            .serverHost(targetHost)
            .serverPort(port)

        if (settings.useTls) builder.sslWithDefaultConfig()

        if (username.isNotBlank()) {
            val auth = builder.simpleAuth().username(username)
            if (password.isNotBlank()) auth.password(password.toByteArray())
            auth.applySimpleAuth()
        }

        val client = builder.buildAsync()
        try {
            // await() suspends instead of blocking the IO thread and propagates
            // coroutine cancellation to the probe.
            withTimeout(CONNECT_TIMEOUT_MS) {
                client.connectWith().cleanStart(true).send().await()
            }
            runCatching { client.disconnectWith().send() }
            TestResult.Connected(host, port)
        } catch (e: TimeoutCancellationException) {
            runCatching { client.disconnectWith().send() }
            TestResult.TimedOut(host, port)
        } catch (e: CancellationException) {
            // Caller (e.g. viewModelScope) was cancelled — clean up and rethrow.
            runCatching { client.disconnectWith().send() }
            throw e
        } catch (e: Exception) {
            runCatching { client.disconnectWith().send() }
            TestResult.Failed(e.cause?.message ?: e.message ?: "unknown error")
        }
    }
}
