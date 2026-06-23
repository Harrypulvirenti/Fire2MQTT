package dev.harrypulvirenti.fire2mqtt.data

import android.content.Intent

/**
 * Broker settings handed to the app by Home Assistant's ADB provisioning step.
 *
 * The integration launches [dev.harrypulvirenti.fire2mqtt.ui.MainActivity] with these
 * values as Intent extras (see `custom_components/fire2mqtt/const.py` `EXTRA_*` and
 * `adb_provision._build_launch_cmd`), so the user configures the broker once in Home
 * Assistant instead of typing it on the TV remote. Fields are null when the matching
 * extra is absent; only non-null fields are persisted.
 */
data class ProvisioningConfig(
    val host: String? = null,
    val port: Int? = null,
    val username: String? = null,
    val password: String? = null,
    val deviceId: String? = null,
    val topicPrefix: String? = null,
    val useTls: Boolean? = null,
)

/**
 * Parses the launch-intent wire contract. The extra keys here are the APK half of the
 * contract and must stay in sync with the integration's `EXTRA_*` constants. All extras
 * arrive as strings (`am start --es`); [port] and [useTls] are parsed from those strings.
 */
object ProvisioningExtras {
    const val EXTRA_BROKER_HOST = "broker_host"
    const val EXTRA_BROKER_PORT = "broker_port"
    const val EXTRA_BROKER_USERNAME = "broker_username"
    const val EXTRA_BROKER_PASSWORD = "broker_password"
    const val EXTRA_TOPIC_PREFIX = "topic_prefix"
    const val EXTRA_DEVICE_ID = "device_id"
    const val EXTRA_USE_TLS = "use_tls"

    private val KEYS = listOf(
        EXTRA_BROKER_HOST, EXTRA_BROKER_PORT, EXTRA_BROKER_USERNAME, EXTRA_BROKER_PASSWORD,
        EXTRA_TOPIC_PREFIX, EXTRA_DEVICE_ID, EXTRA_USE_TLS,
    )

    /** Pure parse from a key→value map. Returns null if no broker extras are present. */
    fun parse(values: Map<String, String?>): ProvisioningConfig? {
        if (KEYS.none { values[it] != null }) return null
        return ProvisioningConfig(
            host        = values[EXTRA_BROKER_HOST],
            port        = values[EXTRA_BROKER_PORT]?.toIntOrNull(),
            username    = values[EXTRA_BROKER_USERNAME],
            password    = values[EXTRA_BROKER_PASSWORD],
            deviceId    = values[EXTRA_DEVICE_ID],
            topicPrefix = values[EXTRA_TOPIC_PREFIX],
            useTls      = values[EXTRA_USE_TLS]?.equals("true", ignoreCase = true),
        )
    }

    /** Intent adapter over [parse]; reads each known extra as a string. */
    fun parse(intent: Intent?): ProvisioningConfig? {
        if (intent == null) return null
        return parse(KEYS.associateWith { intent.getStringExtra(it) })
    }
}
