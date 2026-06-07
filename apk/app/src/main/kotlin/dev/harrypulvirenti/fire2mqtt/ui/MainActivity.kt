package dev.harrypulvirenti.fire2mqtt.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.core.view.WindowCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.harrypulvirenti.fire2mqtt.ui.components.TvDesignScale
import dev.harrypulvirenti.fire2mqtt.ui.theme.Fire2MqttTheme
import org.koin.androidx.compose.koinViewModel

/**
 * Single Compose entry point — the merged setup + permissions dashboard.
 * Replaces the old SettingsActivity / PermissionsActivity pair.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        // Must be installed before super.onCreate(). Shows the branded launch screen
        // (Theme.Fire2MQTT.Splash) until the ViewModel's first load finishes — see
        // setKeepOnScreenCondition below — so the cold start never shows a bare black gap.
        val splash = installSplashScreen()
        super.onCreate(savedInstanceState)
        // Draw edge-to-edge so the dashboard fills the whole panel (no system-bar inset).
        WindowCompat.setDecorFitsSystemWindows(window, false)
        setContent {
            Fire2MqttTheme {
                val vm: SetupViewModel = koinViewModel()
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
}
