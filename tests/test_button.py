"""Integration tests for the Fire2MQTT Launch button."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.fire2mqtt.adb_provision import ProvisionError, ProvisionResult
from custom_components.fire2mqtt.const import ADB_PORT
from tests.conftest import TOPIC_APPS, TOPIC_CMD_LAUNCH, TOPIC_DEVICE, TOPIC_STATUS

BUTTON = "button.fire_tv_test_device_launch_app"
REPROVISION = "button.fire_tv_test_device_re_provision_over_adb"
SELECT = "select.fire_tv_test_device_app_launcher"
INSTALLED = ["com.netflix.ninja", "org.jellyfin.androidtv"]


@pytest.fixture
async def online_with_apps(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await mock_mqtt_subscribe.deliver(TOPIC_APPS, json.dumps({"packages": INSTALLED, "ts": 1}))
    await hass.async_block_till_done()


async def _select(hass: HomeAssistant, option: str) -> None:
    await hass.services.async_call(
        "select", "select_option", {"entity_id": SELECT, "option": option}, blocking=True
    )


async def test_launch_button_launches_the_selected_app(
    hass: HomeAssistant, online_with_apps, mock_mqtt_publish
):
    await _select(hass, "Netflix")
    await hass.services.async_call("button", "press", {"entity_id": BUTTON}, blocking=True)
    assert (TOPIC_CMD_LAUNCH, "com.netflix.ninja") in mock_mqtt_publish.published


async def test_launch_button_without_a_selection_raises(hass: HomeAssistant, online_with_apps):
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("button", "press", {"entity_id": BUTTON}, blocking=True)


# ── Re-provision button ───────────────────────────────────────────────────────

async def test_reprovision_pushes_config_over_adb(
    hass: HomeAssistant, online_with_apps, mock_mqtt_subscribe
):
    await mock_mqtt_subscribe.deliver(
        TOPIC_DEVICE,
        json.dumps({"model": "Fire TV", "fire_os": "11", "ip": "10.0.0.88", "app_version": "0.4.1"}),
    )
    await hass.async_block_till_done()

    config = object()  # opaque; we only assert it's forwarded
    provision = AsyncMock(return_value=ProvisionResult(installed=False, launched=True))
    with (
        patch(
            "custom_components.fire2mqtt.adb_provision.async_recovery_broker_config",
            AsyncMock(return_value=config),
        ),
        patch("custom_components.fire2mqtt.adb_provision.async_provision", provision),
    ):
        await hass.services.async_call(
            "button", "press", {"entity_id": REPROVISION}, blocking=True
        )
    provision.assert_awaited_once_with(hass, "10.0.0.88", config, ADB_PORT)


async def test_reprovision_available_when_device_offline(
    hass: HomeAssistant, setup_integration, mock_mqtt_subscribe
):
    # Device is offline (LWT), but the ADB recovery button must stay usable — that's its job.
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "offline")
    await hass.async_block_till_done()
    assert hass.states.get(REPROVISION).state != "unavailable"


async def test_reprovision_without_device_ip_raises(hass: HomeAssistant, online_with_apps):
    # No state/device delivered → no IP to target.
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button", "press", {"entity_id": REPROVISION}, blocking=True
        )


async def test_reprovision_without_mqtt_broker_raises(
    hass: HomeAssistant, online_with_apps, mock_mqtt_subscribe
):
    await mock_mqtt_subscribe.deliver(
        TOPIC_DEVICE, json.dumps({"model": "Fire TV", "fire_os": "11", "ip": "10.0.0.88"})
    )
    await hass.async_block_till_done()

    with patch(
        "custom_components.fire2mqtt.adb_provision.async_recovery_broker_config",
        AsyncMock(return_value=None),  # no MQTT broker configured
    ):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                "button", "press", {"entity_id": REPROVISION}, blocking=True
            )


NOTIFY = "custom_components.fire2mqtt.button.persistent_notification.async_create"


async def _press_reprovision(hass: HomeAssistant, mock_mqtt_subscribe, provision: AsyncMock):
    await mock_mqtt_subscribe.deliver(
        TOPIC_DEVICE, json.dumps({"model": "Fire TV", "fire_os": "11", "ip": "10.0.0.88"})
    )
    await hass.async_block_till_done()
    with (
        patch(
            "custom_components.fire2mqtt.adb_provision.async_recovery_broker_config",
            AsyncMock(return_value=object()),
        ),
        patch("custom_components.fire2mqtt.adb_provision.async_provision", provision),
    ):
        await hass.services.async_call(
            "button", "press", {"entity_id": REPROVISION}, blocking=True
        )


async def test_reprovision_success_notifies(
    hass: HomeAssistant, online_with_apps, mock_mqtt_subscribe
):
    provision = AsyncMock(return_value=ProvisionResult(installed=True, launched=True))
    with patch(NOTIFY) as notify:
        await _press_reprovision(hass, mock_mqtt_subscribe, provision)
    notify.assert_called_once()
    message = notify.call_args.args[1]
    assert message.startswith("Done on 10.0.0.88.")
    assert "Installed the app" in message


async def test_reprovision_failure_notifies_and_raises(
    hass: HomeAssistant, online_with_apps, mock_mqtt_subscribe
):
    provision = AsyncMock(side_effect=ProvisionError("adb_unreachable", "timed out"))
    with patch(NOTIFY) as notify, pytest.raises(HomeAssistantError):
        await _press_reprovision(hass, mock_mqtt_subscribe, provision)
    notify.assert_called_once()
    assert notify.call_args.args[1].startswith("Failed: Re-provision failed (adb_unreachable)")


async def test_reprovision_results_share_one_notification(
    hass: HomeAssistant, online_with_apps, mock_mqtt_subscribe
):
    # A retry after a failure replaces the failure notice instead of stacking a second one.
    with patch(NOTIFY) as notify:
        with pytest.raises(HomeAssistantError):
            await _press_reprovision(
                hass, mock_mqtt_subscribe, AsyncMock(side_effect=ProvisionError("adb_auth", "x"))
            )
        await _press_reprovision(hass, mock_mqtt_subscribe, AsyncMock(return_value=ProvisionResult()))
    ids = {c.kwargs["notification_id"] for c in notify.call_args_list}
    assert len(notify.call_args_list) == 2 and len(ids) == 1
