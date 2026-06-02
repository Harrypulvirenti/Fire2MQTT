package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

class AppLauncherTest {

    private lateinit var context: Context
    private lateinit var packageManager: PackageManager
    private lateinit var launcher: AppLauncher

    @BeforeEach
    fun setUp() {
        packageManager = mockk(relaxed = true)
        context = mockk(relaxed = true)
        every { context.packageManager } returns packageManager
        launcher = AppLauncher(context)
    }

    @Test fun `known package launches activity and returns true`() {
        val intent = mockk<Intent>(relaxed = true)
        every { packageManager.getLaunchIntentForPackage("com.example.app") } returns intent

        val result = launcher.launch("com.example.app")

        assertTrue(result)
        verify { intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }
        verify { context.startActivity(intent) }
    }

    @Test fun `unknown package does not start activity and returns false`() {
        every { packageManager.getLaunchIntentForPackage("com.unknown") } returns null

        val result = launcher.launch("com.unknown")

        assertFalse(result)
        verify(exactly = 0) { context.startActivity(any()) }
    }
}
