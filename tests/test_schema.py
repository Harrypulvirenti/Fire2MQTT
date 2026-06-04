"""Tests for the Fire2MQTT schema / payload models."""
from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock

import pytest

from custom_components.fire2mqtt.schema import (
    AppPayload,
    DevicePayload,
    PlaybackPayload,
    ScreenPayload,
    VolumePayload,
)
from custom_components.fire2mqtt.const import SCHEMA_VERSION
from custom_components.fire2mqtt.coordinator import Fire2MqttCoordinator
from custom_components.fire2mqtt.state_detection import evaluate
from custom_components.fire2mqtt.data.rules import CURATED_RULES


# ---------------------------------------------------------------------------
# Helpers (mirrors test_coordinator.py make_msg pattern)
# ---------------------------------------------------------------------------

def make_msg(payload: str | dict) -> MagicMock:
    msg = MagicMock()
    msg.payload = payload if isinstance(payload, str) else json.dumps(payload)
    return msg


@pytest.fixture
def coordinator(hass):
    return Fire2MqttCoordinator(hass, topic_prefix="fire2mqtt", device_id="test_device")


# ---------------------------------------------------------------------------
# PlaybackPayload
# ---------------------------------------------------------------------------

class TestPlaybackPayload:
    def test_string_media_session_state_coerced_to_int(self):
        """The original string-vs-int bug: APK may send "3" as a string."""
        result = PlaybackPayload.from_raw(
            {"media_session_state": "3", "app": "com.netflix.ninja"}
        )
        assert result["media_session_state"] == 3
        assert isinstance(result["media_session_state"], int)

    def test_string_coercion_feeds_state_detection(self):
        """PlaybackPayload.from_raw coerces str→int so evaluate() returns 'playing'."""
        result = PlaybackPayload.from_raw(
            {"media_session_state": "3", "app": "com.netflix.ninja"}
        )
        rules = CURATED_RULES["com.netflix.ninja"]
        assert evaluate(rules, result) == "playing"

    def test_unknown_keys_dropped(self):
        result = PlaybackPayload.from_raw(
            {
                "media_session_state": 3,
                "app": "com.netflix.ninja",
                "title": "The Crown",
                "unknown_future_field": "should_be_gone",
                "another_unknown": 42,
            }
        )
        assert "unknown_future_field" not in result
        assert "another_unknown" not in result

    def test_missing_optional_fields_default_to_none(self):
        result = PlaybackPayload.from_raw({"media_session_state": 3, "app": "com.netflix.ninja"})
        assert result["title"] is None
        assert result["artist"] is None
        assert result["album"] is None
        assert result["duration_ms"] is None
        assert result["position_ms"] is None
        assert result["audio_state"] is None
        assert result["wake_lock_size"] is None

    def test_missing_required_fields_use_zero_defaults(self):
        result = PlaybackPayload.from_raw({})
        assert result["media_session_state"] == 0
        assert result["app"] == ""
        assert result["ts"] == 0

    def test_null_optional_fields_become_none(self):
        result = PlaybackPayload.from_raw(
            {"media_session_state": 3, "app": "x", "title": None, "duration_ms": None}
        )
        assert result["title"] is None
        assert result["duration_ms"] is None

    def test_full_fixture_round_trip(self, mqtt_payloads):
        raw = mqtt_payloads["playback_playing"]
        result = PlaybackPayload.from_raw(raw)
        assert result["media_session_state"] == 3
        assert result["app"] == "com.crunchyroll.crunchyroid"
        assert result["title"] == "Demon Slayer S4E01"
        assert result["duration_ms"] == 1380000
        assert result["position_ms"] == 240000

    def test_invalid_int_field_warns_and_uses_default(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = PlaybackPayload.from_raw(
                {"media_session_state": "not-a-number"},
                logger=logging.getLogger("test"),
            )
        assert result["media_session_state"] == 0
        assert any("media_session_state" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# AppPayload
# ---------------------------------------------------------------------------

class TestAppPayload:
    def test_basic_round_trip(self, mqtt_payloads):
        result = AppPayload.from_raw(mqtt_payloads["app_crunchyroll"])
        assert result["package"] == "com.crunchyroll.crunchyroid"
        assert result["name"] == "Crunchyroll"

    def test_unknown_keys_dropped(self):
        result = AppPayload.from_raw({"package": "x", "name": "X", "ts": 1, "extra": "gone"})
        assert "extra" not in result

    def test_missing_fields_use_defaults(self):
        result = AppPayload.from_raw({})
        assert result["package"] == ""
        assert result["name"] == ""
        assert result["ts"] == 0


# ---------------------------------------------------------------------------
# ScreenPayload
# ---------------------------------------------------------------------------

class TestScreenPayload:
    def test_bool_true(self, mqtt_payloads):
        result = ScreenPayload.from_raw(mqtt_payloads["screen_on"])
        assert result["on"] is True

    def test_bool_false(self, mqtt_payloads):
        result = ScreenPayload.from_raw(mqtt_payloads["screen_off"])
        assert result["on"] is False

    def test_string_true_coerced(self):
        result = ScreenPayload.from_raw({"on": "true", "ts": 0})
        assert result["on"] is True

    def test_int_1_coerced_to_true(self):
        result = ScreenPayload.from_raw({"on": 1, "ts": 0})
        assert result["on"] is True

    def test_unknown_keys_dropped(self):
        result = ScreenPayload.from_raw({"on": True, "ts": 0, "brightness": 255})
        assert "brightness" not in result

    def test_missing_on_defaults_false(self):
        result = ScreenPayload.from_raw({})
        assert result["on"] is False


# ---------------------------------------------------------------------------
# VolumePayload
# ---------------------------------------------------------------------------

class TestVolumePayload:
    def test_full_fixture_round_trip(self, mqtt_payloads):
        result = VolumePayload.from_raw(mqtt_payloads["volume_8_of_15"])
        assert result["level"] == 8
        assert result["max"] == 15
        assert result["mute"] is False

    def test_muted_fixture(self, mqtt_payloads):
        result = VolumePayload.from_raw(mqtt_payloads["volume_muted"])
        assert result["mute"] is True

    def test_unknown_keys_dropped(self):
        result = VolumePayload.from_raw(
            {"level": 5, "max": 15, "mute": False, "ts": 0, "stream_type": 3}
        )
        assert "stream_type" not in result

    def test_missing_fields_use_defaults(self):
        result = VolumePayload.from_raw({})
        assert result["level"] == 0
        assert result["max"] == 0
        assert result["mute"] is False


# ---------------------------------------------------------------------------
# DevicePayload
# ---------------------------------------------------------------------------

class TestDevicePayload:
    def test_full_fixture_round_trip(self, mqtt_payloads):
        result = DevicePayload.from_raw(mqtt_payloads["device_info"])
        assert result["model"] == "Fire TV Stick 4K"
        assert result["fire_os"] == "8.2.2.1"
        assert result["schema_version"] == 1

    def test_schema_version_mismatch_logs_warning(self, caplog):
        mismatched_version = SCHEMA_VERSION + 99
        with caplog.at_level(logging.WARNING):
            result = DevicePayload.from_raw(
                {
                    "model": "Fire TV",
                    "fire_os": "9.0",
                    "ip": "10.0.0.1",
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "schema_version": mismatched_version,
                },
                logger=logging.getLogger("test"),
            )
        assert result["schema_version"] == mismatched_version
        assert any("schema_version" in r.message for r in caplog.records)

    def test_matching_schema_version_no_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            DevicePayload.from_raw(
                {
                    "model": "Fire TV",
                    "fire_os": "8.2",
                    "ip": "10.0.0.1",
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "schema_version": SCHEMA_VERSION,
                },
                logger=logging.getLogger("test"),
            )
        # No schema_version warning should be present
        schema_warnings = [r for r in caplog.records if "schema_version" in r.message]
        assert schema_warnings == []

    def test_unknown_keys_dropped(self):
        result = DevicePayload.from_raw(
            {
                "model": "x",
                "fire_os": "1",
                "ip": "1.2.3.4",
                "mac": "aa:bb:cc:dd:ee:ff",
                "schema_version": 1,
                "extra_hw_info": "ignored",
            }
        )
        assert "extra_hw_info" not in result


# ---------------------------------------------------------------------------
# Coordinator keep-last-good (malformed JSON path)
# ---------------------------------------------------------------------------

class TestCoordinatorKeepLastGood:
    def test_malformed_json_keeps_previous_playback(self, coordinator):
        """On bad JSON the previous data.playback value is preserved."""
        good_payload = {"media_session_state": 3, "app": "com.netflix.ninja"}
        coordinator._on_playback(make_msg(good_payload))
        assert coordinator.data.playback["media_session_state"] == 3

        # Now send malformed JSON — data.playback should remain unchanged
        coordinator._on_playback(make_msg("not-json"))
        assert coordinator.data.playback["media_session_state"] == 3

    def test_malformed_json_starting_from_empty_stays_empty(self, coordinator):
        """Bad JSON on a fresh coordinator leaves data.playback as {}."""
        coordinator._on_playback(make_msg("not-json"))
        assert coordinator.data.playback == {}

    def test_malformed_json_keeps_previous_app(self, coordinator):
        coordinator._on_app(make_msg({"package": "com.netflix.ninja", "name": "Netflix", "ts": 1}))
        coordinator._on_app(make_msg("bad-json"))
        assert coordinator.data.app["package"] == "com.netflix.ninja"

    def test_malformed_json_keeps_previous_screen(self, coordinator):
        coordinator._on_screen(make_msg({"on": True, "ts": 1}))
        coordinator._on_screen(make_msg("bad-json"))
        assert coordinator.data.screen["on"] is True

    def test_malformed_json_keeps_previous_volume(self, coordinator):
        coordinator._on_volume(make_msg({"level": 8, "max": 15, "mute": False, "ts": 1}))
        coordinator._on_volume(make_msg("bad-json"))
        assert coordinator.data.volume["level"] == 8


# ---------------------------------------------------------------------------
# MqttBus publish behaviour
# ---------------------------------------------------------------------------

class TestMqttBus:
    @pytest.mark.asyncio
    async def test_publish_dict_is_json_encoded(self, mock_mqtt_publish):
        """MqttBus.publish JSON-encodes dicts before calling async_publish."""
        from custom_components.fire2mqtt.mqtt_bus import MqttBus
        from homeassistant.core import HomeAssistant

        hass = MagicMock(spec=HomeAssistant)
        bus = MqttBus(hass, prefix="fire2mqtt", device_id="dev1")
        await bus.publish("{prefix}/{device_id}/cmd/volume", {"action": "mute"})

        assert len(mock_mqtt_publish.published) == 1
        topic, raw = mock_mqtt_publish.published[0]
        assert topic == "fire2mqtt/dev1/cmd/volume"
        # Payload must be valid JSON encoding the original dict
        assert json.loads(raw) == {"action": "mute"}

    @pytest.mark.asyncio
    async def test_publish_str_passes_through_unchanged(self, mock_mqtt_publish):
        """MqttBus.publish passes string payloads through without JSON encoding."""
        from custom_components.fire2mqtt.mqtt_bus import MqttBus
        from homeassistant.core import HomeAssistant

        hass = MagicMock(spec=HomeAssistant)
        bus = MqttBus(hass, prefix="fire2mqtt", device_id="dev1")
        await bus.publish("{prefix}/{device_id}/cmd/launch", "com.netflix.ninja")

        assert len(mock_mqtt_publish.published) == 1
        topic, raw = mock_mqtt_publish.published[0]
        assert topic == "fire2mqtt/dev1/cmd/launch"
        assert raw == "com.netflix.ninja"
