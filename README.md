# Fire2MQTT

**Real-time Fire TV Stick integration for Home Assistant via MQTT.**

No more polling ADB every 5 seconds. A sideloaded APK on your Fire Stick publishes
state changes via MQTT the moment they happen — a Home Assistant integration
subscribes and exposes proper entities.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

---

## Architecture

```
Fire TV Stick (APK)                MQTT broker               Home Assistant
─────────────────────              ──────────                ──────────────
MediaSessionManager  ─── state/playback ──────────────────▶  media_player
AccessibilityService ─── state/app ────────────────────────▶  sensor: current_app
AudioManager         ─── state/volume ─────────────────────▶  sensor: volume
ScreenReceiver       ─── state/screen ─────────────────────▶  binary_sensor: screen
                     ◀── cmd/launch ─────────────────────────  button: launch app
                     ◀── cmd/key ───────────────────────────   remote
                     ◀── cmd/media ─────────────────────────   media_player services
```

State is **push-only** — the HA integration never polls. Changes arrive in <100ms.

---

## What you get

### Entities per device
| Entity | Type | Description |
|--------|------|-------------|
| `media_player.<device>` | Media Player | Playback state (incl. off/standby), title, position, source select, volume, turn on/off |
| `sensor.<device>_current_app` | Sensor | Foreground app friendly name |
| `sensor.<device>_current_app_package` | Sensor | Foreground app package name (diagnostic, disabled by default) |
| `sensor.<device>_media_title` | Sensor | Now playing title |
| `sensor.<device>_media_artist` | Sensor | Now playing artist |
| `sensor.<device>_volume_level` | Sensor | Volume 0–100% |
| `sensor.<device>_ip_address` | Sensor | Device IP (diagnostic, disabled by default) |
| `binary_sensor.<device>_screen` | Binary Sensor | Screen on/off |
| `binary_sensor.<device>_connectivity` | Binary Sensor | APK online/offline (stays available while offline) |
| `button.<device>_launch_<app>` | Button | Launch a curated streaming app |
| `remote.<device>` | Remote | Send key events (HOME, BACK, DPAD, etc.), turn on/off |

Add one config entry per Fire Stick — every entry gets its own device, entities,
and MQTT topic namespace (`<prefix>/<device_id>/…`), so multiple sticks coexist
cleanly on one broker.

### Curated app state detection (v1)
Out of the box, correct `playing` / `paused` / `idle` states for:
- Crunchyroll · Netflix · Prime Video · YouTube · Disney+
- Jellyfin · Plex · Emby · Spotify · Twitch · Max (HBO) · Apple TV · Kodi

---

## Installation

### Part 1 — Install the HA integration (HACS)

1. In HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/Harrypulvirenti/Fire2MQTT` (category: Integration)
2. Install **Fire2MQTT**
3. Restart Home Assistant
4. Settings → Devices & Services → Add Integration → search **Fire2MQTT**
5. Choose how to install the app on the Fire TV — **automatically over ADB** (also pushes
   your broker settings to the app, so you never type them on the TV) or **manually** —
   then enter the device name and device ID.

> **Requirements:**
> - An **MQTT broker** such as the [Mosquitto broker add-on](https://github.com/home-assistant/addons/tree/master/mosquitto). Fire2MQTT does not run its own broker.
> - Home Assistant's **MQTT integration** configured against that broker (the HA side rides on it).
>
> **Where credentials live:** the HA side authenticates through HA's MQTT integration; the
> Fire TV app connects to the broker directly, so it needs an **existing broker
> username/password**. Home Assistant cannot create accounts on your broker. With the ADB
> install option these are entered once in HA and pushed to the app.

### Part 2 — Install the APK on your Fire Stick

Prefer the **Install automatically over ADB** option in the config flow above. To sideload
by hand instead, see [docs/installing-apk.md](docs/installing-apk.md). Short version:
```bash
adb connect 192.168.1.50
adb install -r apk/app/build/outputs/apk/debug/app-debug.apk
```
Then open the app on the Fire TV and enter your broker address, an existing broker
username/password (toggle **TLS** for `mqtts`), and a device ID matching the one in HA.

---

## Example automations

Ready-to-paste automations are in `examples/automations/`:
- `dim_lights_on_playback.yaml` — dim lights when playing, restore when paused
- `pause_on_doorbell.yaml` — pause when doorbell rings, auto-resume after 60s
- `pause_when_room_empty.yaml` — pause when room is empty, resume on return
- `turn_off_when_idle.yaml` — sleep after 15 min on home screen
- `watching_tv_scene.yaml` — trigger a scene when streaming starts

---

## Contributing a new app

See [docs/adding-apps.md](docs/adding-apps.md). The curated rule database is designed
for future upstream contribution to [python-androidtv](https://github.com/JeffLIrion/python-androidtv).

---

## Development

```bash
# Simulate the APK (no physical device needed)
pip install paho-mqtt
python3 tools/mqtt_simulator.py --broker 192.168.1.10 --device-id living_room_fire_tv

# Run tests
pip install pytest pytest-homeassistant-custom-component
pytest tests/
```

---

## License

MIT © [Harry Pulvirenti](https://github.com/harrypulvirenti)
