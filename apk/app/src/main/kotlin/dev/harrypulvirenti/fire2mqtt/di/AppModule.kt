package dev.harrypulvirenti.fire2mqtt.di

import android.content.ComponentName
import android.content.Context
import dev.harrypulvirenti.fire2mqtt.commands.Fire2MqttAccessibilityService
import dev.harrypulvirenti.fire2mqtt.commands.MediaTransport
import dev.harrypulvirenti.fire2mqtt.media.MediaNotificationListener
import dev.harrypulvirenti.fire2mqtt.media.MediaSessionWatcher
import dev.harrypulvirenti.fire2mqtt.system.ForegroundAppWatcher
import dev.harrypulvirenti.fire2mqtt.system.UsageStatsForegroundSource
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.merge
import org.koin.core.annotation.ComponentScan
import org.koin.core.annotation.Factory
import org.koin.core.annotation.Module
import org.koin.core.annotation.Single

/**
 * Koin object graph. Most definitions come from class-level annotations
 * (@Single/@Factory/@KoinViewModel) discovered by @ComponentScan. The factories
 * below are declared explicitly because their constructors aren't purely
 * graph-resolvable — annotation generation can't honor Kotlin default values or build
 * a non-graph type like ComponentName.
 */
@Module
@ComponentScan("dev.harrypulvirenti.fire2mqtt")
class AppModule {

    /**
     * Foreground app from the accessibility service, plus the usage-stats fallback for devices
     * that refuse to bind it (Fire OS 6.7). The fallback idles while the service is bound.
     */
    @Factory
    fun foregroundAppWatcher(context: Context): ForegroundAppWatcher =
        ForegroundAppWatcher(
            context,
            source = merge(
                Fire2MqttAccessibilityService.foregroundPackages,
                UsageStatsForegroundSource(context).packages(),
            ),
        )

    /** ComponentName isn't a graph type — build it from the app context. */
    @Factory
    fun mediaSessionWatcher(context: Context): MediaSessionWatcher =
        MediaSessionWatcher(
            context,
            ComponentName(context, MediaNotificationListener::class.java),
        )

    /** Same ComponentName requirement as MediaSessionWatcher (session access goes through it). */
    @Factory
    fun mediaTransport(context: Context): MediaTransport =
        MediaTransport(
            context,
            ComponentName(context, MediaNotificationListener::class.java),
        )

    /** Background dispatcher for ViewModels; tests construct directly with a test dispatcher. */
    @Single
    fun ioDispatcher(): CoroutineDispatcher = Dispatchers.IO
}
