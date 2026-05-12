"""Fire2MQTT config flow."""
from __future__ import annotations

import asyncio
import logging
import re

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_DEVICE_ID,
    CONF_ENABLED_APPS,
    CONF_IDLE_TIMEOUT,
    CONF_TOPIC_PREFIX,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    TOPIC_STATUS,
)
from .data.apps import CURATED_APPS

_LOGGER = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"^[a-z0-9_]+$")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


class Fire2MqttConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_not_configured")

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            if not _SLUG_RE.match(device_id):
                errors[CONF_DEVICE_ID] = "invalid_device_id"
            else:
                await self.async_set_unique_id(f"{DOMAIN}_{device_id}")
                self._abort_if_unique_id_configured()

                # Brief check: is the APK already publishing?
                apk_online = await self._check_apk_reachable(
                    user_input.get(CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX),
                    device_id,
                )
                if not apk_online:
                    errors["base"] = "apk_not_reachable"
                    # Non-fatal: user can continue, state will populate when APK starts
                    if user_input.get("_force_continue"):
                        errors = {}

                if not errors:
                    return self.async_create_entry(
                        title=user_input.get("device_name", device_id),
                        data={
                            CONF_DEVICE_ID: device_id,
                            CONF_TOPIC_PREFIX: user_input.get(CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX),
                        },
                    )

        schema = vol.Schema({
            vol.Required("device_name", default="Living Room Fire TV"): TextSelector(
                TextSelectorConfig(type="text")
            ),
            vol.Required(CONF_DEVICE_ID, default=_slug(
                (user_input or {}).get("device_name", "living_room_fire_tv")
            )): TextSelector(TextSelectorConfig(type="text")),
            vol.Optional(CONF_TOPIC_PREFIX, default=DEFAULT_TOPIC_PREFIX): TextSelector(
                TextSelectorConfig(type="text")
            ),
        })

        if errors.get("base") == "apk_not_reachable":
            schema = schema.extend({
                vol.Optional("_force_continue", default=False): bool,
            })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "mqtt_schema_url": "https://github.com/Harrypulvirenti/Fire2MQTT/blob/main/docs/mqtt-schema.md"
            },
        )

    async def _check_apk_reachable(self, prefix: str, device_id: str) -> bool:
        """Subscribe to LWT topic for up to 4 seconds; return True if 'online' received."""
        topic = TOPIC_STATUS.format(prefix=prefix, device_id=device_id)
        result: asyncio.Future[bool] = asyncio.get_event_loop().create_future()

        @callback
        def _on_status(msg: mqtt.ReceiveMessage) -> None:
            if not result.done():
                result.set_result(msg.payload.strip().lower() == "online")

        unsub = await mqtt.async_subscribe(self.hass, topic, _on_status)
        try:
            return await asyncio.wait_for(asyncio.shield(result), timeout=4.0)
        except asyncio.TimeoutError:
            return False
        finally:
            unsub()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return Fire2MqttOptionsFlow(config_entry)


class Fire2MqttOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self._config_entry.options
        app_options = [
            SelectOptionDict(value=key, label=info.friendly_name)
            for key, info in CURATED_APPS.items()
        ]

        schema = vol.Schema({
            vol.Optional(
                CONF_ENABLED_APPS,
                default=current.get(CONF_ENABLED_APPS, list(CURATED_APPS.keys())),
            ): SelectSelector(SelectSelectorConfig(
                options=app_options,
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )),
            vol.Optional(
                CONF_IDLE_TIMEOUT,
                default=current.get(CONF_IDLE_TIMEOUT, DEFAULT_IDLE_TIMEOUT),
            ): NumberSelector(NumberSelectorConfig(
                min=1, max=120, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="min"
            )),
        })

        return self.async_show_form(step_id="init", data_schema=schema)
