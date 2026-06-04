# Graph Report - .  (2026-06-04)

## Corpus Check
- Corpus is ~14,910 words - fits in a single context window. You may not need a graph.

## Summary
- 682 nodes · 1107 edges · 64 communities (49 shown, 15 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 241 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_HA EntityCoordinator Core|HA Entity/Coordinator Core]]
- [[_COMMUNITY_Config Flow & App Registry|Config Flow & App Registry]]
- [[_COMMUNITY_Platform Entity Setup|Platform Entity Setup]]
- [[_COMMUNITY_State Detection Rules|State Detection Rules]]
- [[_COMMUNITY_Architecture Concepts & Docs|Architecture Concepts & Docs]]
- [[_COMMUNITY_UI String Keys|UI String Keys]]
- [[_COMMUNITY_UI Translation Keys|UI Translation Keys]]
- [[_COMMUNITY_Button Entity|Button Entity]]
- [[_COMMUNITY_Coordinator Commands & Setup|Coordinator Commands & Setup]]
- [[_COMMUNITY_Schema Payload Models|Schema Payload Models]]
- [[_COMMUNITY_MQTT Payloads & Command Router|MQTT Payloads & Command Router]]
- [[_COMMUNITY_Android UI Activities|Android UI Activities]]
- [[_COMMUNITY_Sensor Entities|Sensor Entities]]
- [[_COMMUNITY_MQTT Client & Connection|MQTT Client & Connection]]
- [[_COMMUNITY_Accessibility Key Dispatcher|Accessibility Key Dispatcher]]
- [[_COMMUNITY_MQTT Topic Schema|MQTT Topic Schema]]
- [[_COMMUNITY_Binary Sensor Entity|Binary Sensor Entity]]
- [[_COMMUNITY_Coordinator Tests|Coordinator Tests]]
- [[_COMMUNITY_Media Session Watcher|Media Session Watcher]]
- [[_COMMUNITY_MqttBus Transport|MqttBus Transport]]
- [[_COMMUNITY_Remote Entity|Remote Entity]]
- [[_COMMUNITY_App Launch Dispatch|App Launch Dispatch]]
- [[_COMMUNITY_MQTT Fixture Payloads|MQTT Fixture Payloads]]
- [[_COMMUNITY_Idle Playback Payload|Idle Playback Payload]]
- [[_COMMUNITY_Paused Playback Payload|Paused Playback Payload]]
- [[_COMMUNITY_Playing Playback Payload|Playing Playback Payload]]
- [[_COMMUNITY_Volume Controller|Volume Controller]]
- [[_COMMUNITY_Upstream Rules Contract|Upstream Rules Contract]]
- [[_COMMUNITY_Broker Host Validator|Broker Host Validator]]
- [[_COMMUNITY_Foreground Service Notification|Foreground Service Notification]]
- [[_COMMUNITY_Foreground App Watcher|Foreground App Watcher]]
- [[_COMMUNITY_Test Fixtures & Conftest|Test Fixtures & Conftest]]
- [[_COMMUNITY_Boot Receiver|Boot Receiver]]
- [[_COMMUNITY_Volume Watcher|Volume Watcher]]
- [[_COMMUNITY_Coordinator Init|Coordinator Init]]
- [[_COMMUNITY_Device Info Payload|Device Info Payload]]
- [[_COMMUNITY_Playback State Mapper|Playback State Mapper]]
- [[_COMMUNITY_Screen State Watcher|Screen State Watcher]]
- [[_COMMUNITY_Application Entry Point|Application Entry Point]]
- [[_COMMUNITY_Volume Level Payload|Volume Level Payload]]
- [[_COMMUNITY_Volume Muted Payload|Volume Muted Payload]]
- [[_COMMUNITY_HACS Metadata|HACS Metadata]]
- [[_COMMUNITY_App Payload (Crunchyroll)|App Payload (Crunchyroll)]]
- [[_COMMUNITY_App Payload (Home)|App Payload (Home)]]
- [[_COMMUNITY_Schema Test Helpers|Schema Test Helpers]]
- [[_COMMUNITY_Integration Domain Manifest|Integration Domain Manifest]]
- [[_COMMUNITY_Localization Files|Localization Files]]
- [[_COMMUNITY_ADB Rules Dumper|ADB Rules Dumper]]
- [[_COMMUNITY_App Build Script|App Build Script]]
- [[_COMMUNITY_Async Options Update|Async Options Update]]
- [[_COMMUNITY_Integration Unload|Integration Unload]]
- [[_COMMUNITY_Config Entry Alias|Config Entry Alias]]
- [[_COMMUNITY_Platform List|Platform List]]
- [[_COMMUNITY_MQTT Publish Mock|MQTT Publish Mock]]
- [[_COMMUNITY_MQTT Subscribe Mock|MQTT Subscribe Mock]]

