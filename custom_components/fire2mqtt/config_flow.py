"""Fire2MQTT config flow."""
from __future__ import annotations

import asyncio
import json
import logging
import re

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    ADB_PORT,
    CONF_DEVICE_ID,
    CONF_ENABLED_APPS,
    CONF_FIRE_TV_IP,
    CONF_IDLE_TIMEOUT,
    CONF_STATE_DETECTION_RULES_OVERRIDE,
    CONF_TOPIC_PREFIX,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    TOPIC_STATUS,
)
from .data.apps import CURATED_APPS

_LOGGER = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"^[a-z0-9_]+$")
# MQTT-safe prefix: path segments of [A-Za-z0-9_-], no leading/trailing slash,
# and crucially no wildcards (+/#) so a crafted prefix can't subscribe broadly.
_PREFIX_RE = re.compile(r"^[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*$")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


class Fire2MqttConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._entry_data: dict | None = None

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_not_configured")

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            prefix = user_input.get(CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX)
            if not _SLUG_RE.match(device_id):
                errors[CONF_DEVICE_ID] = "invalid_device_id"
            elif not _PREFIX_RE.match(prefix):
                errors[CONF_TOPIC_PREFIX] = "invalid_topic_prefix"
            else:
                await self.async_set_unique_id(f"{DOMAIN}_{device_id}")
                self._abort_if_unique_id_configured()

                # Brief check: is the APK already publishing?
                apk_online = await self._check_apk_reachable(prefix, device_id)
                if not apk_online:
                    errors["base"] = "apk_not_reachable"
                    # Non-fatal: user can continue, state will populate when APK starts
                    if user_input.get("_force_continue"):
                        errors = {}

                if not errors:
                    self._entry_data = {
                        "title": user_input.get("device_name", device_id),
                        CONF_DEVICE_ID: device_id,
                        CONF_TOPIC_PREFIX: prefix,
                    }
                    return await self.async_step_provision()

        schema = vol.Schema({
            vol.Required("device_name", default="Living Room Fire TV"): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_DEVICE_ID, default=_slug(
                (user_input or {}).get("device_name", "living_room_fire_tv")
            )): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Optional(CONF_TOPIC_PREFIX, default=DEFAULT_TOPIC_PREFIX): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
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

    async def async_step_reconfigure(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Allow changing the MQTT topic prefix without removing the device."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            prefix = user_input[CONF_TOPIC_PREFIX]
            if not _PREFIX_RE.match(prefix):
                errors[CONF_TOPIC_PREFIX] = "invalid_topic_prefix"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_TOPIC_PREFIX: prefix},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_TOPIC_PREFIX,
                    default=entry.data.get(CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            }),
            errors=errors,
            description_placeholders={
                CONF_DEVICE_ID: entry.data[CONF_DEVICE_ID],
            },
        )

    async def _check_apk_reachable(self, prefix: str, device_id: str) -> bool:
        """Subscribe to LWT topic for up to 4 seconds; return True if 'online' received."""
        topic = TOPIC_STATUS.format(prefix=prefix, device_id=device_id)
        result: asyncio.Future[bool] = self.hass.loop.create_future()

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

    async def async_step_provision(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Offer optional one-time ADB provisioning of the Fire TV, or finish."""
        return self.async_show_menu(
            step_id="provision",
            menu_options=["provision_adb", "finish"],
        )

    async def async_step_finish(self, user_input: dict | None = None) -> ConfigFlowResult:
        return self._create_entry()

    async def async_step_provision_adb(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Install the APK + grant WRITE_SECURE_SETTINGS over ADB, then create the entry."""
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}

        if user_input is not None:
            # Imported here so the adb_shell dependency only loads when provisioning is used.
            from .adb_provision import ProvisionError, async_provision

            try:
                result = await async_provision(
                    self.hass, user_input[CONF_FIRE_TV_IP], ADB_PORT
                )
            except ProvisionError as err:
                errors["base"] = err.reason
                description_placeholders["detail"] = str(err)
            else:
                summary = "Installed" if result.installed else "Already installed"
                return self._create_entry(
                    f"{summary}; WRITE_SECURE_SETTINGS granted; app launched to self-enable "
                    "accessibility + notification access."
                )

        return self.async_show_form(
            step_id="provision_adb",
            data_schema=vol.Schema({
                vol.Required(CONF_FIRE_TV_IP): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }),
            errors=errors,
            description_placeholders=description_placeholders,
        )

    def _create_entry(self, provision_note: str | None = None) -> ConfigFlowResult:
        assert self._entry_data is not None
        if provision_note:
            _LOGGER.info("Fire2MQTT provisioning: %s", provision_note)
        return self.async_create_entry(
            title=self._entry_data["title"],
            data={
                CONF_DEVICE_ID: self._entry_data[CONF_DEVICE_ID],
                CONF_TOPIC_PREFIX: self._entry_data[CONF_TOPIC_PREFIX],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return Fire2MqttOptionsFlow()


def _validate_rules_override(raw: str) -> dict:
    """Parse and shape-check a user-supplied rules-override JSON string.

    Raises ValueError if it isn't a {package: [rule, ...]} mapping in
    python-androidtv's state_detection_rules format.
    """
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("rules override must be a JSON object")
    for package, rules in parsed.items():
        if not isinstance(package, str) or not isinstance(rules, list):
            raise ValueError(f"rules for {package!r} must be a list")
        for rule in rules:
            if isinstance(rule, str):
                continue
            if isinstance(rule, dict) and all(
                isinstance(state, str) and isinstance(conditions, dict)
                for state, conditions in rule.items()
            ):
                continue
            raise ValueError(f"invalid rule {rule!r} for {package!r}")
    return parsed


class Fire2MqttOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            rules_raw = user_input.pop(CONF_STATE_DETECTION_RULES_OVERRIDE, "").strip()
            rules_override: dict = {}
            if rules_raw:
                try:
                    rules_override = _validate_rules_override(rules_raw)
                except (ValueError, json.JSONDecodeError):
                    errors[CONF_STATE_DETECTION_RULES_OVERRIDE] = "invalid_rules_override"
            if not errors:
                data = dict(user_input)
                if rules_override:
                    data[CONF_STATE_DETECTION_RULES_OVERRIDE] = rules_override
                return self.async_create_entry(data=data)

        current = self.config_entry.options
        app_options = [
            SelectOptionDict(value=key, label=info.friendly_name)
            for key, info in CURATED_APPS.items()
        ]
        current_rules = current.get(CONF_STATE_DETECTION_RULES_OVERRIDE, {})

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
            vol.Optional(
                CONF_STATE_DETECTION_RULES_OVERRIDE,
                description={
                    "suggested_value": json.dumps(current_rules) if current_rules else ""
                },
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)),
        })

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
