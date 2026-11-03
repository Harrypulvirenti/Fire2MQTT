"""Tests for the optional ADB provisioning module."""
from __future__ import annotations

import shlex
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.fire2mqtt.adb_provision import (
    BrokerConfig,
    ProvisionError,
    _build_launch_cmd,
    async_provision,
    async_update_apk,
)
from custom_components.fire2mqtt.const import FIRE2MQTT_LAUNCH_COMPONENT, FIRE2MQTT_PACKAGE


def _cfg(**overrides) -> BrokerConfig:
    base = dict(
        host="192.168.1.10",
        port=1883,
        username="user",
        password="pass",
        device_id="living_room",
        topic_prefix="fire2mqtt",
        use_tls=False,
    )
    base.update(overrides)
    return BrokerConfig(**base)


def _fake_device(shell_map: dict[str, str]) -> MagicMock:
    """Build a fake AdbDeviceTcpAsync whose shell() returns canned output by substring match."""
    device = MagicMock()
    device.connect = AsyncMock()
    device.close = AsyncMock()
    device.push = AsyncMock()

    async def _shell(cmd: str, *args, **kwargs) -> str:
        for needle, out in shell_map.items():
            if needle in cmd:
                return out
        return ""

    device.shell = AsyncMock(side_effect=_shell)
    return device


@pytest.fixture
def _patch_adb_imports():
    """Patch the lazily-imported adb_shell symbols inside async_provision."""
    device_holder: dict = {}

    class _FakeTcp:
        def __init__(self, *a, **k):
            self._d = device_holder["device"]

        def __new__(cls, *a, **k):  # return the prebuilt fake instead of a real device
            return device_holder["device"]

    with patch.dict(
        "sys.modules",
        {
            "adb_shell.adb_device_async": MagicMock(AdbDeviceTcpAsync=_FakeTcp),
            "adb_shell.auth.keygen": MagicMock(keygen=MagicMock()),
            "adb_shell.auth.sign_pythonrsa": MagicMock(
                PythonRSASigner=MagicMock(FromRSAKeyPath=MagicMock(return_value="signer"))
            ),
            "adb_shell.exceptions": MagicMock(
                DeviceAuthError=type("DeviceAuthError", (Exception,), {}),
                TcpTimeoutException=type("TcpTimeoutException", (Exception,), {}),
            ),
        },
    ):
        yield device_holder


async def test_provision_already_installed_grants_and_launches(
    hass: HomeAssistant, _patch_adb_imports
):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": f"android.permission.WRITE_SECURE_SETTINGS: granted=true",
    })
    _patch_adb_imports["device"] = device

    result = await async_provision(hass, "10.0.0.50", _cfg())

    assert result.installed is False
    assert result.write_secure_settings is True
    assert result.launched is True
    device.push.assert_not_called()
    # The launch carries the broker config as extras.
    launch = next(c.args[0] for c in device.shell.call_args_list if "am start" in c.args[0])
    assert "--es broker_host 192.168.1.10" in launch
    assert "--es device_id living_room" in launch
    # The notification listener is bound (via the NMS grant API) BEFORE launch, so the app's
    # MediaSessionWatcher can register on first start — required for media state on Fire OS.
    calls = [c.args[0] for c in device.shell.call_args_list]
    allow_idx = next(i for i, c in enumerate(calls) if "cmd notification allow_listener" in c)
    launch_idx = next(i for i, c in enumerate(calls) if "am start" in c)
    assert allow_idx < launch_idx


_LISTENER = f"{FIRE2MQTT_PACKAGE}/{FIRE2MQTT_PACKAGE}.media.MediaNotificationListener"
_USAGE_GRANT = f"appops set {FIRE2MQTT_PACKAGE} GET_USAGE_STATS allow"


async def test_provision_grants_usage_access_before_launch(
    hass: HomeAssistant, _patch_adb_imports
):
    """Fire OS 6.7 refuses our accessibility service; Current App falls back to usage stats."""
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=true",
    })
    _patch_adb_imports["device"] = device

    await async_provision(hass, "10.0.0.50", _cfg())

    calls = [c.args[0] for c in device.shell.call_args_list]
    assert calls.index(_USAGE_GRANT) < next(i for i, c in enumerate(calls) if "am start" in c)


async def test_provision_usage_access_error_does_not_fail(
    hass: HomeAssistant, _patch_adb_imports
):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=true",
        "appops set": "Error: Unknown operation string: GET_USAGE_STATS",
    })
    _patch_adb_imports["device"] = device

    result = await async_provision(hass, "10.0.0.50", _cfg())

    assert result.launched is True


