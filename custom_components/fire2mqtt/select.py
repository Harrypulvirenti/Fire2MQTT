"""Fire2MQTT select entity — a single app launcher.

Replaces the old per-app launch buttons. Its options are the curated apps the
device actually reports as installed (``state/apps``), optionally narrowed by the
``enabled_apps`` option. Selecting an option launches that app on the Fire TV.
"""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Fire2MqttConfigEntry
from .const import CONF_ENABLED_APPS
from .coordinator import Fire2MqttCoordinator
from .data.apps import CURATED_APPS, PACKAGE_TO_KEY, installed_curated
from .entity import Fire2MqttEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    enabled_keys: list[str] = entry.options.get(CONF_ENABLED_APPS, list(CURATED_APPS.keys()))
    async_add_entities([Fire2MqttAppLauncherSelect(coordinator, enabled_keys)])


class Fire2MqttAppLauncherSelect(Fire2MqttEntity, SelectEntity):
    _attr_name = "App launcher"
    _attr_icon = "mdi:apps"

    def __init__(
        self,
        coordinator: Fire2MqttCoordinator,
        enabled_keys: list[str],
    ) -> None:
        super().__init__(coordinator, "app_launcher")
        self._enabled_keys = set(enabled_keys)

    def _matched(self) -> dict[str, tuple]:
        """Curated+installed apps, narrowed to the ones enabled in options."""
        matched = installed_curated(self.coordinator.data.installed_packages)
        return {key: val for key, val in matched.items() if key in self._enabled_keys}

    @property
    def options(self) -> list[str]:
        return sorted(info.friendly_name for info, _pkg in self._matched().values())

    @property
    def current_option(self) -> str | None:
        """Reflect the foreground app when it's one of the launchable options."""
        package = self.coordinator.data.app.get("package", "")
        key = PACKAGE_TO_KEY.get(package)
        if key is None or key not in self._matched():
            return None
        name = CURATED_APPS[key].friendly_name
        return name if name in self.options else None

    async def async_select_option(self, option: str) -> None:
        for info, launch_package in self._matched().values():
            if info.friendly_name == option:
                await self.coordinator.async_launch_app(launch_package)
                return
        _LOGGER.warning("Fire2MQTT: unknown app launcher option %r", option)
