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
        ConnectivitySensor(coordinator),
    ])


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