## God Nodes (most connected - your core abstractions)
1. `Fire2MqttCoordinator` - 98 edges
2. `Fire2MqttEntity` - 51 edges
3. `Fire2MqttMediaPlayer` - 33 edges
4. `MqttBus` - 30 edges
5. `Fire2MqttService` - 29 edges
6. `PlaybackPayload` - 24 edges
7. `DevicePayload` - 24 edges
8. `AppPayload` - 23 edges
9. `ScreenPayload` - 23 edges
10. `VolumePayload` - 23 edges

## Surprising Connections (you probably didn't know these)
- `PlaybackPayload` --semantically_similar_to--> `state/playback payload spec`  [INFERRED] [semantically similar]
  custom_components/fire2mqtt/schema.py → docs/mqtt-schema.md
- `AppPayload` --semantically_similar_to--> `state/app payload spec`  [INFERRED] [semantically similar]
  custom_components/fire2mqtt/schema.py → docs/mqtt-schema.md
- `ScreenPayload` --semantically_similar_to--> `state/screen payload spec`  [INFERRED] [semantically similar]
  custom_components/fire2mqtt/schema.py → docs/mqtt-schema.md
- `VolumePayload` --semantically_similar_to--> `state/volume payload spec`  [INFERRED] [semantically similar]
  custom_components/fire2mqtt/schema.py → docs/mqtt-schema.md
- `DevicePayload` --semantically_similar_to--> `state/device payload spec`  [INFERRED] [semantically similar]
  custom_components/fire2mqtt/schema.py → docs/mqtt-schema.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **MQTT Command -> Router -> Executor Chain** — mqtt_mqttclient_fire2mqttclient, commands_commandrouter_commandrouter, commands_applauncher_applauncher, commands_volumecontroller_volumecontroller, commands_fire2mqttaccessibilityservice_fire2mqttaccessibilityservice [EXTRACTED 1.00]
- **MQTT Topic/Payload Schema Definitions** — mqtt_topicschema_topicschema, mqtt_payloads_playbackpayload, mqtt_payloads_apppayload, mqtt_payloads_screenpayload, mqtt_payloads_volumepayload, mqtt_payloads_devicepayload, mqtt_payloads_volumecommandpayload [EXTRACTED 1.00]
- **State Watcher -> MQTT Publish Pipeline** — system_foregroundappwatcher_foregroundappwatcher, system_screenwatcher_screenwatcher, system_volumewatcher_volumewatcher, media_mediasessionwatcher_mediasessionwatcher, service_fire2mqttservice_fire2mqttservice, mqtt_mqttclient_fire2mqttclient [EXTRACTED 1.00]
- **Platform entity setup pattern: coordinator data flows through entity classes to HA platform** — fire2mqtt_coordinator_fire2mqttcoordinator, fire2mqtt_entity_fire2mqttentity, fire2mqtt_media_player_fire2mqttmediaplayer, fire2mqtt_sensor_currentappsensor, fire2mqtt_binary_sensor_screenonsensor, fire2mqtt_button_applaunchbutton, fire2mqtt_remote_fire2mqttremote [INFERRED 0.95]
- **App launch flow: CURATED_APPS -> AppLaunchButton/MediaPlayer -> async_launch_app -> MQTT cmd/launch** — fire2mqtt_apps_curated_apps, fire2mqtt_button_applaunchbutton, fire2mqtt_media_player_fire2mqttmediaplayer, fire2mqtt_coordinator_async_launch_app, fire2mqtt_coordinator_async_send_command [EXTRACTED 1.00]
- **State detection pipeline: MQTT payload -> CURATED_RULES -> evaluate() -> MediaPlayerState** — fire2mqtt_coordinator_fire2mqttdata, fire2mqtt_rules_curated_rules, fire2mqtt_state_detection_evaluate, fire2mqtt_media_player_fire2mqttmediaplayer [EXTRACTED 1.00]
- **Home Assistant automation examples using Fire2MQTT entities** — automations_dim_lights_on_playback, automations_pause_on_doorbell, automations_pause_when_room_empty, automations_turn_off_when_idle, automations_watching_tv_scene [EXTRACTED 0.95]
- **App rules discovery and contribution workflow** — tools_dump_rules_from_adb, concept_curated_app_rules_db, docs_adding_apps, tools_mqtt_simulator [INFERRED 0.85]
- **MQTT schema contract — five payload models** — fire2mqtt_schema_playbackpayload, fire2mqtt_schema_apppayload, fire2mqtt_schema_screenpayload, fire2mqtt_schema_volumepayload, fire2mqtt_schema_devicepayload [INFERRED 0.85]
- **Schema-validation pipeline: coordinator -> payload model -> coordinator.data** — fire2mqtt_coordinator_fire2mqttcoordinator, fire2mqtt_schema_playbackpayload, fire2mqtt_coordinator_fire2mqttdata [INFERRED 0.85]
- **Upstreaming mirror: live rules + evaluator -> upstream module -> PR proposal** — fire2mqtt_rules_curated_rules, upstream_state_detection_rules_state_detection_rules, upstream_issue_draft_proposal [INFERRED 0.75]

