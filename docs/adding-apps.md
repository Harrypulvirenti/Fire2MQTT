# Contributing a new app to the state detection database

The curated database lives in two files:

- `custom_components/fire2mqtt/data/apps.py` — friendly name, package, MDI icon
- `custom_components/fire2mqtt/data/rules.py` — per-app state detection rules

Both files use the same dict key format and are intentionally compatible with
`python-androidtv`'s `constants.py` / rule schema for future upstream contribution.

---

## Curated apps vs. the fallback rules — do you actually need this?

Any app that publishes a standard Android `MediaSession` already gets a best-effort
`playing`/`paused`/`idle` state with **zero curation**: `media_player._get_rules()` falls
back to `DEFAULT_RULES` (`custom_components/fire2mqtt/data/rules.py`) for any package that
isn't in `CURATED_RULES` — the same `media_session_state` 3 = playing / 2 = paused / else
idle triplet used by most curated apps. So before spending time on a full curated entry,
just try the app: if it plays and pauses correctly already, you're done.

What curation on top of that fallback actually buys you:

| Curated-only benefit | Why the fallback can't provide it |
|---|---|
| Friendly name + icon in the app-launcher `select` and source list | The fallback has no name/icon metadata — an uncurated app never appears as a pickable/launchable option, even though its live state still reports correctly while it's in the foreground |
| Verified, app-specific rules | The fallback is a guess. Apps that deviate from the standard convention — no MediaSession at all (F1 TV, keyed off `audio_state` instead), no "paused" state (Twitch, live-only) — need a hand-written rule or they'll misreport |
| Package aliases (`alt_packages`) | Apps shipped under multiple package names (e.g. Prime Video's Play-Store vs Fire-TV-native builds) only resolve to one set of rules if the aliases are declared in `apps.py` |

If all you want is correct playback state and you don't care about the launcher entry, no
action is needed — the fallback already covers it. If you want the friendly launcher entry,
or the app doesn't behave like the standard convention, follow the steps below.

---

## Just want an app added? Open an issue, no PR required

Don't have the time or an ADB setup to verify rules yourself? Open a [GitHub
issue](https://github.com/Harrypulvirenti/Fire2MQTT/issues) with:

- The app's name and, if you know it, its Android package name (`adb shell pm list packages`
  or the app's Play Store / Amazon Appstore listing URL)
- Whether the fallback already gets `playing`/`paused` right for you (see the table above) —
  if it does, this is just a request for the launcher entry (name/icon), which is quick to add
- If it *doesn't* detect state correctly: what you observed (e.g. "stuck on idle while
  playing", "playing never switches to paused")

You don't need to gather `dumpsys` output yourself — that's only required if you want to
contribute the fix directly (see below). A maintainer (or another contributor) can still pick
up the issue and do the verification.

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
