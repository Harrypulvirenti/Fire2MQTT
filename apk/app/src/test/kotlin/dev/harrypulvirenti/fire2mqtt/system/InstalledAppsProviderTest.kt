package dev.harrypulvirenti.fire2mqtt.system

import android.content.Context
import android.content.Intent
import android.content.pm.ActivityInfo
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
import io.mockk.every
import io.mockk.mockk
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Test

class InstalledAppsProviderTest {

    private fun resolve(pkg: String): ResolveInfo =
        mockk<ResolveInfo>(relaxed = true).apply {
            activityInfo = mockk<ActivityInfo>(relaxed = true).apply { packageName = pkg }
        }

    private fun provider(vararg resolved: ResolveInfo): InstalledAppsProvider {
        val pm = mockk<PackageManager>(relaxed = true)
        val context = mockk<Context>(relaxed = true)
        every { context.packageManager } returns pm
        every { context.packageName } returns "dev.harrypulvirenti.fire2mqtt"
        // Both category queries return the same list; the provider must union + dedup.
        every { pm.queryIntentActivities(any(), 0) } returns resolved.toList()
        return InstalledAppsProvider(context)
    }

    @Test fun `dedups packages and drops Fire2MQTT's own package`() {
        val result = provider(
            resolve("com.netflix.ninja"),
            resolve("com.netflix.ninja"),                 // duplicate (e.g. across categories)
            resolve("dev.harrypulvirenti.fire2mqtt"),     // our own app — excluded
            resolve("org.jellyfin.androidtv"),
        ).launchablePackages()

        assertEquals(listOf("com.netflix.ninja", "org.jellyfin.androidtv"), result)
        assertFalse("dev.harrypulvirenti.fire2mqtt" in result)
    }

    @Test fun `no launchable apps yields an empty list`() {
        assertEquals(emptyList<String>(), provider().launchablePackages())
    }
}
