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
from .const import CONF_STATE_DETECTION_RULES_OVERRIDE
from .coordinator import Fire2MqttCoordinator
from .data.rules import rules_for
from .entity import Fire2MqttEntity
from .state_detection import evaluate


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    user_rules = entry.options.get(CONF_STATE_DETECTION_RULES_OVERRIDE, {})
    async_add_entities([
        ScreenOnSensor(coordinator),
        PlayingSensor(coordinator, user_rules),
        ConnectivitySensor(coordinator),
    ])


class PlayingSensor(Fire2MqttEntity, BinarySensorEntity):
    """On while media is actively playing, off when paused/idle/stopped.

    Runs the playback payload through the same state-detection rules as the media player, so
    per-app fallbacks (e.g. Jellyfin's `audio_state`) apply here too. Rules are picked by the app
    that owns the playback, falling back to the foreground app.
    """

    _attr_name = "Playing"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:play-circle"

    def __init__(self, coordinator: Fire2MqttCoordinator, user_rules: dict) -> None:
        super().__init__(coordinator, "playing")
        self._user_rules = user_rules

    @property
    def is_on(self) -> bool:
        playback = self.coordinator.data.playback
        package = playback.get("app") or self.coordinator.data.app.get("package", "")
        return evaluate(rules_for(package, self._user_rules), playback) == "playing"


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
