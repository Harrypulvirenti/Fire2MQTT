# Installing the Fire2MQTT APK

## Requirements

- Fire TV Stick with Fire OS 7+ (Android 7.1+)
- ADB enabled on the Fire Stick (Settings → My Fire TV → Developer Options → ADB Debugging ON)
- ADB installed on your computer (only for the manual path below)

## The easy path: let Home Assistant do it

If you've installed the **Fire2MQTT Home Assistant integration**, it can install the APK and grant the
one permission Fire OS hides — over ADB — during setup:

1. On the Fire TV: **Settings → My Fire TV → Developer Options → ADB Debugging → ON**.
2. In Home Assistant, add the **Fire2MQTT** integration. After the device/MQTT step, choose
   **Install & set up over ADB** and enter the Fire TV's IP.
3. The **first** time, an authorization dialog appears on the TV — **accept it**, then submit the form
   again. Home Assistant installs the APK, grants `WRITE_SECURE_SETTINGS`, and launches the app, which
   then enables its own accessibility + notification-listener access.

That's it — no manual ADB commands, no settings hunting. The rest of this doc is the manual path.

## Manual path

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

### 5. Grant permissions (one ADB command)

Fire OS does **not** let a sideloaded app enable Usage Access / Notification Listener / Accessibility from
any in-app UI — the settings screens don't open and the app isn't listed. Instead, Fire2MQTT enables its
own permissions once it has **`WRITE_SECURE_SETTINGS`**, which you grant with a single ADB command:

```bash
adb connect <fire-tv-ip>:5555
adb shell pm grant dev.harrypulvirenti.fire2mqtt android.permission.WRITE_SECURE_SETTINGS
```

The app's **Permissions** screen shows this exact command (with your device's IP). After you run it, return
to the app and tap **Enable permissions** (or just restart the app) — it writes the secure settings to turn
on:

- **Accessibility service** — key injection (`cmd/key`, `cmd/media`) **and** foreground-app detection
  (`state/app`). App launching (`cmd/launch`) works without it.
- **Notification-listener access** — MediaSession metadata (`state/playback`).

> Foreground-app detection runs on the accessibility service now; there is no separate Usage Access
> permission anymore.
>
> A few Fire OS builds have `WRITE_SECURE_SETTINGS` removed by Amazon. If the grant doesn't stick, the app
> can't self-enable and these features stay off.

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
