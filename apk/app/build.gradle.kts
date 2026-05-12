plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "dev.harrypulvirenti.fire2mqtt"
    compileSdk = 34

    defaultConfig {
        applicationId = "dev.harrypulvirenti.fire2mqtt"
        minSdk = 25         // Fire OS 7 (Android 7.1)
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    // HiveMQ MQTT 5 Kotlin client — coroutine-native, better lifecycle than paho
    implementation("com.hivemq:hivemq-mqtt-client-kotlin-coroutines:1.3.3")

    // Kotlin serialization for JSON payloads
    implementation(libs.kotlinx.serialization.json)

    // Coroutines
    implementation(libs.kotlinx.coroutines.android)

    // AndroidX
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.preference.ktx)
    implementation(libs.androidx.lifecycle.service)
}
