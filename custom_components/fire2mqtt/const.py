DOMAIN = "fire2mqtt"
SCHEMA_VERSION = 1

DEFAULT_TOPIC_PREFIX = "fire2mqtt"
DEFAULT_IDLE_TIMEOUT = 10  # minutes on launcher before reporting "off"

CONF_DEVICE_ID = "device_id"
CONF_TOPIC_PREFIX = "topic_prefix"
CONF_ENABLED_APPS = "enabled_apps"
CONF_IDLE_TIMEOUT = "idle_timeout"
CONF_STATE_DETECTION_RULES_OVERRIDE = "state_detection_rules_override"

TOPIC_STATUS = "{prefix}/{device_id}/status"
TOPIC_STATE_DEVICE = "{prefix}/{device_id}/state/device"
TOPIC_STATE_PLAYBACK = "{prefix}/{device_id}/state/playback"
TOPIC_STATE_APP = "{prefix}/{device_id}/state/app"
TOPIC_STATE_SCREEN = "{prefix}/{device_id}/state/screen"
TOPIC_STATE_VOLUME = "{prefix}/{device_id}/state/volume"
TOPIC_CMD_LAUNCH = "{prefix}/{device_id}/cmd/launch"
TOPIC_CMD_KEY = "{prefix}/{device_id}/cmd/key"
TOPIC_CMD_VOLUME = "{prefix}/{device_id}/cmd/volume"
TOPIC_CMD_POWER = "{prefix}/{device_id}/cmd/power"
TOPIC_CMD_MEDIA = "{prefix}/{device_id}/cmd/media"

MEDIA_SESSION_STATE_NONE = 0
MEDIA_SESSION_STATE_STOPPED = 1
MEDIA_SESSION_STATE_PAUSED = 2
MEDIA_SESSION_STATE_PLAYING = 3

PLATFORMS = ["media_player", "sensor", "binary_sensor", "button", "remote"]
