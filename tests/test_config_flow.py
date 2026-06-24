"""Tests for the Fire2MQTT config flow and options flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fire2mqtt.config_flow import Fire2MqttConfigFlow
from custom_components.fire2mqtt.const import (
    CONF_BROKER_HOST,
    CONF_BROKER_PASSWORD,
    CONF_BROKER_PORT,
    CONF_BROKER_USERNAME,
    CONF_DEVICE_ID,
    CONF_ENABLED_APPS,
    CONF_FIRE_TV_IP,
    CONF_IDLE_TIMEOUT,
    CONF_TOPIC_PREFIX,
    CONF_USE_TLS,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)
from custom_components.fire2mqtt.data.apps import CURATED_APPS


# ── helpers ──────────────────────────────────────────────────────────────────

def _patch_mqtt_client(available: bool = True):
    return patch(
        "homeassistant.components.mqtt.async_wait_for_mqtt_client",
        AsyncMock(return_value=available),
    )


def _patch_apk_check(online: bool = True):
    return patch.object(
        Fire2MqttConfigFlow,
        "_check_apk_reachable",
        AsyncMock(return_value=online),
    )


def _schema_defaults(result) -> dict:
    """Extract {key: default value} from a returned form's voluptuous schema."""
    return {
        marker.schema: marker.default()
        for marker in result["data_schema"].schema
        if getattr(marker, "default", vol.UNDEFINED) is not vol.UNDEFINED
    }


def _add_mqtt_entry(hass: HomeAssistant, **data) -> MockConfigEntry:
    """Register a fake HA MQTT config entry so the provisioning form can read its broker."""
    entry = MockConfigEntry(domain="mqtt", data=data)
    entry.add_to_hass(hass)
    return entry


VALID_INPUT = {
    "device_name": "Living Room",
    CONF_DEVICE_ID: "living_room",
    CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
}

# The comprehensive one-form ADB branch collects device + broker fields together.
PROVISION_INPUT = {
    CONF_FIRE_TV_IP: "10.0.0.50",
    "device_name": "Living Room",
    CONF_DEVICE_ID: "living_room",
    CONF_BROKER_HOST: "192.168.1.10",
    CONF_BROKER_PORT: 1883,
    CONF_BROKER_USERNAME: "user",
    CONF_BROKER_PASSWORD: "pass",
    CONF_USE_TLS: False,
    CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
}


# ── config flow ──────────────────────────────────────────────────────────────

async def _advance_to_config_form(hass: HomeAssistant) -> str:
    """Drive user (install-choice menu) → manual_install → config form; return flow_id."""
    with _patch_mqtt_client():
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        flow_id = list(hass.config_entries.flow.async_progress())[0]["flow_id"]
        await hass.config_entries.flow.async_configure(
            flow_id, user_input={"next_step_id": "manual_install"}
        )
        result = await hass.config_entries.flow.async_configure(flow_id, user_input={})
    assert result["type"] == "form"
    assert result["step_id"] == "config"
    return flow_id


async def test_install_menu_shown_on_init(hass: HomeAssistant):
    with _patch_mqtt_client():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
    assert result["type"] == "menu"
    assert result["step_id"] == "user"
    assert set(result["menu_options"]) == {"provision_adb", "manual_install"}


async def test_aborts_when_mqtt_not_configured(hass: HomeAssistant):
    with _patch_mqtt_client(available=False):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
    assert result["type"] == "abort"
    assert result["reason"] == "mqtt_not_configured"


async def test_manual_install_leads_to_config_form(hass: HomeAssistant):
    flow_id = await _advance_to_config_form(hass)
    assert flow_id  # reaching the config form is the assertion (made in the helper)


async def test_invalid_device_id_shows_error(hass: HomeAssistant):
    flow_id = await _advance_to_config_form(hass)
    with _patch_apk_check():
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={**VALID_INPUT, CONF_DEVICE_ID: "Has Spaces!"},
        )
    assert result["type"] == "form"
    assert result["errors"].get(CONF_DEVICE_ID) == "invalid_device_id"


async def test_manual_install_valid_config_creates_entry(hass: HomeAssistant):
    flow_id = await _advance_to_config_form(hass)
    with _patch_apk_check(online=True):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input=VALID_INPUT,
        )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_DEVICE_ID] == "living_room"
    assert result["data"][CONF_TOPIC_PREFIX] == DEFAULT_TOPIC_PREFIX
    assert result["title"] == "Living Room"


async def test_apk_not_reachable_shows_error(hass: HomeAssistant):
    flow_id = await _advance_to_config_form(hass)
    with _patch_apk_check(online=False):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input=VALID_INPUT,
        )
    assert result["type"] == "form"
    assert result["errors"].get("base") == "apk_not_reachable"


