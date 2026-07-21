"""Tests for the state detection rule evaluator."""
import pytest

from custom_components.fire2mqtt.state_detection import evaluate
from custom_components.fire2mqtt.data.rules import CURATED_RULES, DEFAULT_RULES


@pytest.mark.parametrize("app,state_int,expected", [
    ("com.crunchyroll.crunchyroid", 3, "playing"),
    ("com.crunchyroll.crunchyroid", 2, "paused"),
    ("com.crunchyroll.crunchyroid", 0, "idle"),
    ("com.netflix.ninja", 3, "playing"),
    ("com.netflix.ninja", 2, "paused"),
    ("com.amazon.avod.thirdpartyclient", 3, "playing"),
    ("com.amazon.avod.thirdpartyclient", 2, "paused"),
    ("com.amazon.firetv.youtube", 3, "playing"),
    ("com.amazon.firetv.youtube", 2, "paused"),
    ("com.disney.disneyplus", 3, "playing"),
    ("com.disney.disneyplus", 2, "paused"),
    ("org.jellyfin.androidtv", 3, "playing"),
    ("org.jellyfin.androidtv", 2, "paused"),
    ("com.plexapp.android", 3, "playing"),
    ("com.plexapp.android", 2, "paused"),
    ("tv.emby.embyatv", 3, "playing"),
    ("tv.emby.embyatv", 2, "paused"),
    # Twitch has no paused state
    ("tv.twitch.android.app", 3, "playing"),
    ("tv.twitch.android.app", 2, "idle"),  # falls through to idle
    ("com.nuvio.tv", 3, "playing"),
    ("com.nuvio.tv", 2, "paused"),
])
def test_curated_rules(app: str, state_int: int, expected: str):
    rules = CURATED_RULES.get(app, ["idle"])
    result = evaluate(rules, {"media_session_state": state_int})
    assert result == expected, f"{app} state={state_int}: expected {expected}, got {result}"


def test_unconditional_fallback():
    rules = ["standby"]
    assert evaluate(rules, {}) == "standby"


def test_first_match_wins():
    rules = [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 3}},  # never reached
        "idle",
    ]
    assert evaluate(rules, {"media_session_state": 3}) == "playing"


def test_all_conditions_must_match():
    rules = [{"playing": {"media_session_state": 3, "wake_lock_size": 4}}]
    # Only media_session_state=3, no wake_lock_size — should NOT match
    assert evaluate(rules, {"media_session_state": 3}) is None


def test_unknown_app_returns_none_without_fallback():
    assert evaluate([], {"media_session_state": 3}) is None


@pytest.mark.parametrize("state_int,expected", [
    (3, "playing"),
    (2, "paused"),
    (0, "idle"),
])
def test_uncurated_package_gets_default_rules(state_int: int, expected: str):
    """An uncurated package falls back to DEFAULT_RULES (media_player._get_rules mirrors
    this lookup), so it gets real playing/paused detection instead of being stuck at idle."""
    rules = CURATED_RULES.get("com.some.unknown.app", DEFAULT_RULES)
    assert rules is DEFAULT_RULES
    result = evaluate(rules, {"media_session_state": state_int})
    assert result == expected


def test_all_curated_apps_have_rules():
    from custom_components.fire2mqtt.data.apps import CURATED_APPS
    for key, info in CURATED_APPS.items():
        assert info.package in CURATED_RULES, (
            f"App '{key}' ({info.package}) is in apps.py but missing from rules.py"
        )
