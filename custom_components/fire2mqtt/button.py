"""Fire2MQTT button entities — the Launch button for the app-launcher select."""
from __future__ import annotations

import logging

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Fire2MqttConfigEntry
from .const import ADB_PORT
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
    async_add_entities([LaunchAppButton(coordinator), ReprovisionButton(coordinator)])


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


class ReprovisionButton(Fire2MqttEntity, ButtonEntity):
    """Re-pushes the broker config to the Fire TV over ADB and brings the service back up.

    Recovers a device whose stored config was lost or wrong — e.g. after a clean reinstall
    (signing-key change) wipes app data. Pulls the broker credentials from HA's MQTT
    integration, so there's nothing to retype on the TV.
    """

    _attr_name = "Re-provision over ADB"
    _attr_icon = "mdi:cog-refresh"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "reprovision")

    @property
    def available(self) -> bool:
        # Always available: this is an ADB recovery action that exists precisely for when the
        # device is offline/unresponsive over MQTT, so it must not inherit the LWT-based
        # availability. The press handler reports a clear error if the IP isn't known yet.
        return True

    async def async_press(self) -> None:
        # A button press shows nothing in HA on success, and a failure toast is easy to miss
        # (or absent when pressed from an automation), so report both as a notification.
        # One notification id per device: each press replaces the previous result.
        notification_id = f"fire2mqtt_reprovision_{self.coordinator.device_id}"
        title = f"Fire2MQTT: re-provision {self.coordinator.device_id}"
        try:
            message = await self._async_reprovision()
        except HomeAssistantError as err:
            persistent_notification.async_create(
                self.hass, f"Failed: {err}", title=title, notification_id=notification_id
            )
            raise
        persistent_notification.async_create(
            self.hass, message, title=title, notification_id=notification_id
        )

    async def _async_reprovision(self) -> str:
        """Run provisioning; return a success summary or raise HomeAssistantError."""
        host = self.coordinator.data.device_info.get("ip")
        if not host:
            raise HomeAssistantError(
                "Fire TV IP unknown — the device hasn't reported state/device yet."
            )
        # Imported here so adb_shell only loads when provisioning is actually run.
        from .adb_provision import (
            ProvisionError,
            async_provision,
            async_recovery_broker_config,
        )

        config = await async_recovery_broker_config(
            self.hass, self.coordinator.device_id, self.coordinator.topic_prefix
        )
        if config is None:
            raise HomeAssistantError(
                "No MQTT broker configured in Home Assistant — set up the MQTT "
                "integration first so its broker details can be pushed to the Fire TV."
            )
        try:
            result = await async_provision(self.hass, host, config, ADB_PORT)
        except ProvisionError as err:
            raise HomeAssistantError(f"Re-provision failed ({err.reason}): {err}") from err
        installed = "Installed the app" if result.installed else "App already installed"
        return (
            f"Done on {host}. {installed}, permissions granted, broker settings pushed and "
            "the app restarted. Its state should be back in Home Assistant within a minute."
        )
