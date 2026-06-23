package dev.harrypulvirenti.fire2mqtt.ui

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningExtras
import dev.harrypulvirenti.fire2mqtt.ui.components.TvDesignScale
import dev.harrypulvirenti.fire2mqtt.ui.theme.Fire2MqttTheme
import org.koin.androidx.viewmodel.ext.android.viewModel

/**
 * Single Compose entry point — the merged setup + permissions dashboard.
 * Replaces the old SettingsActivity / PermissionsActivity pair.
 *
 * Also consumes the broker config that HA's ADB provisioning passes as launch-intent
 * extras (see [ProvisioningExtras]), so a provisioned device opens pre-filled.
 */
class MainActivity : ComponentActivity() {

    // Activity-scoped so onCreate/onNewIntent and the Compose tree share one instance.
    private val vm: SetupViewModel by viewModel()

    override fun onCreate(savedInstanceState: Bundle?) {
        // Must be installed before super.onCreate(). Shows the branded launch screen
        // (Theme.Fire2MQTT.Splash) until the ViewModel's first load finishes — see
        // setKeepOnScreenCondition below — so the cold start never shows a bare black gap.
        val splash = installSplashScreen()
        super.onCreate(savedInstanceState)
        // Apply provisioning extras only on a genuine fresh start; a non-null
        // savedInstanceState means a config-change recreate, where we already consumed them.
        if (savedInstanceState == null) applyProvisioningExtras(intent)
        // Draw edge-to-edge so the dashboard fills the whole panel (no system-bar inset).
        enableEdgeToEdge()
        setContent {
            Fire2MqttTheme {
                val state by vm.state.collectAsStateWithLifecycle()

                // Hold the splash until the off-thread initial load populates the state.
                splash.setKeepOnScreenCondition { !state.ready }

                // Returning to the screen (e.g. after the one-time ADB grant) re-checks
                // permission state and self-enables access when WRITE_SECURE_SETTINGS is held.
                LifecycleEventEffect(Lifecycle.Event.ON_RESUME) { vm.refreshPermissions() }

                TvDesignScale {
                    SetupDashboard(
                        state = state,
                        onHostChange = vm::updateHost,
                        onPortChange = vm::updatePort,
                        onUsernameChange = vm::updateUsername,
                        onPasswordChange = vm::updatePassword,
                        onUseTlsChange = vm::updateUseTls,
                        onDeviceIdChange = vm::updateDeviceId,
                        onTopicPrefixChange = vm::updateTopicPrefix,
                        onTestConnection = vm::testConnection,
                        onStartService = vm::startService,
                        onStopService = vm::stopService,
                        onRecheck = vm::refreshPermissions,
                    )
                }
            }
        }
    }

    // singleTop: a re-launch (e.g. re-provisioning) delivers fresh extras here, not a new instance.
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        applyProvisioningExtras(intent)
    }

    private fun applyProvisioningExtras(intent: Intent?) {
        ProvisioningExtras.parse(intent)?.let(vm::applyProvisioning)
    }
}