async def test_update_apk_grants_usage_access(hass: HomeAssistant, _patch_adb_imports):
    device = _fake_device({"pm install": "Success"})
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/x.apk"),
    ):
        await async_update_apk(hass, "10.0.0.50")

    assert _USAGE_GRANT in [c.args[0] for c in device.shell.call_args_list]


async def test_provision_fire_os_6_toggles_listener_setting(
    hass: HomeAssistant, _patch_adb_imports
):
    # Fire OS 6 (Android 7.1) has no `cmd notification`; the shell prints an error instead of
    # failing, so the bind falls back to toggling our entry in the secure setting.
    other = "com.example/.OtherListener"
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=true",
        "cmd notification": "No shell command implementation.",
        "settings get secure enabled_notification_listeners": f"{other}:{_LISTENER}\n",
    })
    _patch_adb_imports["device"] = device

    await async_provision(hass, "10.0.0.50", _cfg())

    calls = [c.args[0] for c in device.shell.call_args_list]
    puts = [c for c in calls if c.startswith("settings put secure enabled_notification_listeners")]
    # Removed (other listeners kept), then re-added — never a blanket delete.
    assert puts == [
        f"settings put secure enabled_notification_listeners {other}",
        f"settings put secure enabled_notification_listeners {other}:{_LISTENER}",
    ]
    assert not any("settings delete" in c for c in calls)
    assert calls.index(puts[-1]) < next(i for i, c in enumerate(calls) if "am start" in c)


async def test_provision_fire_os_6_listener_setting_only_ours(
    hass: HomeAssistant, _patch_adb_imports
):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=true",
        "cmd notification": "No shell command implementation.",
        "settings get secure enabled_notification_listeners": f"{_LISTENER}\n",
    })
    _patch_adb_imports["device"] = device

    await async_provision(hass, "10.0.0.50", _cfg())

    calls = [c.args[0] for c in device.shell.call_args_list]
    toggle = [c for c in calls if "enabled_notification_listeners" in c and "get" not in c]
    assert toggle == [
        "settings delete secure enabled_notification_listeners",
        f"settings put secure enabled_notification_listeners {_LISTENER}",
    ]


async def test_provision_modern_fire_os_does_not_touch_listener_setting(
    hass: HomeAssistant, _patch_adb_imports
):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=true",
    })
    _patch_adb_imports["device"] = device

    await async_provision(hass, "10.0.0.50", _cfg())

    calls = [c.args[0] for c in device.shell.call_args_list]
    assert not any("enabled_notification_listeners" in c for c in calls)


async def test_provision_downloads_and_installs_when_missing(
    hass: HomeAssistant, _patch_adb_imports
):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": "",  # not installed
        "pm install": "Success",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=true",
    })
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/fire2mqtt.apk"),
    ):
        result = await async_provision(hass, "10.0.0.50", _cfg())

    assert result.installed is True
    device.push.assert_awaited_once()


async def test_provision_grant_failed_raises(hass: HomeAssistant, _patch_adb_imports):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=false",
    })
    _patch_adb_imports["device"] = device

    with pytest.raises(ProvisionError) as exc:
        await async_provision(hass, "10.0.0.50", _cfg())
    assert exc.value.reason == "grant_failed"
    device.close.assert_awaited()


# ── update (reinstall) path ───────────────────────────────────────────────────

async def test_update_apk_reinstalls_and_relaunches(hass: HomeAssistant, _patch_adb_imports):
    device = _fake_device({"pm install": "Success"})
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/fire2mqtt.apk"),
    ):
        await async_update_apk(hass, "10.0.0.50")

    device.push.assert_awaited_once()
    assert any("pm install -r -g" in c.args[0] for c in device.shell.call_args_list)
    # Relaunched, with no broker extras (settings persist across install -r).
    launch = next(c.args[0] for c in device.shell.call_args_list if "am start" in c.args[0])
    assert FIRE2MQTT_LAUNCH_COMPONENT in launch
    assert "--es" not in launch
    # The reinstall leaves the listener enabled-but-unbound; it's rebound before the relaunch.
    calls = [c.args[0] for c in device.shell.call_args_list]
    allow_idx = next(i for i, c in enumerate(calls) if "cmd notification allow_listener" in c)
    launch_idx = next(i for i, c in enumerate(calls) if "am start" in c)
    assert allow_idx < launch_idx
    device.close.assert_awaited_once()


