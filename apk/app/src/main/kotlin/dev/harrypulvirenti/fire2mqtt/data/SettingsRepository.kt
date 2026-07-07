package dev.harrypulvirenti.fire2mqtt.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.SharedPreferencesMigration
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import org.koin.core.annotation.Single

/**
 * Single process-wide Preferences DataStore. On first access it migrates (and then
 * deletes) the legacy "${packageName}_preferences" SharedPreferences file — the one
 * PreferenceManager.getDefaultSharedPreferences() used historically — so existing
 * installs keep their broker settings.
 */
private val Context.settingsDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "fire2mqtt_settings",
    produceMigrations = { context ->
        listOf(SharedPreferencesMigration(context, "${context.packageName}_preferences"))
    },
)

/**
 * Broker/device settings on Preferences DataStore: reads are a [Flow], writes are
 * suspend and serialized by DataStore — no main-thread disk I/O either way.
 *
 * Key names and defaults are frozen — prior installs (via the SharedPreferences
 * migration above) and the running service depend on them. Port stays string-typed
 * on the wire format because that's how the legacy preference stored it.
 */
@Single
class SettingsRepository(private val context: Context) {

    data class MqttSettings(
        val host: String,
        val port: Int,
        val username: String,
        val password: String,
        val deviceId: String,
        val topicPrefix: String,
        val useTls: Boolean = false,
    )

    /** Live settings stream — emits on every persisted change. */
    val settings: Flow<MqttSettings> = context.settingsDataStore.data.map { prefs ->
        MqttSettings(
            host        = prefs[KEY_HOST] ?: DEFAULT_HOST,
            port        = prefs[KEY_PORT]?.toIntOrNull() ?: DEFAULT_PORT,
            username    = prefs[KEY_USERNAME] ?: DEFAULT_USERNAME,
            password    = prefs[KEY_PASSWORD] ?: DEFAULT_PASSWORD,
            deviceId    = prefs[KEY_DEVICE_ID] ?: DEFAULT_DEVICE_ID,
            topicPrefix = prefs[KEY_TOPIC_PREFIX] ?: DEFAULT_TOPIC_PREFIX,
            useTls      = (prefs[KEY_USE_TLS] ?: DEFAULT_USE_TLS).toBoolean(),
        )
    }

    /** One-shot snapshot of [settings]. */
    suspend fun load(): MqttSettings = settings.first()

    suspend fun setHost(value: String) = set(KEY_HOST, value)

    /** Persisted as a String to preserve the string-typed key used historically. */
    suspend fun setPort(value: Int) = set(KEY_PORT, value.toString())

    suspend fun setUsername(value: String) = set(KEY_USERNAME, value)

    suspend fun setPassword(value: String) = set(KEY_PASSWORD, value)

    /**
     * Slugified the same way Home Assistant's config flow slugifies device names
     * (lowercase, non-alphanumeric runs collapsed to `_`, no leading/trailing `_`) so a
     * hand-typed device ID here can't silently diverge from what HA subscribes to.
     */
    suspend fun setDeviceId(value: String) = set(KEY_DEVICE_ID, value.slugify())

    suspend fun setTopicPrefix(value: String) = set(KEY_TOPIC_PREFIX, value.trim())

    /** Stored as "true"/"false" to keep every key string-typed (matches the legacy format). */
    suspend fun setUseTls(value: Boolean) = set(KEY_USE_TLS, value.toString())

    /**
     * Apply broker settings pushed by HA's ADB provisioning. Writes only the fields that were
     * actually provided (non-null), in a single edit, so absent extras leave existing values
     * untouched. See [ProvisioningConfig].
     */
    suspend fun applyProvisioning(config: ProvisioningConfig) {
        context.settingsDataStore.edit { prefs ->
            config.host?.let { prefs[KEY_HOST] = it }
            config.port?.let { prefs[KEY_PORT] = it.toString() }
            config.username?.let { prefs[KEY_USERNAME] = it }
            config.password?.let { prefs[KEY_PASSWORD] = it }
            config.deviceId?.let { prefs[KEY_DEVICE_ID] = it }
            config.topicPrefix?.let { prefs[KEY_TOPIC_PREFIX] = it }
            config.useTls?.let { prefs[KEY_USE_TLS] = it.toString() }
        }
    }

    private suspend fun set(key: Preferences.Key<String>, value: String) {
        context.settingsDataStore.edit { it[key] = value }
    }

    companion object {
        private val KEY_HOST         = stringPreferencesKey("broker_host")
        private val KEY_PORT         = stringPreferencesKey("broker_port")
        private val KEY_USERNAME     = stringPreferencesKey("broker_username")
        private val KEY_PASSWORD     = stringPreferencesKey("broker_password")
        private val KEY_DEVICE_ID    = stringPreferencesKey("device_id")
        private val KEY_TOPIC_PREFIX = stringPreferencesKey("topic_prefix")
        private val KEY_USE_TLS      = stringPreferencesKey("use_tls")

        private const val DEFAULT_HOST         = ""
        private const val DEFAULT_PORT         = 1883
        private const val DEFAULT_USERNAME     = ""
        private const val DEFAULT_PASSWORD     = ""
        private const val DEFAULT_DEVICE_ID    = "fire_tv"
        private const val DEFAULT_TOPIC_PREFIX = "fire2mqtt"
        private const val DEFAULT_USE_TLS      = "false"
    }
}

internal fun String.slugify(): String =
    lowercase().replace(Regex("[^a-z0-9]+"), "_").trim('_')
