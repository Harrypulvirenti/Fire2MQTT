"""Fire2MQTT config flow."""
from __future__ import annotations

import asyncio
import json
import logging
import re

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_PORT, CONF_USERNAME
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
    CONF_BROKER_HOST,
    CONF_BROKER_PASSWORD,
    CONF_BROKER_PORT,
    CONF_BROKER_USERNAME,
    CONF_DEVICE_ID,
    CONF_ENABLED_APPS,
    CONF_FIRE_TV_IP,
    CONF_IDLE_TIMEOUT,
    CONF_STATE_DETECTION_RULES_OVERRIDE,
    CONF_TOPIC_PREFIX,
    CONF_USE_TLS,
    DEFAULT_BROKER_PORT,
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


# Broker hostnames that only resolve on the HA host itself — a Fire TV across the LAN can't
# reach these, so we substitute HA's own LAN IP when the configured MQTT broker is one of them
# (the Mosquitto add-on registers as ``core-mosquitto``; a same-host broker as ``localhost``).
_LOCAL_ONLY_HOSTS = frozenset(
    {
        "",
        "localhost",
        "127.0.0.1",
        "::1",
        "core-mosquitto",
        "addon_core_mosquitto",
        "homeassistant",
        "homeassistant.local",
    }
)


async def _mqtt_broker_defaults(hass) -> dict:
    """Best-effort broker defaults for the provisioning form, taken from HA's own MQTT entry.

    The Fire TV is provisioned to talk to the same broker the user already set up in Home
    Assistant, so they never retype host/port/credentials. When that broker is only reachable
    on the HA box (``core-mosquitto``, ``localhost``, …) we swap in HA's LAN IP, which is the
    address the Fire TV must actually connect to. Returns only the keys we could resolve;
    every value is still editable in the form.
    """
    entries = hass.config_entries.async_entries("mqtt")
    if not entries:
        return {}
    data = entries[0].data
    host = data.get(mqtt.CONF_BROKER, "")
    if host in _LOCAL_ONLY_HOSTS:
        try:
            from homeassistant.components.network import async_get_source_ip

            host = await async_get_source_ip(hass)
        except Exception:  # noqa: BLE001 — IP discovery is best-effort; never block the form
            _LOGGER.debug("Could not resolve HA LAN IP for broker default", exc_info=True)
            host = ""
    defaults: dict = {}
    if host:
        defaults[CONF_BROKER_HOST] = host
    if (port := data.get(CONF_PORT)) is not None:
        defaults[CONF_BROKER_PORT] = port
    if username := data.get(CONF_USERNAME):
        defaults[CONF_BROKER_USERNAME] = username
    if password := data.get(CONF_PASSWORD):
        defaults[CONF_BROKER_PASSWORD] = password
    return defaults


