"""pytest fixtures for Fire2MQTT integration tests."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
