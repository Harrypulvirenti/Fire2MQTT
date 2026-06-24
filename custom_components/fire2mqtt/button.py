"""Fire2MQTT button entities — the Launch button for the app-launcher select."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Fire2MqttConfigEntry
from .coordinator import Fire2MqttCoordinator
from .data.apps import installed_curated
from .entity import Fire2MqttEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([LaunchAppButton(coordinator)])


class LaunchAppButton(Fire2MqttEntity, ButtonEntity):
    """Launches the app currently chosen in the App launcher select."""

    _attr_name = "Launch app"
    _attr_icon = "mdi:rocket-launch"

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        # Note: unique suffix avoids the legacy "launch_<app>" prefix that
        # __init__._purge_legacy_buttons cleans up.
        super().__init__(coordinator, "app_launch")

    async def async_press(self) -> None:
        key = self.coordinator.selected_app_key
        matched = installed_curated(self.coordinator.data.installed_packages)
        if key is None or key not in matched:
            raise HomeAssistantError(
                "No installed app selected — pick one in the App launcher select first."
            )
        _info, launch_package = matched[key]
        await self.coordinator.async_launch_app(launch_package)