async def test_force_continue_bypasses_apk_error(hass: HomeAssistant):
    flow_id = await _advance_to_config_form(hass)

    # Step 1: first submit → APK offline → form re-shown with _force_continue field
    with _patch_apk_check(online=False):
        result = await hass.config_entries.flow.async_configure(flow_id, user_input=VALID_INPUT)
    assert result["type"] == "form"
    assert result["errors"].get("base") == "apk_not_reachable"

    # Step 2: re-submit with _force_continue=True → entry created (offline APK bypassed)
    with _patch_apk_check(online=False):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={**VALID_INPUT, "_force_continue": True}
        )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_DEVICE_ID] == "living_room"


async def test_duplicate_device_id_aborts(hass: HomeAssistant):
    existing = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{DOMAIN}_living_room",
        data={CONF_DEVICE_ID: "living_room", CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX},
    )
    existing.add_to_hass(hass)

    flow_id = await _advance_to_config_form(hass)
    with _patch_apk_check(online=True):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input=VALID_INPUT,
        )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


# ── ADB provisioning step ─────────────────────────────────────────────────────

async def _advance_to_provision_form(hass: HomeAssistant) -> dict:
    """Drive the flow through user menu → provision_adb form; return the form result."""
    with _patch_mqtt_client():
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        flow_id = list(hass.config_entries.flow.async_progress())[0]["flow_id"]
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={"next_step_id": "provision_adb"}
        )
    assert result["type"] == "form"
    assert result["step_id"] == "provision_adb"
    return result


async def test_provision_adb_success_creates_entry(hass: HomeAssistant):
    from custom_components.fire2mqtt.adb_provision import BrokerConfig, ProvisionResult

    flow_id = (await _advance_to_provision_form(hass))["flow_id"]
    mock = AsyncMock(return_value=ProvisionResult(installed=True, write_secure_settings=True))
    with patch("custom_components.fire2mqtt.adb_provision.async_provision", mock):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input=PROVISION_INPUT
        )
    # The comprehensive form provisions and creates the entry in one shot.
    assert result["type"] == "create_entry"
    assert result["data"][CONF_DEVICE_ID] == "living_room"
    assert result["data"][CONF_TOPIC_PREFIX] == DEFAULT_TOPIC_PREFIX

    # The broker config was forwarded to provisioning (args: hass, ip, config, port).
    config = mock.call_args.args[2]
    assert isinstance(config, BrokerConfig)
    assert config.host == "192.168.1.10"
    assert config.device_id == "living_room"
    assert config.use_tls is False


async def test_provision_adb_invalid_device_id_shows_error(hass: HomeAssistant):
    flow_id = (await _advance_to_provision_form(hass))["flow_id"]
    result = await hass.config_entries.flow.async_configure(
        flow_id, user_input={**PROVISION_INPUT, CONF_DEVICE_ID: "Bad ID!"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "provision_adb"
    assert result["errors"].get(CONF_DEVICE_ID) == "invalid_device_id"


async def test_provision_adb_error_reshows_form(hass: HomeAssistant):
    from custom_components.fire2mqtt.adb_provision import ProvisionError

    flow_id = (await _advance_to_provision_form(hass))["flow_id"]
    with patch(
        "custom_components.fire2mqtt.adb_provision.async_provision",
        AsyncMock(side_effect=ProvisionError("adb_unreachable", "timeout")),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input=PROVISION_INPUT
        )
    assert result["type"] == "form"
    assert result["step_id"] == "provision_adb"
    assert result["errors"].get("base") == "adb_unreachable"


async def test_provision_form_prefills_broker_from_mqtt_entry(hass: HomeAssistant):
    """The form defaults host/port/username/password from HA's existing MQTT entry."""
    _add_mqtt_entry(
        hass, broker="192.168.1.50", port=1884, username="mq", password="secret"
    )
    result = await _advance_to_provision_form(hass)
    defaults = _schema_defaults(result)
    assert defaults[CONF_BROKER_HOST] == "192.168.1.50"
    assert defaults[CONF_BROKER_PORT] == 1884
    assert defaults[CONF_BROKER_USERNAME] == "mq"
    assert defaults[CONF_BROKER_PASSWORD] == "secret"


async def test_provision_form_substitutes_lan_ip_for_local_broker(hass: HomeAssistant):
    """A broker only reachable on the HA host (core-mosquitto) becomes HA's LAN IP."""
    _add_mqtt_entry(hass, broker="core-mosquitto", port=1883)
    with patch(
        "homeassistant.components.network.async_get_source_ip",
        AsyncMock(return_value="10.0.0.7"),
    ):
        result = await _advance_to_provision_form(hass)
    assert _schema_defaults(result)[CONF_BROKER_HOST] == "10.0.0.7"


async def test_provision_form_host_stays_required_without_mqtt_entry(hass: HomeAssistant):
    """With no MQTT entry to learn from, the host field keeps no default (stays required)."""
    result = await _advance_to_provision_form(hass)
    assert CONF_BROKER_HOST not in _schema_defaults(result)


# ── options flow ──────────────────────────────────────────────────────────────

@pytest.fixture
def config_entry_with_options(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE_ID: "living_room", CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX},
        options={
            CONF_ENABLED_APPS: list(CURATED_APPS.keys()),
            CONF_IDLE_TIMEOUT: DEFAULT_IDLE_TIMEOUT,
        },
    )
    entry.add_to_hass(hass)
    return entry


async def test_options_flow_shows_form(hass: HomeAssistant, config_entry_with_options):
    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_options_flow_saves_selection(hass: HomeAssistant, config_entry_with_options):
    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ENABLED_APPS: ["netflix", "jellyfin"],
            CONF_IDLE_TIMEOUT: 5,
        },
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENABLED_APPS] == ["netflix", "jellyfin"]
    assert result["data"][CONF_IDLE_TIMEOUT] == 5


