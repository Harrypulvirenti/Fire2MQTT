package dev.harrypulvirenti.fire2mqtt.system

import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import io.mockk.*
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ForegroundAppWatcherTest {

    private lateinit var packageManager: PackageManager
    private lateinit var context: Context

    @BeforeEach
    fun setUp() {
        packageManager = mockk()
        context = mockk()
        every { context.packageManager } returns packageManager
    }

    @AfterEach
    fun tearDown() = unmockkAll()

    private fun watcherFor(vararg packages: String): ForegroundAppWatcher =
        ForegroundAppWatcher(context, source = flowOf(*packages))

    private fun stubAppLabel(pkg: String, label: String) {
        val appInfo = mockk<ApplicationInfo>()
        every { packageManager.getApplicationInfo(pkg, 0) } returns appInfo
        every { packageManager.getApplicationLabel(appInfo) } returns label
    }

    @Test
    fun `new foreground app emits ForegroundAppEvent with resolved name`() = runTest {
        stubAppLabel("com.example.app", "Example App")

        val events = watcherFor("com.example.app").foregroundAppFlow().take(1).toList()

        assertEquals(1, events.size)
        assertEquals("com.example.app", events[0].packageName)
        assertEquals("Example App", events[0].appName)
    }

    @Test
    fun `consecutive duplicate package does not emit again`() = runTest {
        stubAppLabel("com.example.app", "Example App")
        stubAppLabel("com.other.app", "Other App")

        val events = watcherFor("com.example.app", "com.example.app", "com.other.app")
            .foregroundAppFlow()
            .toList()

        assertEquals(2, events.size)
        assertEquals("com.example.app", events[0].packageName)
        assertEquals("com.other.app", events[1].packageName)
    }

    @Test
    fun `getApplicationLabel failure falls back to package name`() = runTest {
        every { packageManager.getApplicationInfo("com.no.label", 0) } throws
            PackageManager.NameNotFoundException()

        val events = watcherFor("com.no.label").foregroundAppFlow().take(1).toList()

        assertEquals(1, events.size)
        assertEquals("com.no.label", events[0].packageName)
        assertEquals("com.no.label", events[0].appName)
    }

    @Test
    fun `launcher echo right after an app takes focus is dropped`() = runTest {
        // Google TV fires launcherx just after the app it opened (finding 6 in #41).
        stubAppLabel("com.google.android.youtube.tv", "YouTube")
        val times = ArrayDeque(listOf(0L, 300L))
        val watcher = ForegroundAppWatcher(
            context,
            source = flowOf("com.google.android.youtube.tv", "com.google.android.apps.tv.launcherx"),
            nowMs = { times.removeFirst() },
        )

        val events = watcher.foregroundAppFlow().toList()

        assertEquals(listOf("com.google.android.youtube.tv"), events.map { it.packageName })
    }

    @Test
    fun `returning to the launcher after the window is reported`() = runTest {
        stubAppLabel("com.google.android.youtube.tv", "YouTube")
        stubAppLabel("com.google.android.apps.tv.launcherx", "Google TV")
        val times = ArrayDeque(listOf(0L, LAUNCHER_FLICKER_WINDOW_MS + 1))
        val watcher = ForegroundAppWatcher(
            context,
            source = flowOf("com.google.android.youtube.tv", "com.google.android.apps.tv.launcherx"),
            nowMs = { times.removeFirst() },
        )

        val events = watcher.foregroundAppFlow().toList()

        assertEquals(
            listOf("com.google.android.youtube.tv", "com.google.android.apps.tv.launcherx"),
            events.map { it.packageName },
        )
    }

    @Test
    fun `repeat events from the same app do not reopen the flicker window`() = runTest {
        // A real HOME press shortly after an in-app window change must still register.
        stubAppLabel("com.example.app", "Example App")
        stubAppLabel("com.amazon.tv.launcher", "Home")
        val times = ArrayDeque(listOf(0L, 5_000L, 5_300L))
        val watcher = ForegroundAppWatcher(
            context,
            source = flowOf("com.example.app", "com.example.app", "com.amazon.tv.launcher"),
            nowMs = { times.removeFirst() },
        )

        val events = watcher.foregroundAppFlow().toList()

        assertEquals(listOf("com.example.app", "com.amazon.tv.launcher"), events.map { it.packageName })
    }
}
