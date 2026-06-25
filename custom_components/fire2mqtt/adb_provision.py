"""Optional ADB-based provisioning of the Fire2MQTT APK.

One-time setup that a user would otherwise do by hand: install the APK, grant the single
``WRITE_SECURE_SETTINGS`` permission, and launch the app so it self-enables its accessibility
and notification-listener access. Only this one ADB grant is needed — on modern Fire OS the app
writes the remaining secure settings itself (see the APK's ``SecureSettingsManager``).

Two things cannot be automated (Fire OS / ADB security):
  * the user must enable **ADB Debugging** once in Developer Options, and
  * accept the on-TV authorization dialog the first time the integration connects.

This module is intentionally self-contained and only imported when the user runs the provisioning
step, so a normal MQTT-only install never loads ``adb_shell``.
"""
from __future__ import annotations

import hashlib
import logging
import os
import shlex
import tempfile
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ADB_KEY_FILENAME,
    ADB_PORT,
    EXTRA_BROKER_HOST,
    EXTRA_BROKER_PASSWORD,
    EXTRA_BROKER_PORT,
    EXTRA_BROKER_USERNAME,
    EXTRA_DEVICE_ID,
    EXTRA_TOPIC_PREFIX,
    EXTRA_USE_TLS,
    FIRE2MQTT_LAUNCH_COMPONENT,
    FIRE2MQTT_PACKAGE,
    GITHUB_LATEST_RELEASE_URL,
)

_LOGGER = logging.getLogger(__name__)

_REMOTE_APK_PATH = "/data/local/tmp/fire2mqtt.apk"
_WRITE_SECURE_SETTINGS = "android.permission.WRITE_SECURE_SETTINGS"

# `pm install -r` refuses to replace an app signed with a different key. This happens
# whenever the signing key changes (e.g. the old debug-signed builds → the release key).
# Recovery requires a clean uninstall + fresh install, which wipes the app's stored config.
_SIGNATURE_MISMATCH_MARKERS = ("signatures do not match", "INSTALL_FAILED_UPDATE_INCOMPATIBLE")