class Fire2MqttConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._entry_data: dict | None = None
        self._provision_note: str | None = None

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """First step: decide how the APK gets onto the Fire TV before collecting config.

        The app must be installed (and, in the manual case, configured on-device) before
        Home Assistant can talk to it, so we offer the install choice up front and only
        gather MQTT/device details afterwards in :meth:`async_step_config`.
        """
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_not_configured")

        return self.async_show_menu(
            step_id="user",
            menu_options=["provision_adb", "manual_install"],
        )

    async def async_step_manual_install(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Acknowledge the APK is built, sideloaded, and launched."""
        if user_input is not None:
            return await self.async_step_manual_grant_permissions()

        return self.async_show_form(
            step_id="manual_install",
            data_schema=vol.Schema({}),
        )

    async def async_step_manual_grant_permissions(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Acknowledge WRITE_SECURE_SETTINGS has been granted over ADB."""
        if user_input is not None:
            return await self.async_step_manual_configure_app()

        return self.async_show_form(
            step_id="manual_grant_permissions",
            data_schema=vol.Schema({}),
        )

    async def async_step_manual_configure_app(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Acknowledge the app is configured with broker + device ID, then collect config."""
        if user_input is not None:
            return await self.async_step_config()

        return self.async_show_form(
            step_id="manual_configure_app",
            data_schema=vol.Schema({}),
        )

    async def async_step_config(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Collect device name/ID/topic prefix and create the entry (post-install)."""
        errors: dict[str, str] = {}
        status_topic = ""

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
                    status_topic = TOPIC_STATUS.format(prefix=prefix, device_id=device_id)
                    # Non-fatal: user can continue, state will populate when APK starts
                    if user_input.get("_force_continue"):
                        errors = {}

                if not errors:
                    self._entry_data = {
                        "title": user_input.get("device_name", device_id),
                        CONF_DEVICE_ID: device_id,
                        CONF_TOPIC_PREFIX: prefix,
                    }
                    return self._create_entry(self._provision_note)

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
            step_id="config",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "mqtt_schema_url": "https://github.com/Harrypulvirenti/Fire2MQTT/blob/main/docs/mqtt-schema.md",
                "status_topic": status_topic,
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

    async def async_step_provision_adb(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """One comprehensive ADB step: install the APK, grant WRITE_SECURE_SETTINGS, push the
        broker config to the app, and create the entry — all from a single form, since
        injecting the config means we already have the device id + prefix here."""
        errors: dict[str, str] = {}
        # `detail` is always supplied so the form's {detail} placeholder renders on the
        # first (error-free) pass too; it's filled in only when provisioning fails.
        description_placeholders: dict[str, str] = {"detail": ""}

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

                # Imported here so the adb_shell dependency only loads when provisioning is used.
                from .adb_provision import BrokerConfig, ProvisionError, async_provision

                config = BrokerConfig(
                    host=user_input[CONF_BROKER_HOST],
                    port=int(user_input.get(CONF_BROKER_PORT, DEFAULT_BROKER_PORT)),
                    username=user_input.get(CONF_BROKER_USERNAME, ""),
                    password=user_input.get(CONF_BROKER_PASSWORD, ""),
                    device_id=device_id,
                    topic_prefix=prefix,
                    use_tls=user_input.get(CONF_USE_TLS, False),
                )
                try:
                    result = await async_provision(
                        self.hass, user_input[CONF_FIRE_TV_IP], config, ADB_PORT
                    )
                except ProvisionError as err:
                    errors["base"] = err.reason
                    description_placeholders["detail"] = str(err)
                else:
                    self._entry_data = {
                        "title": user_input.get("device_name", device_id),
                        CONF_DEVICE_ID: device_id,
                        CONF_TOPIC_PREFIX: prefix,
                    }
                    summary = "Installed" if result.installed else "Already installed"
                    return self._create_entry(
                        f"{summary}; WRITE_SECURE_SETTINGS granted; broker config pushed; "
                        "app launched to self-enable accessibility + notification access."
                    )

        suggested = user_input or {}
        # Prefill the broker fields from HA's own MQTT integration so the user doesn't retype
        # what they already configured. A re-shown form (after an error) keeps the user's edits,
        # so user_input takes precedence over the detected defaults.
        detected = await _mqtt_broker_defaults(self.hass)

        def _broker_default(key, fallback):
            return suggested.get(key, detected.get(key, fallback))

        # Only attach a default when we actually detected a host; otherwise keep the field a
        # bare Required so the form still forces the user to supply one.
        broker_host = _broker_default(CONF_BROKER_HOST, None)
        host_key = (
            vol.Required(CONF_BROKER_HOST, default=broker_host)
            if broker_host
            else vol.Required(CONF_BROKER_HOST)
        )

        schema = vol.Schema({
            vol.Required(CONF_FIRE_TV_IP): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required("device_name", default="Living Room Fire TV"): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_DEVICE_ID, default=_slug(
                suggested.get("device_name", "living_room_fire_tv")
            )): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            host_key: TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Optional(
                CONF_BROKER_PORT,
                default=_broker_default(CONF_BROKER_PORT, DEFAULT_BROKER_PORT),
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=65535, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_BROKER_USERNAME,
                default=_broker_default(CONF_BROKER_USERNAME, ""),
            ): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Optional(
                CONF_BROKER_PASSWORD,
                default=_broker_default(CONF_BROKER_PASSWORD, ""),
            ): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
            vol.Optional(CONF_USE_TLS, default=False): bool,
            vol.Optional(CONF_TOPIC_PREFIX, default=DEFAULT_TOPIC_PREFIX): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
        })

        return self.async_show_form(
            step_id="provision_adb",
            data_schema=schema,
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