## Communities (64 total, 15 thin omitted)

### Community 0 - "HA Entity/Coordinator Core"
Cohesion: 0.05
Nodes (46): Any, bool, HomeAssistant, int, str, state/app payload spec, state/device payload spec, schema_version contract / breaking-change policy (+38 more)

### Community 1 - "Config Flow & App Registry"
Cohesion: 0.06
Nodes (36): ConfigFlowResult, bool, ConfigEntry, str, bool, HomeAssistant, AppInfo, Curated app database for Fire TV devices.  Each entry maps a short key to metada (+28 more)

### Community 2 - "Platform Entity Setup"
Cohesion: 0.10
Nodes (10): AddEntitiesCallback, bool, ConfigEntry, HomeAssistant, str, async_setup_entry(), Fire2MqttMediaPlayer, float (+2 more)

### Community 3 - "State Detection Rules"
Cohesion: 0.08
Nodes (27): Any, bool, str, Curated per-app state detection rules for Fire TV.  Rule list format is intentio, Any, bool, str, Fire2MQTT media player entity. (+19 more)

### Community 4 - "Architecture Concepts & Docs"
Cohesion: 0.11
Nodes (23): Client, Curated app state detection rule database, Push-only state architecture, Fire Stick APK sideloading via ADB, python-androidtv upstream contribution plan, docs/adding-apps.md, docs/installing-apk.md, docs/upstream-pr.md (+15 more)

### Community 5 - "UI String Keys"
Cohesion: 0.08
Nodes (23): already_configured, mqtt_not_configured, config, abort, error, step, device_id, device_name (+15 more)

### Community 6 - "UI Translation Keys"
Cohesion: 0.08
Nodes (23): already_configured, mqtt_not_configured, config, abort, error, step, device_id, device_name (+15 more)

### Community 7 - "Button Entity"
Cohesion: 0.11
Nodes (18): AppInfo, ButtonEntity, AddEntitiesCallback, ConfigEntry, Fire2MqttCoordinator, HomeAssistant, str, bool (+10 more)

### Community 8 - "Coordinator Commands & Setup"
Cohesion: 0.13
Nodes (7): async_setup_entry (__init__), Fire2MqttRuntimeData, Fire2MqttCoordinator, Push-driven coordinator. Entities update immediately on MQTT message., Subscribe to all state topics. Called from async_setup_entry., Unsubscribe from all topics. Called from async_unload_entry., ReceiveMessage

### Community 9 - "Schema Payload Models"
Cohesion: 0.16
Nodes (16): Any, bool, int, str, _coerce_bool(), _coerce_int(), _coerce_str(), Validate/coerce *raw* and return a plain normalised dict. (+8 more)

