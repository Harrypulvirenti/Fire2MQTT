"""MQTT transport abstraction for Fire2MQTT.

``MqttBus`` owns topic formatting, subscription lifecycle, and publishing.
The coordinator delegates all MQTT I/O here, keeping the coordinator focused
on data/state management.
"""
from __future__ import annotations

import json
from typing import Any, Callable

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant


class MqttBus:
    """Thin wrapper around HA's MQTT helpers.

    Responsibilities
    ----------------
    - Format topic templates using ``prefix`` and ``device_id``.
    - Track subscription unsub callbacks and tear them all down at once.
    - Publish commands, JSON-encoding non-string payloads automatically.
    """

    def __init__(self, hass: HomeAssistant, prefix: str, device_id: str) -> None:
        self.hass = hass
        self._prefix = prefix
        self._device_id = device_id
        self._unsubscribe: list[Callable] = []

    # ── Topic helpers ──────────────────────────────────────────────────────

    def topic(self, template: str) -> str:
        """Format a state-topic template."""
        return template.format(prefix=self._prefix, device_id=self._device_id)

    def cmd_topic(self, template: str) -> str:
        """Format a command-topic template."""
        return template.format(prefix=self._prefix, device_id=self._device_id)

    # ── Subscription management ────────────────────────────────────────────

    async def subscribe(self, template: str, handler: Callable) -> Callable:
        """Subscribe to *template* (formatted) and track the unsub callable."""
        formatted = self.topic(template)
        unsub = await mqtt.async_subscribe(self.hass, formatted, handler)
        self._unsubscribe.append(unsub)
        return unsub

    async def teardown(self) -> None:
        """Unsubscribe from all tracked topics and clear the list."""
        for unsub in self._unsubscribe:
            unsub()
        self._unsubscribe.clear()

    # ── Publishing ─────────────────────────────────────────────────────────

    async def publish(self, template: str, payload: Any) -> None:
        """Publish *payload* to the formatted command topic.

        String payloads are sent as-is; everything else is JSON-encoded.
        """
        topic = self.cmd_topic(template)
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        await mqtt.async_publish(self.hass, topic, raw)