async def test_update_apk_install_failure_raises(hass: HomeAssistant, _patch_adb_imports):
    device = _fake_device({"pm install": "Failure [INSTALL_FAILED_VERSION_DOWNGRADE]"})
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/fire2mqtt.apk"),
    ):
        with pytest.raises(ProvisionError) as exc:
            await async_update_apk(hass, "10.0.0.50")
    assert exc.value.reason == "install_failed"
    device.close.assert_awaited_once()


async def test_update_apk_signature_mismatch_without_recovery_raises(
    hass: HomeAssistant, _patch_adb_imports
):
    device = _fake_device(
        {"pm install": "Failure [INSTALL_FAILED_UPDATE_INCOMPATIBLE: signatures do not match]"}
    )
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/fire2mqtt.apk"),
    ):
        with pytest.raises(ProvisionError) as exc:
            await async_update_apk(hass, "10.0.0.50")  # no recovery_config
    assert exc.value.reason == "signature_mismatch"


async def test_update_apk_signature_mismatch_self_heals_with_recovery(
    hass: HomeAssistant, _patch_adb_imports
):
    # In-place install fails (key changed); the clean fresh install then succeeds.
    calls: list[str] = []

    async def _shell(cmd: str, *args, **kwargs) -> str:
        calls.append(cmd)
        if "pm install -r -g" in cmd:
            return "Failure [INSTALL_FAILED_UPDATE_INCOMPATIBLE: signatures do not match]"
        if "pm install -g" in cmd:  # fresh install after uninstall
            return "Success"
        return ""

    device = _fake_device({})
    device.shell = AsyncMock(side_effect=_shell)
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/fire2mqtt.apk"),
    ):
        await async_update_apk(hass, "10.0.0.50", recovery_config=_cfg())

    # Recovery path: uninstall → fresh install → re-grant → bind listener → relaunch with extras.
    assert any(f"pm uninstall {FIRE2MQTT_PACKAGE}" in c for c in calls)
    assert any("pm install -g" in c for c in calls)
    assert any(f"pm grant {FIRE2MQTT_PACKAGE}" in c for c in calls)
    allow_idx = next(i for i, c in enumerate(calls) if "cmd notification allow_listener" in c)
    launch_idx = next(i for i, c in enumerate(calls) if "am start" in c)
    assert allow_idx < launch_idx
    launch = next(c for c in calls if "am start" in c)
    assert "--es broker_host 192.168.1.10" in launch
    device.close.assert_awaited_once()


async def test_update_apk_uses_generous_install_timeout(hass: HomeAssistant, _patch_adb_imports):
    # pm install streams no output for tens of seconds; the push + install must run with a per-read
    # timeout well above the 9s connect default, or adb-shell times the read out mid-install.
    device = _fake_device({"pm install": "Success"})
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/fire2mqtt.apk"),
    ):
        await async_update_apk(hass, "10.0.0.50")

    push_kwargs = device.push.call_args.kwargs
    assert push_kwargs.get("transport_timeout_s", 0) > 9
    assert push_kwargs.get("read_timeout_s", 0) > 9
    install_call = next(c for c in device.shell.call_args_list if "pm install" in c.args[0])
    assert install_call.kwargs.get("transport_timeout_s", 0) > 9
    assert install_call.kwargs.get("read_timeout_s", 0) > 9


async def test_update_apk_read_timeout_raises_install_timeout(
    hass: HomeAssistant, _patch_adb_imports
):
    # A genuinely stuck install (adb-shell TcpTimeoutException) surfaces as a mappable
    # ProvisionError("install_timeout"), not the raw adb-shell error the update entity can't map.
    import sys

    tcp_timeout = sys.modules["adb_shell.exceptions"].TcpTimeoutException

    async def _shell(cmd: str, *args, **kwargs) -> str:
        if "pm install" in cmd:
            raise tcp_timeout("Reading from 10.0.0.50:5555 timed out (180.0 seconds)")
        return ""

    device = _fake_device({})
    device.shell = AsyncMock(side_effect=_shell)
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/fire2mqtt.apk"),
    ):
        with pytest.raises(ProvisionError) as exc:
            await async_update_apk(hass, "10.0.0.50")
    assert exc.value.reason == "install_timeout"
    device.close.assert_awaited_once()


# ── pure launch-command builder ───────────────────────────────────────────────

def test_build_launch_cmd_includes_all_extras():
    cmd = _build_launch_cmd(FIRE2MQTT_LAUNCH_COMPONENT, _cfg())
    assert cmd.startswith(f"am start -n {FIRE2MQTT_LAUNCH_COMPONENT}")
    for fragment in (
        "--es broker_host 192.168.1.10",
        "--es broker_port 1883",
        "--es broker_username user",
        "--es broker_password pass",
        "--es device_id living_room",
        "--es topic_prefix fire2mqtt",
        "--es use_tls false",
    ):
        assert fragment in cmd, fragment