### Community 10 - "MQTT Payloads & Command Router"
Cohesion: 0.16
Nodes (11): String, CommandRouter, DevicePayload, Fire2MqttClient, Job, MqttConfig, AppPayload, DevicePayload (+3 more)

### Community 11 - "Android UI Activities"
Cohesion: 0.13
Nodes (12): Bundle, Boolean, Bundle, Context, String, AppCompatActivity, PreferenceFragmentCompat, SharedPreferences (+4 more)

### Community 12 - "Sensor Entities"
Cohesion: 0.22
Nodes (10): AddEntitiesCallback, str, async_setup_entry(), CurrentAppPackageSensor, CurrentAppSensor, MediaArtistSensor, MediaTitleSensor, Fire2MQTT sensor entities. (+2 more)

### Community 13 - "MQTT Client & Connection"
Cohesion: 0.17
Nodes (8): Boolean, Flow, String, Retained MQTT State Cache (pre-seed before connect), Mqtt5AsyncClient, Fire2MqttClient, Pair, Unit

### Community 14 - "Accessibility Key Dispatcher"
Cohesion: 0.18
Nodes (8): AccessibilityEvent, AccessibilityService, android, Boolean, Int, Fire2MqttAccessibilityService, sendKey(), AccessibilityService Key Injection Pattern

### Community 16 - "Binary Sensor Entity"
Cohesion: 0.15
Nodes (10): BinarySensorEntity, AddEntitiesCallback, bool, ConfigEntry, Fire2MqttCoordinator, HomeAssistant, async_setup_entry(), Fire2MQTT binary sensor entities. (+2 more)

### Community 17 - "Coordinator Tests"
Cohesion: 0.22
Nodes (11): make_msg(), MagicMock, str, Tests for the Fire2MQTT coordinator., test_app_callback_updates_data(), test_invalid_json_does_not_crash(), test_playback_callback_updates_data(), test_screen_callback_updates_data() (+3 more)

### Community 18 - "Media Session Watcher"
Cohesion: 0.17
Nodes (9): Flow, MediaNotificationListener, MediaSessionWatcher, MediaController, MediaMetadata, PlaybackPayload, NotificationListenerService, PlaybackPayload (+1 more)

### Community 19 - "MqttBus Transport"
Cohesion: 0.20
Nodes (7): Any, HomeAssistant, str, Format a state-topic template., Format a command-topic template., Subscribe to *template* (formatted) and track the unsub callable., Publish *payload* to the formatted command topic.          String payloads are s

### Community 20 - "Remote Entity"
Cohesion: 0.18
Nodes (9): AddEntitiesCallback, ConfigEntry, Fire2MqttCoordinator, HomeAssistant, str, async_setup_entry(), Fire2MqttRemote, Fire2MQTT remote entity — sends key events via MQTT cmd/key. (+1 more)

### Community 21 - "App Launch Dispatch"
Cohesion: 0.20
Nodes (6): Boolean, String, String, AppLauncher, CommandRouter, VolumeCommandPayload

### Community 22 - "MQTT Fixture Payloads"
Cohesion: 0.20
Nodes (9): screen_off, on, ts, screen_on, on, ts, status_offline, status_online (+1 more)

### Community 23 - "Idle Playback Payload"
Cohesion: 0.22
Nodes (9): playback_idle, album, app, artist, duration_ms, media_session_state, position_ms, title (+1 more)

### Community 24 - "Paused Playback Payload"
Cohesion: 0.22
Nodes (9): playback_paused, album, app, artist, duration_ms, media_session_state, position_ms, title (+1 more)

### Community 25 - "Playing Playback Payload"
Cohesion: 0.22
Nodes (9): playback_playing, album, app, artist, duration_ms, media_session_state, position_ms, title (+1 more)

### Community 27 - "Upstream Rules Contract"
Cohesion: 0.32
Nodes (8): media_session_state integer mapping, state/playback payload spec, python-androidtv Compatible Rule Format, Fire2MqttMediaPlayer._get_rules, CURATED_RULES, Upstream STATE_DETECTION_RULES PR proposal, python-androidtv, STATE_DETECTION_RULES (upstream mirror)

