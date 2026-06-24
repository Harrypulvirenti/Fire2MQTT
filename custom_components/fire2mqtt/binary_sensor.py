"""Fire2MQTT binary sensor entities."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Fire2MqttConfigEntry
from .const import MEDIA_SESSION_STATE_PLAYING
from .coordinator import Fire2MqttCoordinator
from .entity import Fire2MqttEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([
        ScreenOnSensor(coordinator),
        PlayingSensor(coordinator),
        ConnectivitySensor(coordinator),
    ])


class PlayingSensor(Fire2MqttEntity, BinarySensorEntity):
    """On while media is actively playing, off when paused/idle/stopped.

    Reads the primary media session's state from the playback payload — a simple
    'is something playing?' signal alongside the media_player entity's richer state.
    """

    _attr_name = "Playing"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:play-circle"

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "playing")

    @property
    def is_on(self) -> bool:
        return (
            self.coordinator.data.playback.get("media_session_state")
            == MEDIA_SESSION_STATE_PLAYING
        )


class ScreenOnSensor(Fire2MqttEntity, BinarySensorEntity):
    _attr_name = "Screen"
    _attr_device_class = BinarySensorDeviceClass.POWER

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "screen")

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.screen.get("on")


class ConnectivitySensor(Fire2MqttEntity, BinarySensorEntity):
    """Tracks the APK's MQTT LWT status — stays available so 'offline' is visible."""

    _attr_name = "Connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "connectivity")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.online
