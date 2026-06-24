from homeassistant.const import Platform

DOMAIN = "fire2mqtt"
SCHEMA_VERSION = 2

DEFAULT_TOPIC_PREFIX = "fire2mqtt"
DEFAULT_IDLE_TIMEOUT = 10  # minutes on launcher before reporting "off"

CONF_DEVICE_ID = "device_id"
CONF_TOPIC_PREFIX = "topic_prefix"
CONF_ENABLED_APPS = "enabled_apps"
CONF_IDLE_TIMEOUT = "idle_timeout"
CONF_STATE_DETECTION_RULES_OVERRIDE = "state_detection_rules_override"
CONF_FIRE_TV_IP = "fire_tv_ip"
# Broker settings collected during ADB provisioning, pushed to the app so the user
# never types credentials on the Fire TV remote.
CONF_BROKER_HOST = "broker_host"
CONF_BROKER_PORT = "broker_port"
CONF_BROKER_USERNAME = "broker_username"
CONF_BROKER_PASSWORD = "broker_password"
CONF_USE_TLS = "use_tls"

DEFAULT_BROKER_PORT = 1883
DEFAULT_BROKER_PORT_TLS = 8883

# ADB provisioning (optional, one-time): the integration installs the APK, grants
# WRITE_SECURE_SETTINGS, and launches the app so it self-enables its other permissions.
ADB_PORT = 5555
FIRE2MQTT_PACKAGE = "dev.harrypulvirenti.fire2mqtt"
FIRE2MQTT_LAUNCH_COMPONENT = f"{FIRE2MQTT_PACKAGE}/.ui.MainActivity"
ADB_KEY_FILENAME = "fire2mqtt_adbkey"

# Launch-intent extra keys — the wire contract for pushing broker config to the app
# (see the APK's data/ProvisioningExtras.kt). All values are sent as strings via
# `am start --es`; the app parses them. Keep both sides in sync.
EXTRA_BROKER_HOST = "broker_host"
EXTRA_BROKER_PORT = "broker_port"
EXTRA_BROKER_USERNAME = "broker_username"
EXTRA_BROKER_PASSWORD = "broker_password"
EXTRA_TOPIC_PREFIX = "topic_prefix"
EXTRA_DEVICE_ID = "device_id"
EXTRA_USE_TLS = "use_tls"
GITHUB_LATEST_RELEASE_URL = (
    "https://api.github.com/repos/Harrypulvirenti/Fire2MQTT/releases/latest"
)
GITHUB_RELEASES_URL = "https://github.com/Harrypulvirenti/Fire2MQTT/releases"

TOPIC_STATUS = "{prefix}/{device_id}/status"
TOPIC_STATE_DEVICE = "{prefix}/{device_id}/state/device"
TOPIC_STATE_PLAYBACK = "{prefix}/{device_id}/state/playback"
TOPIC_STATE_APP = "{prefix}/{device_id}/state/app"
TOPIC_STATE_SCREEN = "{prefix}/{device_id}/state/screen"
TOPIC_STATE_VOLUME = "{prefix}/{device_id}/state/volume"
TOPIC_STATE_APPS = "{prefix}/{device_id}/state/apps"
TOPIC_CMD_LAUNCH = "{prefix}/{device_id}/cmd/launch"
TOPIC_CMD_KEY = "{prefix}/{device_id}/cmd/key"
TOPIC_CMD_VOLUME = "{prefix}/{device_id}/cmd/volume"
TOPIC_CMD_POWER = "{prefix}/{device_id}/cmd/power"
TOPIC_CMD_MEDIA = "{prefix}/{device_id}/cmd/media"

# Foreground packages that mean "sitting on the home screen" — used by the
# media player's idle-timeout logic to report STANDBY after CONF_IDLE_TIMEOUT.
LAUNCHER_PACKAGES = frozenset({
    "com.amazon.tv.launcher",
    "com.amazon.firetv.launcher",
})

# HA rejects states longer than 255 chars; cap coerced strings so a buggy or
# malicious MQTT publisher can't blow up entity updates or bloat the recorder.
MAX_PAYLOAD_STR_LENGTH = 255

MEDIA_SESSION_STATE_NONE = 0
MEDIA_SESSION_STATE_STOPPED = 1
MEDIA_SESSION_STATE_PAUSED = 2
MEDIA_SESSION_STATE_PLAYING = 3

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.UPDATE,
]
