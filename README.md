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
UsageStatsManager    ─── state/app ────────────────────────▶  sensor: current_app
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
| `media_player.<device>` | Media Player | Playback state, title, position, volume control |
| `sensor.<device>_current_app` | Sensor | Foreground app friendly name |
| `sensor.<device>_current_app_package` | Sensor | Foreground app package name |
| `sensor.<device>_media_title` | Sensor | Now playing title |
| `sensor.<device>_media_artist` | Sensor | Now playing artist |
| `sensor.<device>_volume_level` | Sensor | Volume 0–100% |
| `binary_sensor.<device>_screen` | Binary Sensor | Screen on/off |
| `button.<device>_launch_<app>` | Button | Launch a curated streaming app |
| `remote.<device>` | Remote | Send key events (HOME, BACK, DPAD, etc.) |

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
5. Enter your device name and device ID (must match the APK setting)

> **Prerequisite:** The MQTT integration must be configured first — Fire2MQTT uses your existing broker.

### Part 2 — Install the APK on your Fire Stick

See [docs/installing-apk.md](docs/installing-apk.md) for step-by-step instructions.
Short version:
```bash
adb connect 192.168.1.50
adb install -r apk/app/build/outputs/apk/debug/app-debug.apk
```

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