### Community 28 - "Broker Host Validator"
Cohesion: 0.33
Nodes (4): Boolean, String, DNS Rebinding Protection via IP Pinning, BrokerHostValidator

### Community 29 - "Foreground Service Notification"
Cohesion: 0.33
Nodes (4): Int, Intent, IBinder, Notification

### Community 30 - "Foreground App Watcher"
Cohesion: 0.38
Nodes (4): Flow, String, ForegroundAppEvent, ForegroundAppWatcher

### Community 31 - "Test Fixtures & Conftest"
Cohesion: 0.29
Nodes (4): mock_mqtt_subscribe(), pytest fixtures for Fire2MQTT integration tests., Mock mqtt.async_subscribe to capture subscriptions and replay test messages., coordinator fixture (test_coordinator.py)

### Community 32 - "Boot Receiver"
Cohesion: 0.33
Nodes (4): Context, Intent, BroadcastReceiver, BootReceiver

### Community 33 - "Volume Watcher"
Cohesion: 0.33
Nodes (4): Flow, VolumePayload, VolumeWatcher, VolumePayload

### Community 35 - "Device Info Payload"
Cohesion: 0.33
Nodes (6): device_info, fire_os, ip, mac, model, schema_version

### Community 36 - "Playback State Mapper"
Cohesion: 0.40
Nodes (3): Int, python-androidtv media_session_state Schema Convention, PlaybackStateMapper

### Community 37 - "Screen State Watcher"
Cohesion: 0.40
Nodes (3): Boolean, Flow, ScreenWatcher

### Community 39 - "Volume Level Payload"
Cohesion: 0.40
Nodes (5): volume_8_of_15, level, max, mute, ts

### Community 40 - "Volume Muted Payload"
Cohesion: 0.40
Nodes (5): volume_muted, level, max, mute, ts

### Community 41 - "HACS Metadata"
Cohesion: 0.40
Nodes (4): content_in_root, hacs, homeassistant, name

### Community 42 - "App Payload (Crunchyroll)"
Cohesion: 0.50
Nodes (4): app_crunchyroll, name, package, ts

### Community 43 - "App Payload (Home)"
Cohesion: 0.50
Nodes (4): app_home, name, package, ts

## Knowledge Gaps
- **167 isolated node(s):** `String`, `Boolean`, `String`, `android`, `AccessibilityEvent` (+162 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Fire2MqttCoordinator` connect `Coordinator Commands & Setup` to `HA Entity/Coordinator Core`, `Config Flow & App Registry`, `Platform Entity Setup`, `Coordinator Init`, `State Detection Rules`, `Button Entity`, `Schema Test Helpers`, `Sensor Entities`, `Binary Sensor Entity`, `Coordinator Tests`, `Remote Entity`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Why does `Fire2MqttMediaPlayer` connect `Platform Entity Setup` to `Config Flow & App Registry`, `State Detection Rules`, `Button Entity`, `Coordinator Commands & Setup`, `Binary Sensor Entity`, `Upstream Rules Contract`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Fire2MqttService` connect `MQTT Payloads & Command Router` to `Boot Receiver`, `Volume Watcher`, `Screen State Watcher`, `Application Entry Point`, `Android UI Activities`, `MQTT Client & Connection`, `MQTT Topic Schema`, `Media Session Watcher`, `App Launch Dispatch`, `Broker Host Validator`, `Foreground Service Notification`, `Foreground App Watcher`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 65 inferred relationships involving `Fire2MqttCoordinator` (e.g. with `AppInfo` and `AddEntitiesCallback`) actually correct?**
  _`Fire2MqttCoordinator` has 65 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `Fire2MqttEntity` (e.g. with `AppInfo` and `AddEntitiesCallback`) actually correct?**
  _`Fire2MqttEntity` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `Fire2MqttMediaPlayer` (e.g. with `ScreenOnSensor` and `Fire2MqttCoordinator`) actually correct?**
  _`Fire2MqttMediaPlayer` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `MqttBus` (e.g. with `Any` and `bool`) actually correct?**
  _`MqttBus` has 17 INFERRED edges - model-reasoned connections that need verification._