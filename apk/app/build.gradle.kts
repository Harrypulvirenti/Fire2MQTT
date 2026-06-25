import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
}

kotlin {
    jvmToolchain(17)
}

// Release signing comes from env vars (CI secrets) or a gitignored
// keystore.properties (local). A stable key is mandatory: Android rejects an
// update whose signature differs from the installed one, so debug signing (a
// per-machine/ephemeral key) made every release uninstallable-over-the-top.
// When no signing material is present (e.g. a contributor build), the release
// build falls back to debug signing so `assembleRelease` still works locally.
val keystorePropsFile = rootProject.file("keystore.properties")
val keystoreProps = Properties().apply {
    if (keystorePropsFile.exists()) keystorePropsFile.inputStream().use { load(it) }
}
fun signingProp(prop: String, env: String): String? =
    System.getenv(env) ?: keystoreProps.getProperty(prop)
val releaseStoreFile: String? = signingProp("storeFile", "KEYSTORE_FILE")
val hasReleaseSigning: Boolean = releaseStoreFile != null && file(releaseStoreFile).exists()

android {
    namespace = "dev.harrypulvirenti.fire2mqtt"
    compileSdk = 37

    defaultConfig {
        applicationId = "dev.harrypulvirenti.fire2mqtt"
        minSdk = 25         // Fire OS 7 (Android 7.1)
        // compileSdk is ahead of targetSdk on purpose: core/material 1.19/1.14 need API 37
        // to compile, but we don't opt into API-37 runtime behavior changes on Fire OS yet.
        targetSdk = 36
        // Keep in lockstep with custom_components/fire2mqtt/manifest.json on every release —
        // HA's update entity compares this versionName against the integration version.
        versionCode = 7
        versionName = "0.4.3"
    }

    signingConfigs {
        if (hasReleaseSigning) {
            create("release") {
                storeFile = file(releaseStoreFile!!)
                storePassword = signingProp("storePassword", "KEYSTORE_PASSWORD")
                keyAlias = signingProp("keyAlias", "KEY_ALIAS")
                keyPassword = signingProp("keyPassword", "KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            // R8 is off: proguard-rules.pro is empty and the serialization/Koin/HiveMQ
            // graph is reflection-heavy, so a shrunk build is untested and would likely
            // crash. Keep the release APK behaviourally identical to the (working) debug
            // build — the only intended differences are the stable signature + no debuggable.
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName(if (hasReleaseSigning) "release" else "debug")
        }
    }

    packaging {
        resources {
            excludes += setOf(
                "META-INF/INDEX.LIST",
                "META-INF/io.netty.versions.properties",
            )
        }
    }

    buildFeatures {
        compose = true
    }

    testOptions {
        unitTests.all { it.useJUnitPlatform() }
        // Let android.jar stubs (e.g. constructing an Intent in InstalledAppsProvider)
        // return defaults instead of throwing, so pure-JVM unit tests can exercise them.
        unitTests.isReturnDefaultValues = true
    }
}

// Verify the Koin graph at compile time (missing definitions fail the build).
ksp {
    arg("KOIN_CONFIG_CHECK", "true")
    arg("KOIN_DEFAULT_MODULE", "true")
}

dependencies {
    // HiveMQ MQTT 5 Kotlin client — coroutine-native, better lifecycle than paho
    implementation("com.hivemq:hivemq-mqtt-client:1.3.14")

    // Kotlin serialization for JSON payloads
    implementation(libs.kotlinx.serialization.json)

    // Coroutines
    implementation(libs.kotlinx.coroutines.android)

    // Logging
    implementation(libs.kermit)

    // Dependency injection — Koin (+ annotations via KSP)
    implementation(platform(libs.koin.bom))
    implementation(libs.koin.android)
    implementation(libs.koin.androidx.compose)
    implementation(libs.koin.annotations)
    ksp(libs.koin.ksp.compiler)

    // AndroidX
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.core.splashscreen)
    implementation(libs.androidx.datastore.preferences)
    implementation(libs.androidx.lifecycle.service)

    // Jetpack Compose (BOM-aligned) — setup dashboard UI
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.foundation)
    implementation(libs.compose.material3)
    // icons-core only (Check, Notifications); the one extended icon we need
    // (Accessibility) is inlined in ui/components — extended is ~12MB of methods.
    implementation(libs.compose.material.icons.core)
    implementation(libs.compose.ui.tooling.preview)
    debugImplementation(libs.compose.ui.tooling)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)

    // Testing
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.junit.jupiter.params)
    testImplementation(libs.mockk)
    testImplementation(libs.kotlinx.coroutines.test)
    testRuntimeOnly("org.junit.platform:junit-platform-launcher:6.1.0")
}
