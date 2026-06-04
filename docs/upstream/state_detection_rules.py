"""Curated per-app state detection rules for Fire TV / Android TV.

This module is a **self-contained, dependency-free** mirror of the rule
database maintained in the Fire2MQTT project
(https://github.com/Harrypulvirenti/Fire2MQTT).  It is formatted to be a
drop-in contribution to ``python-androidtv``'s ``androidtv/constants.py``
as a ``STATE_DETECTION_RULES`` companion to the existing ``APPS`` dict.

Credit
------
Rules verified through real-device ``dumpsys media_session`` observation by
Fire2MQTT contributors.  See the Fire2MQTT repository for the full list of
contributors and per-app verification notes.

``media_session_state`` semantics
----------------------------------
The integer values mirror Android's ``PlaybackState.STATE_*`` constants as
exposed via ``dumpsys media_session``:

    0  — None / unknown  (no active session, or state not yet reported)
    1  — STOPPED         (session exists but playback has stopped)
    2  — PAUSED          (playback is paused / buffering)
    3  — PLAYING         (playback is active, including seeking / buffering)

These are the same values used by ``python-androidtv``'s
``CONF_STATE_DETECTION_RULES`` / ``_custom_state_detection``.

Rule list format
----------------
Each value in ``STATE_DETECTION_RULES`` is a rule list compatible with
``python-androidtv``'s ``_custom_state_detection`` logic:

  - A plain string (``"idle"``, ``"paused"``, ``"playing"``, …) is an
    unconditional fallback — it always matches and ends evaluation.
  - A dict ``{"<ha_state>": {<conditions>}}`` matches only when **all**
    conditions are satisfied.  Supported condition keys:

      * ``media_session_state`` (int)
      * ``audio_state``         (str)
      * ``wake_lock_size``      (int)

Rules are evaluated in order; the first match wins.


Evaluator (copy from Fire2MQTT ``state_detection.py``)
------------------------------------------------------
The ``evaluate`` and ``_conditions_match`` functions below reproduce the
logic exactly so this file remains self-contained.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Rule evaluator (self-contained copy of Fire2MQTT state_detection.py logic)
# ---------------------------------------------------------------------------

def evaluate(rules: list, payload: dict[str, Any]) -> str | None:
    """Evaluate a rule list against a playback payload.

    Returns the matched HA state string, or ``None`` if no rule matches.
    The caller should fall back to ``"idle"`` when ``None`` is returned.
    """
    for rule in rules:
        if isinstance(rule, str):
            return rule

        if not isinstance(rule, dict):
            continue

        for state, conditions in rule.items():
            if _conditions_match(conditions, payload):
                return state

    return None


def _conditions_match(conditions: dict[str, Any], payload: dict[str, Any]) -> bool:
    """Return ``True`` only when every condition key matches the payload."""
    for key, expected in conditions.items():
        if payload.get(key) != expected:
            return False
    return True


# ---------------------------------------------------------------------------
# Curated rule database
# (mirror of custom_components/fire2mqtt/data/rules.py — keep in sync)
# ---------------------------------------------------------------------------

STATE_DETECTION_RULES: dict[str, list] = {
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
    # foreground and title is empty we stay "idle" (handled upstream in
    # basetv logic or custom media_player).
    "com.amazon.avod.thirdpartyclient": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],

    # ── YouTube (Fire TV edition) ─────────────────────────────────────────
    # YouTube sets state=3 during buffering; short playing→paused→playing
    # cycles should be coalesced upstream into "playing".
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
