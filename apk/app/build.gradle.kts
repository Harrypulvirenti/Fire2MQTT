plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
}

kotlin {
    jvmToolchain(17)
}

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
        versionCode = 2
        versionName = "0.2.0-beta5"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
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
