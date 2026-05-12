"""State detection rule evaluator.

Pure-function port of python-androidtv's _custom_state_detection logic.
Keeping this format-compatible ensures the data/rules.py database
can be contributed upstream as a drop-in dict.
"""
from __future__ import annotations

from typing import Any


def evaluate(rules: list, payload: dict[str, Any]) -> str | None:
    """Evaluate a rule list against a playback payload.

    Returns the matched HA state string, or None if no rule matches.
    The caller should fall back to "idle" when None is returned.
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
    """Return True only when every condition key matches the payload."""
    for key, expected in conditions.items():
        if key == "media_session_state":
            if payload.get("media_session_state") != expected:
                return False
        elif key == "audio_state":
            if payload.get("audio_state") != expected:
                return False
        elif key == "wake_lock_size":
            if payload.get("wake_lock_size") != expected:
                return False
        else:
            if payload.get(key) != expected:
                return False
    return True
