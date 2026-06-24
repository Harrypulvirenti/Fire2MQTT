"""pytest fixtures for Fire2MQTT integration tests."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Imported for its side effect: puts the custom_components package in
# sys.modules so HA's loader discovers the integration even when a test file
# that doesn't import it directly is run on its own.
import custom_components.fire2mqtt  # noqa: F401

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let every test load integrations from custom_components/."""
    yield

DEVICE_ID = "test_device"
PREFIX = "fire2mqtt"

TOPIC_STATUS = f"{PREFIX}/{DEVICE_ID}/status"
TOPIC_PLAYBACK = f"{PREFIX}/{DEVICE_ID}/state/playback"
TOPIC_APP = f"{PREFIX}/{DEVICE_ID}/state/app"
TOPIC_SCREEN = f"{PREFIX}/{DEVICE_ID}/state/screen"
TOPIC_VOLUME = f"{PREFIX}/{DEVICE_ID}/state/volume"
TOPIC_APPS = f"{PREFIX}/{DEVICE_ID}/state/apps"
TOPIC_DEVICE = f"{PREFIX}/{DEVICE_ID}/state/device"
TOPIC_CMD_MEDIA = f"{PREFIX}/{DEVICE_ID}/cmd/media"
TOPIC_CMD_LAUNCH = f"{PREFIX}/{DEVICE_ID}/cmd/launch"
TOPIC_CMD_KEY = f"{PREFIX}/{DEVICE_ID}/cmd/key"
TOPIC_CMD_VOLUME = f"{PREFIX}/{DEVICE_ID}/cmd/volume"
TOPIC_CMD_POWER = f"{PREFIX}/{DEVICE_ID}/cmd/power"


@pytest.fixture
def mqtt_payloads() -> dict:
    with open(FIXTURES_DIR / "mqtt_payloads.json") as f:
        return json.load(f)


@pytest.fixture
def mock_mqtt_subscribe():
    """Mock mqtt.async_subscribe to capture subscriptions and replay test messages."""
    subscriptions: dict[str, list] = {}
    unsub_callbacks: list = []

    async def _subscribe(hass, topic, callback):
        subscriptions.setdefault(topic, []).append(callback)
        mock_unsub = MagicMock()
        unsub_callbacks.append(mock_unsub)
        return mock_unsub

    async def deliver(topic: str, payload: str):
        msg = MagicMock()
        msg.topic = topic
        msg.payload = payload
        for cb in subscriptions.get(topic, []):
            cb(msg)

    mock = AsyncMock(side_effect=_subscribe)
    mock.deliver = deliver
    mock.subscriptions = subscriptions

    with patch("homeassistant.components.mqtt.async_subscribe", mock):
        yield mock


@pytest.fixture
def mock_mqtt_publish():
    published: list[tuple] = []

    async def _publish(hass, topic, payload, **kwargs):
        published.append((topic, payload))

    mock = AsyncMock(side_effect=_publish)
    mock.published = published

    with patch("homeassistant.components.mqtt.async_publish", mock):
        yield mock


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain="fire2mqtt",
        title=f"Fire TV {DEVICE_ID}",
        data={"device_id": DEVICE_ID, "topic_prefix": PREFIX},
        options={},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_integration(hass: HomeAssistant, config_entry: MockConfigEntry, mock_mqtt_subscribe, mock_mqtt_publish):
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    yield config_entry
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
