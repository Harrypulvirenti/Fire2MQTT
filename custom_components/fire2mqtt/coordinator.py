"""Fire2MQTT coordinator — MQTT-driven, push-only (no polling)."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    TOPIC_STATE_APP,
    TOPIC_STATE_DEVICE,
    TOPIC_STATE_PLAYBACK,
    TOPIC_STATE_SCREEN,
    TOPIC_STATE_VOLUME,
    TOPIC_STATUS,
    TOPIC_CMD_LAUNCH,
    TOPIC_CMD_KEY,
    TOPIC_CMD_MEDIA,
    TOPIC_CMD_POWER,
    TOPIC_CMD_VOLUME,
)
from .mqtt_bus import MqttBus
from .schema import AppPayload, DevicePayload, PlaybackPayload, ScreenPayload, VolumePayload

_LOGGER = logging.getLogger(__name__)


@dataclass
class Fire2MqttData:
    online: bool = False
    playback: dict[str, Any] = field(default_factory=dict)
    app: dict[str, Any] = field(default_factory=dict)
    screen: dict[str, Any] = field(default_factory=dict)
    volume: dict[str, Any] = field(default_factory=dict)
    device_info: dict[str, Any] = field(default_factory=dict)


class Fire2MqttCoordinator(DataUpdateCoordinator[Fire2MqttData]):
    """Push-driven coordinator. Entities update immediately on MQTT message."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        topic_prefix: str,
        device_id: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{device_id}",
            update_interval=None,  # no polling — MQTT callbacks drive updates
        )
        self._prefix = topic_prefix
        self._device_id = device_id
        self._bus = MqttBus(hass, topic_prefix, device_id)
        self.data = Fire2MqttData()

    @property
    def device_id(self) -> str:
        """The user-chosen device slug shared with the APK."""
        return self._device_id

    async def async_setup(self) -> None:
        """Subscribe to all state topics. Called from async_setup_entry."""
        subscriptions = [
            (TOPIC_STATUS, self._on_status),
            (TOPIC_STATE_PLAYBACK, self._on_playback),
            (TOPIC_STATE_APP, self._on_app),
            (TOPIC_STATE_SCREEN, self._on_screen),
            (TOPIC_STATE_VOLUME, self._on_volume),
            (TOPIC_STATE_DEVICE, self._on_device_info),
        ]
        for template, handler in subscriptions:
            await self._bus.subscribe(template, handler)
        _LOGGER.debug(
            "Subscribed to %d MQTT topics for device %s",
            len(subscriptions),
            self._device_id,
        )

    async def async_teardown(self) -> None:
        """Unsubscribe from all topics. Called from async_unload_entry."""
        await self._bus.teardown()

    async def async_launch_app(self, package_or_key: str) -> None:
        await self._bus.publish(TOPIC_CMD_LAUNCH, package_or_key)

    async def async_send_key(self, key_name: str) -> None:
        await self._bus.publish(TOPIC_CMD_KEY, key_name)

    async def async_media_command(self, action: str) -> None:
        await self._bus.publish(TOPIC_CMD_MEDIA, action)

    async def async_power(self, action: str) -> None:
        """Send a power command ("sleep" or "wake")."""
        await self._bus.publish(TOPIC_CMD_POWER, action)

    async def async_set_volume(self, level: int) -> None:
        await self._bus.publish(TOPIC_CMD_VOLUME, {"action": "set", "level": level})

    async def async_volume_step(self, up: bool) -> None:
        await self._bus.publish(TOPIC_CMD_VOLUME, {"action": "up" if up else "down"})

    async def async_mute_volume(self, mute: bool) -> None:
        action = "mute" if mute else "unmute"
        await self._bus.publish(TOPIC_CMD_VOLUME, {"action": action})

    # ── MQTT callbacks ────────────────────────────────────────────────────

    @callback
    def _on_status(self, msg: mqtt.ReceiveMessage) -> None:
        online = msg.payload.strip().lower() == "online"
        if self.data.online != online:
            self.data.online = online
            self.async_set_updated_data(self.data)

    @callback
    def _on_playback(self, msg: mqtt.ReceiveMessage) -> None:
        parsed = self._parse_json(msg.payload)
        if parsed is None:
            return
        self.data.playback = PlaybackPayload.from_raw(parsed, logger=_LOGGER)
        self.async_set_updated_data(self.data)

    @callback
    def _on_app(self, msg: mqtt.ReceiveMessage) -> None:
        parsed = self._parse_json(msg.payload)
        if parsed is None:
            return
        self.data.app = AppPayload.from_raw(parsed, logger=_LOGGER)
        self.async_set_updated_data(self.data)

    @callback
    def _on_screen(self, msg: mqtt.ReceiveMessage) -> None:
        parsed = self._parse_json(msg.payload)
        if parsed is None:
            return
        self.data.screen = ScreenPayload.from_raw(parsed, logger=_LOGGER)
        self.async_set_updated_data(self.data)

    @callback
    def _on_volume(self, msg: mqtt.ReceiveMessage) -> None:
        parsed = self._parse_json(msg.payload)
        if parsed is None:
            return
        self.data.volume = VolumePayload.from_raw(parsed, logger=_LOGGER)
        self.async_set_updated_data(self.data)

    @callback
    def _on_device_info(self, msg: mqtt.ReceiveMessage) -> None:
        parsed = self._parse_json(msg.payload)
        if parsed is None:
            return
        self.data.device_info = DevicePayload.from_raw(parsed, logger=_LOGGER)
        self._sync_device_registry()
        self.async_set_updated_data(self.data)

    @callback
    def _sync_device_registry(self) -> None:
        """Push model/firmware/MAC into the device registry.

        HA only reads an entity's device_info when the entity is added, but the
        state/device payload usually arrives after setup — sync it explicitly.
        """
        registry = dr.async_get(self.hass)
        device = registry.async_get_device(identifiers={(DOMAIN, self._device_id)})
        if device is None:
            return
        info = self.data.device_info
        updates: dict[str, Any] = {}
        if model := info.get("model"):
            updates["model"] = model
        if fire_os := info.get("fire_os"):
            updates["sw_version"] = fire_os
        if mac := info.get("mac"):
            updates["merge_connections"] = {(dr.CONNECTION_NETWORK_MAC, mac)}
        if updates:
            registry.async_update_device(device.id, **updates)

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            _LOGGER.warning("Fire2MQTT: invalid JSON payload: %.200r", raw)
            return None
        if not isinstance(parsed, dict):
            _LOGGER.warning("Fire2MQTT: payload is not a JSON object: %.200r", raw)
            return None
        return parsed
