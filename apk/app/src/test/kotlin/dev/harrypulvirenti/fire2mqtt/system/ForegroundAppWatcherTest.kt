package dev.harrypulvirenti.fire2mqtt.system

import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import io.mockk.*
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ForegroundAppWatcherTest {

    private lateinit var usageStats: UsageStatsManager
    private lateinit var packageManager: PackageManager
    private lateinit var watcher: ForegroundAppWatcher

    @BeforeEach
    fun setUp() {
        // UsageEvents.Event() constructor throws "Stub!" on JVM — mock it away.
        mockkConstructor(UsageEvents.Event::class)

        usageStats = mockk()
        packageManager = mockk()
        val context = mockk<Context>()
        every { context.getSystemService(UsageStatsManager::class.java) } returns usageStats
        every { context.packageManager } returns packageManager
        watcher = ForegroundAppWatcher(context)
    }

    @AfterEach
    fun tearDown() = unmockkAll()

    private fun stubForegroundPackage(pkg: String?) {
        val queryResult = mockk<UsageEvents>()
        every { usageStats.queryEvents(any(), any()) } returns queryResult

        if (pkg == null) {
            every { queryResult.hasNextEvent() } returns false
        } else {
            // Production code does: val event = UsageEvents.Event(); getNextEvent(event);
            // mockkConstructor intercepts the constructor so anyConstructed<UsageEvents.Event>()
            // stubs the properties read afterwards.
            every { anyConstructed<UsageEvents.Event>().eventType } returns UsageEvents.Event.ACTIVITY_RESUMED
            every { anyConstructed<UsageEvents.Event>().packageName } returns pkg
            every { queryResult.hasNextEvent() } returnsMany listOf(true, false)
            every { queryResult.getNextEvent(any()) } returns true
        }
    }

    private fun stubAppLabel(pkg: String, label: String) {
        val appInfo = mockk<ApplicationInfo>()
        every { packageManager.getApplicationInfo(pkg, 0) } returns appInfo
        every { packageManager.getApplicationLabel(appInfo) } returns label
    }

    @Test
    fun `new foreground app emits ForegroundAppEvent with resolved name`() = runTest {
        stubForegroundPackage("com.example.app")
        stubAppLabel("com.example.app", "Example App")

        val events = watcher.foregroundAppFlow().take(1).toList()

        assertEquals(1, events.size)
        assertEquals("com.example.app", events[0].packageName)
        assertEquals("Example App", events[0].appName)
    }

    @Test
    fun `same package repeated does not emit again`() = runTest {
        stubForegroundPackage("com.example.app")
        stubAppLabel("com.example.app", "Example App")

        // First emission changes lastPackage to "com.example.app", subsequent polls with the
        // same package must not emit.
        val events = watcher.foregroundAppFlow().take(1).toList()

        assertEquals(1, events.size)
        assertEquals("com.example.app", events[0].packageName)
    }

    @Test
    fun `getApplicationLabel failure falls back to package name`() = runTest {
        stubForegroundPackage("com.no.label")
        every { packageManager.getApplicationInfo("com.no.label", 0) } throws PackageManager.NameNotFoundException()

        val events = watcher.foregroundAppFlow().take(1).toList()

        assertEquals(1, events.size)
        assertEquals("com.no.label", events[0].packageName)
        assertEquals("com.no.label", events[0].appName)
    }

    @Test
    fun `queryEvents failure does not emit and does not crash`() = runTest {
        every { usageStats.queryEvents(any(), any()) } throws SecurityException("no permission")

        val collected = mutableListOf<ForegroundAppEvent>()
        val job = launch {
            watcher.foregroundAppFlow().collect { collected.add(it) }
        }
        advanceTimeBy(3_000L)
        job.cancel()

        assertEquals(0, collected.size)
    }
}