async def test_invalid_topic_prefix_shows_error(hass: HomeAssistant):
    flow_id = await _advance_to_config_form(hass)
    with _patch_apk_check():
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={**VALID_INPUT, CONF_TOPIC_PREFIX: "bad/#/prefix"},
        )
    assert result["type"] == "form"
    assert result["errors"].get(CONF_TOPIC_PREFIX) == "invalid_topic_prefix"


async def test_nested_topic_prefix_accepted(hass: HomeAssistant):
    flow_id = await _advance_to_config_form(hass)
    with _patch_apk_check(online=True):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={**VALID_INPUT, CONF_TOPIC_PREFIX: "home/media/fire2mqtt"},
        )
    assert result["type"] == "create_entry"


# ── reconfigure flow ──────────────────────────────────────────────────────────

async def test_reconfigure_updates_topic_prefix(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{DOMAIN}_living_room",
        data={CONF_DEVICE_ID: "living_room", CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] == "form"
    assert result["step_id"] == "reconfigure"

    with _patch_mqtt_client():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_TOPIC_PREFIX: "newprefix"}
        )
    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_TOPIC_PREFIX] == "newprefix"
    assert entry.data[CONF_DEVICE_ID] == "living_room"


async def test_reconfigure_rejects_invalid_prefix(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{DOMAIN}_living_room",
        data={CONF_DEVICE_ID: "living_room", CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOPIC_PREFIX: "nope+wild"}
    )
    assert result["type"] == "form"
    assert result["errors"].get(CONF_TOPIC_PREFIX) == "invalid_topic_prefix"


# ── options: state detection rules override ──────────────────────────────────

async def test_options_flow_accepts_rules_override(hass: HomeAssistant, config_entry_with_options):
    from custom_components.fire2mqtt.const import CONF_STATE_DETECTION_RULES_OVERRIDE

    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ENABLED_APPS: ["netflix"],
            CONF_IDLE_TIMEOUT: 10,
            CONF_STATE_DETECTION_RULES_OVERRIDE: '{"com.netflix.ninja": [{"playing": {"media_session_state": 3}}, "idle"]}',
        },
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_STATE_DETECTION_RULES_OVERRIDE] == {
        "com.netflix.ninja": [{"playing": {"media_session_state": 3}}, "idle"]
    }


async def test_options_flow_rejects_bad_rules_override(hass: HomeAssistant, config_entry_with_options):
    from custom_components.fire2mqtt.const import CONF_STATE_DETECTION_RULES_OVERRIDE

    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ENABLED_APPS: ["netflix"],
            CONF_IDLE_TIMEOUT: 10,
            CONF_STATE_DETECTION_RULES_OVERRIDE: '["not", "a", "mapping"]',
        },
    )
    assert result["type"] == "form"
    assert result["errors"].get(CONF_STATE_DETECTION_RULES_OVERRIDE) == "invalid_rules_override"


async def test_options_flow_empty_rules_override_omitted(hass: HomeAssistant, config_entry_with_options):
    from custom_components.fire2mqtt.const import CONF_STATE_DETECTION_RULES_OVERRIDE

    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLED_APPS: ["netflix"], CONF_IDLE_TIMEOUT: 10},
    )
    assert result["type"] == "create_entry"
    assert CONF_STATE_DETECTION_RULES_OVERRIDE not in result["data"]
