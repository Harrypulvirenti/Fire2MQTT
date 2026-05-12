# Installing the Fire2MQTT APK

## Requirements

- Fire TV Stick with Fire OS 7+ (Android 7.1+)
- ADB enabled on the Fire Stick (Settings → My Fire TV → Developer Options → ADB Debugging ON)
- ADB installed on your computer

## Steps

### 1. Build the APK

Open the `apk/` folder in Android Studio and run **Build → Build Bundle(s) / APK(s) → Build APK(s)**.
The debug APK is at `apk/app/build/outputs/apk/debug/app-debug.apk`.

### 2. Sideload via ADB

```bash
# Connect over your local network (replace with your Fire Stick IP)
adb connect 192.168.1.50

# Install
adb install -r apk/app/build/outputs/apk/debug/app-debug.apk
```

### 3. Launch the app

Find **Fire2MQTT** in your app drawer or run:
```bash
adb shell am start -n dev.harrypulvirenti.fire2mqtt/.ui.SettingsActivity
```

### 4. Configure the MQTT broker

In the Fire2MQTT settings screen:
- **Broker Host** — IP or hostname of your MQTT broker (e.g. `192.168.1.10`)
- **Broker Port** — default `1883`
- **Username / Password** — if your broker requires auth
- **Device ID** — slug that appears in MQTT topics (e.g. `living_room_fire_tv`)
- **Topic Prefix** — default `fire2mqtt`

### 5. Grant required permissions

The app will open the **Permissions** screen automatically. You must grant three permissions:

#### a) Usage Access (required for foreground app detection)
Tap **Grant Usage Access** → find **Fire2MQTT** → enable the toggle.

> Without this, the `state/app` topic will not publish.

#### b) Notification Listener Access (required for MediaSession)
Tap **Grant Notification Access** → find **Fire2MQTT** → enable.

> Without this, the `state/playback` topic will not publish (no media metadata).

#### c) Accessibility Service (required for key injection — HOME, BACK, DPAD, media keys)
Tap **Grant Accessibility Access** → find **Fire2MQTT** → enable.

> Without this, `cmd/key` and `cmd/media` commands will be silently dropped.
> App launching (`cmd/launch`) works without this permission.

### 6. Start the service

Tap **Start Service** in the app, or reboot the Fire Stick (the service auto-starts via `BOOT_COMPLETED`).

### 7. Verify

On your broker, subscribe to all topics:
```bash
mosquitto_sub -h 192.168.1.10 -t "fire2mqtt/#" -v
```

You should see `fire2mqtt/<device_id>/status: online` and `state/device` within a few seconds.

---

## Updating

Re-install with `adb install -r ...`. The service auto-restarts via `ACTION_MY_PACKAGE_REPLACED`.

## Uninstalling

```bash
adb uninstall dev.harrypulvirenti.fire2mqtt
```

The broker will receive `fire2mqtt/<device_id>/status: offline` via LWT.
