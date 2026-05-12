# Contributing a new app to the state detection database

The curated database lives in two files:

- `custom_components/fire2mqtt/data/apps.py` — friendly name, package, MDI icon
- `custom_components/fire2mqtt/data/rules.py` — per-app state detection rules

Both files use the same dict key format and are intentionally compatible with
`python-androidtv`'s `constants.py` / rule schema for future upstream contribution.

---

## How to discover rules for a new app

### Step 1 — Find the package name

```bash
adb shell pm list packages | grep <app_name_fragment>
```

### Step 2 — Observe MediaSession state while using the app

Use the helper script:
```bash
python3 tools/dump_rules_from_adb.py --device-ip 192.168.1.50
```

Or manually:
```bash
# Watch media session state changes live
watch -n 1 "adb shell dumpsys media_session | grep -A 5 '<package_name>'"
```

Take note of `state=<int>` while:
- Actively playing → should be `3`
- Paused → should be `2`
- On the app home screen (not playing) → usually `1` or `0`
- App closed → session disappears

### Step 3 — Add the app entry

In `data/apps.py`, add to `CURATED_APPS`:
```python
"my_app_key": AppInfo(
    package="com.example.myapp",
    friendly_name="My App",
    category="streaming",
    icon_mdi="mdi:television-play",
),
```

In `data/rules.py`, add to `CURATED_RULES`:
```python
"com.example.myapp": [
    {"playing": {"media_session_state": 3}},
    {"paused": {"media_session_state": 2}},
    "idle",  # fallback when app is open but nothing playing
],
```

### Step 4 — Test with the simulator

```bash
# Simulate the new app's playback cycle
python3 tools/mqtt_simulator.py --device-id test_device --app com.example.myapp
```

Check that `media_player` in HA transitions `idle → playing → paused → idle` correctly.

### Step 5 — Open a PR

Include the app name, package, Fire OS version tested, and the observed `media_session_state` values.

---

## Edge cases to watch for

| App behaviour | How to handle |
|---|---|
| Trailers auto-play on home screen (Prime Video) | Add a note in the rules comment. The HA integration will show "playing" for trailers — document this in the PR. |
| Live streams have no "paused" state (Twitch) | Omit the paused rule; use `"idle"` as the only fallback. |
| App sets `state=3` during buffering | This is intentional — schema int 3 maps both PLAYING and BUFFERING, matching python-androidtv convention. |
| Multiple active MediaSessions | The APK publishes the most-recently-active session. No action needed. |
