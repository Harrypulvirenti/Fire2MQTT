"""Curated per-app state detection rules for Fire TV.

Rule list format is intentionally compatible with python-androidtv's
state_detection_rules schema to enable upstream PR contribution.

Each list is evaluated in order:
  - A plain string ("idle", "standby", "off", "playing", "paused") is an unconditional fallback.
  - A dict {"<state>": {<conditions>}} matches only when ALL conditions are satisfied.
    Supported condition keys: media_session_state (int), audio_state (str), wake_lock_size (int).

media_session_state integers mirror Android PlaybackState.STATE_*:
  0 = None/unknown, 1 = STOPPED, 2 = PAUSED, 3 = PLAYING
"""
from __future__ import annotations

CURATED_RULES: dict[str, list] = {
    # ── Crunchyroll ──────────────────────────────────────────────────────
    # Verified by direct dumpsys media_session observation.
    "com.crunchyroll.crunchyroid": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Netflix ──────────────────────────────────────────────────────────
    "com.netflix.ninja": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Prime Video ──────────────────────────────────────────────────────
    # Auto-playing trailers on home screen also set state=3; if app is
    # foreground and title is empty we stay "idle" (handled in media_player.py).
    "com.amazon.avod.thirdpartyclient": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── F1 TV ─────────────────────────────────────────────────────────────
    # F1 TV publishes no MediaSession at all, so media_session_state never
    # leaves 0. Fall back to audio_state (active audio playback) instead:
    # "playing" while audio is producing, "idle" otherwise. Pause can't be
    # distinguished from stop via audio playback, so there's no "paused" rule.
    "com.formulaone.production": [
        {"playing": {"audio_state": "playing"}},
        "idle",
    ],

    # ── YouTube (Fire TV edition) ─────────────────────────────────────────
    # YouTube sets state=3 during buffering; media_player.py coalesces
    # very-short playing→paused→playing cycles into "playing".
    "com.amazon.firetv.youtube": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Disney+ ──────────────────────────────────────────────────────────
    "com.disney.disneyplus": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Jellyfin ─────────────────────────────────────────────────────────
    "org.jellyfin.androidtv": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Plex ─────────────────────────────────────────────────────────────
    "com.plexapp.android": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Emby ─────────────────────────────────────────────────────────────
    "tv.emby.embyatv": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Spotify ──────────────────────────────────────────────────────────
    "com.spotify.music": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Twitch ───────────────────────────────────────────────────────────
    # Twitch live streams have no "paused" state, only playing or stopped.
    "tv.twitch.android.app": [
        {"playing": {"media_session_state": 3}},
        "idle",
    ],

    # ── Max (HBO) ────────────────────────────────────────────────────────
    "com.hbo.hbonow": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Apple TV ────────────────────────────────────────────────────────
    "com.apple.atve.amazon.appletv": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── Kodi ────────────────────────────────────────────────────────────
    "org.xbmc.kodi": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],
}
