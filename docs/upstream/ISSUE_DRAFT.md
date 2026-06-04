# [Feature] Ship a curated `STATE_DETECTION_RULES` database alongside `APPS`

## Problem

`python-androidtv` ships the excellent `APPS` dict (150+ package → friendly-name
entries) but provides **no per-app state detection rules**.  Every user who wants
accurate playing/paused/idle detection must write their own YAML rules from scratch
— and most don't, leaving them with a media player that is always "idle".

The `CONF_STATE_DETECTION_RULES` / `_custom_state_detection` machinery already
exists and works well.  What's missing is a community-maintained default rule set
that kicks in automatically when the user has not written their own rules.

## Proposed solution

Add a `STATE_DETECTION_RULES: dict[str, list]` constant to
`androidtv/constants.py`, using the same rule-list format already understood by
`_custom_state_detection`:

```python
STATE_DETECTION_RULES: dict[str, list] = {
    "com.netflix.ninja": [
        {"playing": {"media_session_state": 3}},
        {"paused":  {"media_session_state": 2}},
        "idle",
    ],
    # ... one entry per app
}
```

Then in `basetv/basetv.py`, fall back to `STATE_DETECTION_RULES` when no
user-provided rules exist for the current app — user rules always take
precedence.

## Existing rule database — 13 verified apps

The [Fire2MQTT](https://github.com/Harrypulvirenti/Fire2MQTT) project already
maintains a `data/rules.py` database built from real-device
`dumpsys media_session` observation.  It currently covers **13 apps**:

| App | Package |
|-----|---------|
| Crunchyroll | `com.crunchyroll.crunchyroid` |
| Netflix | `com.netflix.ninja` |
| Prime Video | `com.amazon.avod.thirdpartyclient` |
| YouTube (Fire TV) | `com.amazon.firetv.youtube` |
| Disney+ | `com.disney.disneyplus` |
| Jellyfin | `org.jellyfin.androidtv` |
| Plex | `com.plexapp.android` |
| Emby | `tv.emby.embyatv` |
| Spotify | `com.spotify.music` |
| Twitch | `tv.twitch.android.app` |
| Max (HBO) | `com.hbo.hbonow` |
| Apple TV | `com.apple.atve.amazon.appletv` |
| Kodi | `org.xbmc.kodi` |

The rules use only `media_session_state` today; entries that require
`audio_state` or `wake_lock_size` disambiguation can be added later.

A self-contained copy of the database formatted as `STATE_DETECTION_RULES` —
including a standalone `evaluate()` function and full docstring — lives at
[`docs/upstream/state_detection_rules.py`](state_detection_rules.py)
in the Fire2MQTT repo.

## Format compatibility

The rule-list format is **already identical** to what `_custom_state_detection`
expects.  The only change needed on the python-androidtv side is:

1. Add `STATE_DETECTION_RULES` to `androidtv/constants.py`.
2. In `basetv/basetv.py`, after checking user-provided rules, fall back:

   ```python
   from .constants import STATE_DETECTION_RULES
   # ...
   rules = self._state_detection_rules.get(current_app) \
           or STATE_DETECTION_RULES.get(current_app)
   if rules:
       return self._custom_state_detection(rules, ...)
   ```

3. Add tests and update the docs noting that curated rules exist and user
   rules take precedence.

## `media_session_state` integer mapping

| Value | Android `PlaybackState` constant | Meaning |
|-------|----------------------------------|---------|
| `0` | `STATE_NONE` | No session / unknown |
| `1` | `STATE_STOPPED` | Playback stopped |
| `2` | `STATE_PAUSED` | Paused / buffering |
| `3` | `STATE_PLAYING` | Playing (also seeking) |

These are the same values already used by python-androidtv.

## Next steps

- [ ] Confirm interest from maintainer before submitting PR
- [ ] Expand rule DB to cover more apps (contributions welcome in Fire2MQTT first)
- [ ] Decide whether `STATE_DETECTION_RULES` lives in `constants.py` or a
      separate `state_detection_rules.py` module
- [ ] Add tests in python-androidtv's test suite
- [ ] Update docs

## References

- Fire2MQTT repo: https://github.com/Harrypulvirenti/Fire2MQTT
- Rule database: `custom_components/fire2mqtt/data/rules.py`
- Upstream target file: `androidtv/constants.py`
