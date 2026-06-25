"""Fire2MQTT update entity — surfaces an out-of-date APK and pushes the latest over ADB.

The APK reports its own ``app_version`` on ``state/device``; this entity compares it against the
integration's release version (they ship in lockstep) and, on Install, reinstalls the latest signed
APK over ADB using the Fire TV IP the device itself reported.
"""
from __future__ import annotations

import logging

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.loader import async_get_integration

from . import Fire2MqttConfigEntry
from .const import ADB_PORT, DOMAIN, GITHUB_RELEASES_URL
from .coordinator import Fire2MqttCoordinator
from .entity import Fire2MqttEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    # The integration's own version is the latest APK we'd push (lockstep releases).
    integration = await async_get_integration(hass, DOMAIN)
    async_add_entities([Fire2MqttApkUpdate(coordinator, str(integration.version))])


class Fire2MqttApkUpdate(Fire2MqttEntity, UpdateEntity):
    _attr_name = "App"
    _attr_supported_features = UpdateEntityFeature.INSTALL
    _attr_release_url = GITHUB_RELEASES_URL

    def __init__(self, coordinator: Fire2MqttCoordinator, latest_version: str) -> None:
        super().__init__(coordinator, "apk_update")
        self._attr_latest_version = latest_version

    @property
    def installed_version(self) -> str | None:
        """The APK version reported on state/device; None until the device reports it."""
        return self.coordinator.data.device_info.get("app_version") or None

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        host = self.coordinator.data.device_info.get("ip")
        if not host:
            raise HomeAssistantError(
                "Fire TV IP unknown — the device hasn't reported state/device yet."
            )
        # Imported here so adb_shell only loads when an update is actually pushed.
        from .adb_provision import ProvisionError, async_update_apk

        # If the APK's signing key changed, an in-place update is impossible and a clean
        # reinstall wipes the app's settings. Reconstruct the broker config (same source the
        # config flow prefills from) so the update can self-heal without user input.
        recovery_config = await self._async_recovery_config()
        try:
            await async_update_apk(self.hass, host, ADB_PORT, recovery_config=recovery_config)
        except ProvisionError as err:
            raise HomeAssistantError(f"APK update failed ({err.reason}): {err}") from err

    async def _async_recovery_config(self):
        """Rebuild the broker config from HA's MQTT integration + this entry, for use when a
        signing-key change forces a clean reinstall. Returns None if no MQTT broker is set up."""
        from .adb_provision import async_recovery_broker_config

        return await async_recovery_broker_config(
            self.hass, self.coordinator.device_id, self.coordinator.topic_prefix
        )