class ProvisionError(Exception):
    """Raised when provisioning cannot complete. ``reason`` maps to a config-flow error key."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(detail or reason)
        self.reason = reason


@dataclass
class BrokerConfig:
    """Broker settings pushed to the app at launch so the user never types them on the TV."""

    host: str
    port: int
    username: str
    password: str
    device_id: str
    topic_prefix: str
    use_tls: bool


@dataclass
class ProvisionResult:
    installed: bool = False
    write_secure_settings: bool = False
    launched: bool = False
    notes: list[str] = field(default_factory=list)


def _build_launch_cmd(component: str, config: BrokerConfig) -> str:
    """Build the ``am start`` command that launches the app with broker config as extras.

    Every value is ``shlex.quote``d because passwords may contain spaces or shell
    metacharacters. All extras are passed as strings (``--es``); the app parses them
    (see the APK's ProvisioningExtras). Pure + side-effect free so it's unit-testable.
    """
    extras = {
        EXTRA_BROKER_HOST: config.host,
        EXTRA_BROKER_PORT: str(config.port),
        EXTRA_BROKER_USERNAME: config.username,
        EXTRA_BROKER_PASSWORD: config.password,
        EXTRA_TOPIC_PREFIX: config.topic_prefix,
        EXTRA_DEVICE_ID: config.device_id,
        EXTRA_USE_TLS: "true" if config.use_tls else "false",
    }
    parts = ["am", "start", "-n", component]
    for key, value in extras.items():
        parts += ["--es", key, shlex.quote(value)]
    return " ".join(parts)


async def _async_connect_device(hass: HomeAssistant, host: str, port: int):
    """Open an authenticated ADB connection, mapping failures to :class:`ProvisionError`.

    Shared by the first-time provisioning flow and the later update push. The caller owns
    closing the returned device.
    """
    # Imported lazily so the dependency is only required when ADB is actually used.
    try:
        from adb_shell.adb_device_async import AdbDeviceTcpAsync
        from adb_shell.auth.keygen import keygen
        from adb_shell.auth.sign_pythonrsa import PythonRSASigner
        from adb_shell.exceptions import DeviceAuthError, TcpTimeoutException
    except ImportError as err:  # pragma: no cover - dependency always present at runtime
        raise ProvisionError("adb_unavailable", str(err)) from err

    signer = await _async_load_signer(hass, keygen, PythonRSASigner)

    device = AdbDeviceTcpAsync(host, port, default_transport_timeout_s=9.0)
    try:
        await device.connect(rsa_keys=[signer], auth_timeout_s=12.0)
    except DeviceAuthError as err:
        raise ProvisionError("adb_auth", str(err)) from err
    except (TcpTimeoutException, OSError) as err:
        # Either ADB debugging is off, the host is wrong, or the user hasn't accepted the dialog.
        raise ProvisionError("adb_unreachable", str(err)) from err
    return device


async def _async_install_latest_apk(
    hass: HomeAssistant, device, *, fresh: bool = False
) -> None:
    """Download the latest signed APK and install it onto an open device.

    ``fresh=False`` does an in-place ``pm install -r`` (keeps app data). ``fresh=True``
    uninstalls first then installs clean — needed when the signing key changed, but it
    wipes the app's stored config, so the caller must re-grant + re-push broker config.
    A signature-mismatch failure raises ``ProvisionError("signature_mismatch")`` so callers
    can decide whether to fall back to a fresh reinstall.
    """
    apk = await _async_download_apk(hass)
    try:
        await device.push(apk, _REMOTE_APK_PATH)
        if fresh:
            await device.shell(f"pm uninstall {FIRE2MQTT_PACKAGE}")
            install_out = await device.shell(f"pm install -g {_REMOTE_APK_PATH}")
        else:
            install_out = await device.shell(f"pm install -r -g {_REMOTE_APK_PATH}")
        if "Success" not in install_out:
            reason = (
                "signature_mismatch"
                if any(m in install_out for m in _SIGNATURE_MISMATCH_MARKERS)
                else "install_failed"
            )
            raise ProvisionError(reason, install_out.strip())
        await device.shell(f"rm -f {_REMOTE_APK_PATH}")
    finally:
        await hass.async_add_executor_job(_remove_quietly, apk)


async def async_update_apk(
    hass: HomeAssistant,
    host: str,
    port: int = ADB_PORT,
    recovery_config: "BrokerConfig | None" = None,
) -> None:
    """Reinstall the latest APK over ADB and relaunch it.

    Used by the HA update entity. Normally an in-place ``install -r`` keeps the app's
    settings, and we relaunch so the new build re-publishes ``state/device`` (with the new
    version). If the install fails because the signing key changed (``signature_mismatch``)
    and a ``recovery_config`` is supplied, fall back to a clean uninstall + fresh install,
    then re-grant WRITE_SECURE_SETTINGS and relaunch with the broker config — since the
    fresh install wipes the app's stored settings. Raises :class:`ProvisionError`.
    """
    device = await _async_connect_device(hass, host, port)
    try:
        try:
            await _async_install_latest_apk(hass, device)
            await device.shell(f"am start -n {FIRE2MQTT_LAUNCH_COMPONENT}")
        except ProvisionError as err:
            if err.reason != "signature_mismatch" or recovery_config is None:
                raise
            # Signing key changed: an in-place update is impossible. Reinstall clean and
            # re-provision so the device comes back fully configured without user input.
            _LOGGER.warning(
                "Fire2MQTT: APK signing key changed; reinstalling fresh and re-provisioning"
            )
            await _async_install_latest_apk(hass, device, fresh=True)
            await device.shell(f"pm grant {FIRE2MQTT_PACKAGE} {_WRITE_SECURE_SETTINGS}")
            await device.shell(_build_launch_cmd(FIRE2MQTT_LAUNCH_COMPONENT, recovery_config))
    finally:
        await device.close()


async def async_provision(
    hass: HomeAssistant,
    host: str,
    config: BrokerConfig,
    port: int = ADB_PORT,
) -> ProvisionResult:
    """Install + grant + launch (with broker config) over ADB. Raises :class:`ProvisionError`."""
    device = await _async_connect_device(hass, host, port)

    result = ProvisionResult()
    try:
        if await _async_is_installed(device):
            result.notes.append("APK already installed")
        else:
            await _async_install_latest_apk(hass, device)
            result.installed = True

        # The one unavoidable grant. The app does the rest on launch.
        await device.shell(
            f"pm grant {FIRE2MQTT_PACKAGE} {_WRITE_SECURE_SETTINGS}"
        )
        result.write_secure_settings = await _async_has_write_secure_settings(device)
        if not result.write_secure_settings:
            # Some Fire OS builds removed WRITE_SECURE_SETTINGS entirely.
            raise ProvisionError("grant_failed", "WRITE_SECURE_SETTINGS not held after grant")

        # Launch with the broker config as intent extras so the app stores it without the
        # user typing anything on the TV; this also runs SecureSettingsManager.ensureAllEnabled().
        await device.shell(_build_launch_cmd(FIRE2MQTT_LAUNCH_COMPONENT, config))
        result.launched = True
        return result
    finally:
        await device.close()


async def _async_load_signer(hass: HomeAssistant, keygen, signer_cls):
    """Load (or generate, once) a persistent ADB RSA key so the on-TV dialog appears only once."""
    key_path = hass.config.path(ADB_KEY_FILENAME)

    def _ensure_key() -> object:
        if not os.path.isfile(key_path):
            keygen(key_path)
        return signer_cls.FromRSAKeyPath(key_path)

    return await hass.async_add_executor_job(_ensure_key)


async def _async_is_installed(device) -> bool:
    out = await device.shell(f"pm list packages {FIRE2MQTT_PACKAGE}")
    return f"package:{FIRE2MQTT_PACKAGE}" in out


async def _async_has_write_secure_settings(device) -> bool:
    out = await device.shell(
        f"dumpsys package {FIRE2MQTT_PACKAGE} | grep {_WRITE_SECURE_SETTINGS}"
    )
    return "granted=true" in out


async def _async_download_apk(hass: HomeAssistant) -> str:
    """Resolve the latest release's .apk asset, download it to a temp file, return the path."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            GITHUB_LATEST_RELEASE_URL, headers={"Accept": "application/vnd.github+json"}
        ) as resp:
            if resp.status != 200:
                raise ProvisionError("download_failed", f"release lookup HTTP {resp.status}")
            release = await resp.json()
    except ProvisionError:
        raise
    except Exception as err:  # noqa: BLE001 - network errors surface as one reason
        raise ProvisionError("download_failed", str(err)) from err

    apk_asset = next(
        (
            asset
            for asset in release.get("assets", [])
            if asset.get("name", "").endswith(".apk")
        ),
        None,
    )
    if not apk_asset:
        raise ProvisionError("no_apk_asset", "latest release has no .apk asset")

    try:
        async with session.get(apk_asset["browser_download_url"]) as resp:
            if resp.status != 200:
                raise ProvisionError("download_failed", f"APK download HTTP {resp.status}")
            data = await resp.read()
    except ProvisionError:
        raise
    except Exception as err:  # noqa: BLE001
        raise ProvisionError("download_failed", str(err)) from err

    # GitHub publishes a sha256 digest per asset; verify it when present so a
    # corrupted or tampered download is never pushed to the device.
    expected_digest = apk_asset.get("digest", "")
    if expected_digest.startswith("sha256:"):
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected_digest.removeprefix("sha256:"):
            raise ProvisionError(
                "download_failed",
                f"APK sha256 mismatch: expected {expected_digest}, got sha256:{actual}",
            )
    else:
        _LOGGER.warning(
            "Fire2MQTT: release asset has no sha256 digest; skipping integrity check"
        )

    def _write() -> str:
        fd, dest = tempfile.mkstemp(prefix="fire2mqtt_", suffix=".apk")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return dest

    return await hass.async_add_executor_job(_write)


def _remove_quietly(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass
