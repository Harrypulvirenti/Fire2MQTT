# Fire2MQTT — MQTT Schema v2

This document is the canonical contract between the Fire TV APK and the Home Assistant integration.
**Breaking changes bump `schema_version` in the `state/device` payload and require a coordinated APK + integration release.**

`schema_version` 2 added the retained `state/apps` topic (installed-app inventory). It is
additive — an older integration ignores it — but the version bump nudges users to update both halves.

## Topic structure

```
fire2mqtt/<device_id>/<direction>/<subject>
```

- `<device_id>` — slug set in the APK settings and the HA config entry (e.g. `living_room_fire_tv`)
- Topic prefix defaults to `fire2mqtt` but is configurable in both APK and HA

---

## State topics (APK → HA, all retained)

### `fire2mqtt/<device_id>/status`
LWT (Last Will and Testament) — published by broker when APK disconnects ungracefully.

| Payload | Meaning |
|---------|---------|
| `online` | APK connected, publishing |
| `offline` | APK disconnected or broker LWT fired |

---

### `fire2mqtt/<device_id>/state/device`
Published once on connect. Contains static device metadata.

```json
{
  "model": "Fire TV Stick 4K Max",
  "fire_os": "8.2.2.1",
  "ip": "192.168.1.50",
  "mac": "a4:c3:f0:xx:xx:xx",
  "schema_version": 2,
  "app_version": "0.2.0-beta5",
  "app_version_code": 2
}
```

`app_version` / `app_version_code` are the APK's own `versionName` / `versionCode`; HA's update
entity compares them against the integration's release version to offer an ADB-pushed update.

---

### `fire2mqtt/<device_id>/state/playback`
Published on every MediaSession callback. `media_session_state` intentionally mirrors
`python-androidtv`'s convention for upstream compatibility.

```json
{
  "media_session_state": 3,
  "app": "com.crunchyroll.crunchyroid",
  "title": "Demon Slayer S04E01",
  "artist": null,
  "album": null,
  "duration_ms": 1380000,
  "position_ms": 240000,
  "ts": 1747000000000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `media_session_state` | int | Android PlaybackState (see table below) |
| `app` | string | Package name of the active media session owner |
| `title` | string\|null | Track / episode title, or null when nothing is playing |
| `artist` | string\|null | Artist name, or null |
| `album` | string\|null | Album name, or null |
| `duration_ms` | int\|null | Total duration in milliseconds, or null |
| `position_ms` | int\|null | Current playback position in milliseconds, or null |
| `ts` | int | Unix epoch milliseconds when the APK emitted this payload |

| `media_session_state` | Meaning |
|-----------------------|---------|
| `0` | None / unknown |
| `1` | Stopped |
| `2` | Paused |
| `3` | Playing (also buffering, seeking) |

---

### `fire2mqtt/<device_id>/state/app`
Published when the foreground app changes (polled at 1s via UsageStatsManager).

```json
{
  "package": "com.crunchyroll.crunchyroid",
  "name": "Crunchyroll",
  "ts": 1747000000000
}
```

---

### `fire2mqtt/<device_id>/state/apps`
Published once on connect (since `schema_version` 2). The launchable packages installed on
the device, so the integration can offer only the apps that are actually present. A service
restart re-publishes after an install/uninstall.

```json
{
  "packages": [
    "com.netflix.ninja",
    "com.amazon.avod.thirdpartyclient",
    "org.jellyfin.androidtv"
  ],
  "ts": 1747000000000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `packages` | string[] | Package names of every launchable (`LAUNCHER` or `LEANBACK_LAUNCHER`) app, excluding Fire2MQTT itself |
| `ts` | int | Unix epoch milliseconds when the APK emitted this payload |

---

### `fire2mqtt/<device_id>/state/screen`
Published on `ACTION_SCREEN_ON` / `ACTION_SCREEN_OFF` system broadcasts.

```json
{
  "on": true,
  "ts": 1747000000000
}
```

---

### `fire2mqtt/<device_id>/state/volume`
Published when stream volume or mute state changes.

```json
{
  "level": 8,
  "max": 15,
  "mute": false,
  "ts": 1747000000000
}
```

---

## Command topics (HA → APK)

### `fire2mqtt/<device_id>/cmd/launch`
Payload: Android package name (or curated app key as a convenience alias).

```
com.crunchyroll.crunchyroid
```

### `fire2mqtt/<device_id>/cmd/key`
Payload: Android KeyEvent name (uppercase string).

Common values: `HOME`, `BACK`, `MENU`, `DPAD_UP`, `DPAD_DOWN`, `DPAD_LEFT`, `DPAD_RIGHT`,
`DPAD_CENTER`, `MEDIA_PLAY_PAUSE`, `MEDIA_PLAY`, `MEDIA_PAUSE`, `MEDIA_STOP`,
`MEDIA_NEXT`, `MEDIA_PREVIOUS`, `VOLUME_UP`, `VOLUME_DOWN`, `MUTE`.

### `fire2mqtt/<device_id>/cmd/volume`
```json
{ "action": "set", "level": 10 }
{ "action": "up" }
{ "action": "down" }
{ "action": "mute" }
{ "action": "unmute" }
```

### `fire2mqtt/<device_id>/cmd/power`
```
sleep
wake
```

### `fire2mqtt/<device_id>/cmd/media`
```
play | pause | play_pause | next | prev | stop
```
