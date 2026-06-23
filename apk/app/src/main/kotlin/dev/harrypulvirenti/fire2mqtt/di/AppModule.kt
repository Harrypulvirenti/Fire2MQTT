package dev.harrypulvirenti.fire2mqtt.di

import android.content.ComponentName
import android.content.Context
import dev.harrypulvirenti.fire2mqtt.media.MediaNotificationListener
import dev.harrypulvirenti.fire2mqtt.media.MediaSessionWatcher
import dev.harrypulvirenti.fire2mqtt.system.ForegroundAppWatcher
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import org.koin.core.annotation.ComponentScan
import org.koin.core.annotation.Factory
import org.koin.core.annotation.Module
import org.koin.core.annotation.Single

/**
 * Koin object graph. Most definitions come from class-level annotations
 * (@Single/@Factory/@KoinViewModel) discovered by @ComponentScan. The two factories
 * below are declared explicitly because their constructors aren't purely
 * graph-resolvable — annotation generation can't honor Kotlin default values or build
 * a non-graph type like ComponentName.
 */
@Module
@ComponentScan("dev.harrypulvirenti.fire2mqtt")
class AppModule {

    /** Keeps ForegroundAppWatcher's default static `source` (a defaulted ctor arg). */
    @Factory
    fun foregroundAppWatcher(context: Context): ForegroundAppWatcher =
        ForegroundAppWatcher(context)

    /** ComponentName isn't a graph type — build it from the app context. */
    @Factory
    fun mediaSessionWatcher(context: Context): MediaSessionWatcher =
        MediaSessionWatcher(
            context,
            ComponentName(context, MediaNotificationListener::class.java),
        )

    /** Background dispatcher for ViewModels; tests construct directly with a test dispatcher. */
    @Single
    fun ioDispatcher(): CoroutineDispatcher = Dispatchers.IO
}