def test_build_launch_cmd_serializes_tls_as_bool_string():
    assert "--es use_tls true" in _build_launch_cmd("comp", _cfg(use_tls=True, port=8883))


def test_build_launch_cmd_quotes_password_with_shell_metacharacters():
    # A password with a space and a quote must survive device.shell() tokenization intact.
    secret = "p@ss word'!$x"
    cmd = _build_launch_cmd("comp", _cfg(password=secret))
    assert shlex.quote(secret) in cmd
    tokens = shlex.split(cmd)
    assert tokens[tokens.index("broker_password") + 1] == secret


# --- APK download: the release matching the integration's version ---

_APK_BYTES = b"fake-apk"
_BETA = "0.8.0-beta2"


def _release(tag: str) -> dict:
    import hashlib

    return {
        "tag_name": tag,
        "assets": [{
            "name": "app-release.apk",
            "browser_download_url": f"https://example.invalid/{tag}/app-release.apk",
            "digest": "sha256:" + hashlib.sha256(_APK_BYTES).hexdigest(),
        }],
    }


class _FakeResponse:
    def __init__(self, status: int = 200, json_body=None, body: bytes = b"") -> None:
        self.status = status
        self._json = json_body
        self._body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def json(self):
        return self._json

    async def read(self):
        return self._body


class _FakeSession:
    """Serves canned responses by URL and records what was requested. A real aiohttp session
    would start pycares' resolver thread, which the HA test harness flags as lingering."""

    def __init__(self, routes: dict[str, _FakeResponse]) -> None:
        self._routes = routes
        self.requested: list[str] = []

    def get(self, url, **_kwargs):
        self.requested.append(url)
        return self._routes.get(url, _FakeResponse(status=404))


@pytest.fixture
def download_env(hass: HomeAssistant):
    """Pin the integration version and run executor jobs inline; yields a setter for the fake
    session so each test supplies its own routes."""

    async def _run(func, *args):
        return func(*args)

    holder: dict[str, _FakeSession] = {}
    with (
        patch.object(hass, "async_add_executor_job", side_effect=_run),
        patch(
            "custom_components.fire2mqtt.adb_provision.async_get_integration",
            AsyncMock(return_value=MagicMock(version=_BETA)),
        ),
        patch(
            "custom_components.fire2mqtt.adb_provision.async_get_clientsession",
            side_effect=lambda _hass: holder["session"],
        ),
    ):
        def _use(routes: dict[str, _FakeResponse]) -> _FakeSession:
            holder["session"] = _FakeSession(routes)
            return holder["session"]

        yield _use


async def _download_and_read(hass: HomeAssistant) -> bytes:
    import os

    from custom_components.fire2mqtt.adb_provision import _async_download_apk

    path = await _async_download_apk(hass)
    try:
        with open(path, "rb") as fh:
            return fh.read()
    finally:
        os.remove(path)


async def test_download_uses_release_matching_integration_version(
    hass: HomeAssistant, download_env
):
    # A beta integration must push the beta APK; /releases/latest is the last stable one and
    # Android refuses it over a beta as a downgrade (#45).
    from custom_components.fire2mqtt.const import (
        GITHUB_LATEST_RELEASE_URL,
        GITHUB_RELEASE_BY_TAG_URL,
    )

    session = download_env({
        GITHUB_RELEASE_BY_TAG_URL.format(version=_BETA): _FakeResponse(
            json_body=_release(f"v{_BETA}")
        ),
        GITHUB_LATEST_RELEASE_URL: _FakeResponse(json_body=_release("v0.7.3")),
        f"https://example.invalid/v{_BETA}/app-release.apk": _FakeResponse(body=_APK_BYTES),
    })

    assert await _download_and_read(hass) == _APK_BYTES
    assert GITHUB_LATEST_RELEASE_URL not in session.requested


async def test_download_falls_back_to_latest_for_unreleased_version(
    hass: HomeAssistant, download_env
):
    from custom_components.fire2mqtt.const import GITHUB_LATEST_RELEASE_URL

    session = download_env({
        GITHUB_LATEST_RELEASE_URL: _FakeResponse(json_body=_release("v0.7.3")),
        "https://example.invalid/v0.7.3/app-release.apk": _FakeResponse(body=_APK_BYTES),
    })

    assert await _download_and_read(hass) == _APK_BYTES
    assert session.requested[-1].endswith("v0.7.3/app-release.apk")
