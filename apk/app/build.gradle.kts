plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.serialization)
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
        versionCode = 1
        versionName = "0.1.0"
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
        viewBinding = true
    }

    testOptions {
        unitTests.all { it.useJUnitPlatform() }
    }
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

    // AndroidX
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.preference.ktx)
    implementation(libs.androidx.lifecycle.service)

    // Testing
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.junit.jupiter.params)
    testImplementation(libs.mockk)
    testImplementation(libs.kotlinx.coroutines.test)
    testRuntimeOnly("org.junit.platform:junit-platform-launcher:6.1.0")
}
