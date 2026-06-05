# Graph Report - .  (2026-06-05)

## Corpus Check
- 29 files · ~19,527 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 775 nodes · 1345 edges · 46 communities (41 shown, 5 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 243 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_HA Entity Layer|HA Entity Layer]]
- [[_COMMUNITY_APK Service & Boot|APK Service & Boot]]
- [[_COMMUNITY_Architecture Docs|Architecture Docs]]
- [[_COMMUNITY_HA Test Fixtures|HA Test Fixtures]]
- [[_COMMUNITY_Config Flow & Apps DB|Config Flow & Apps DB]]
- [[_COMMUNITY_APK Command Routing|APK Command Routing]]
- [[_COMMUNITY_Media Player Entity|Media Player Entity]]
- [[_COMMUNITY_APK App & Foreground|APK App & Foreground]]
- [[_COMMUNITY_State Detection Rules|State Detection Rules]]
- [[_COMMUNITY_MQTT Payload Fixtures|MQTT Payload Fixtures]]
- [[_COMMUNITY_Automations & Concepts|Automations & Concepts]]
- [[_COMMUNITY_Media Player Tests|Media Player Tests]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]

## God Nodes (most connected - your core abstractions)
1. `Fire2MqttCoordinator` - 97 edges
2. `Fire2MqttEntity` - 50 edges
3. `Fire2MQTT media player entity.` - 34 edges
4. `MqttBus` - 30 edges
5. `CommandRouter` - 27 edges
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
- 1-file cycle: `tests/conftest.py -> tests/conftest.py`
- 1-file cycle: `tests/test_config_flow.py -> tests/test_config_flow.py`

## Hyperedges (group relationships)
- **MQTT Topic/Payload Schema Definitions** — mqtt_topicschema_topicschema, mqtt_payloads_playbackpayload, mqtt_payloads_apppayload, mqtt_payloads_screenpayload, mqtt_payloads_volumepayload, mqtt_payloads_devicepayload, mqtt_payloads_volumecommandpayload [EXTRACTED 1.00]
- **Platform entity setup pattern: coordinator data flows through entity classes to HA platform** — fire2mqtt_coordinator_fire2mqttcoordinator, fire2mqtt_entity_fire2mqttentity, fire2mqtt_media_player_fire2mqttmediaplayer, fire2mqtt_sensor_currentappsensor, fire2mqtt_binary_sensor_screenonsensor, fire2mqtt_button_applaunchbutton, fire2mqtt_remote_fire2mqttremote [INFERRED 0.95]
- **App launch flow: CURATED_APPS -> AppLaunchButton/MediaPlayer -> async_launch_app -> MQTT cmd/launch** — fire2mqtt_apps_curated_apps, fire2mqtt_button_applaunchbutton, fire2mqtt_media_player_fire2mqttmediaplayer, fire2mqtt_coordinator_async_launch_app, fire2mqtt_coordinator_async_send_command [EXTRACTED 1.00]
- **MQTT schema contract — five payload models** — fire2mqtt_schema_playbackpayload, fire2mqtt_schema_apppayload, fire2mqtt_schema_screenpayload, fire2mqtt_schema_volumepayload, fire2mqtt_schema_devicepayload [INFERRED 0.85]
- **Home Assistant automation examples using Fire2MQTT entities** — automations_dim_lights_on_playback, automations_pause_on_doorbell, automations_pause_when_room_empty, automations_turn_off_when_idle, automations_watching_tv_scene [EXTRACTED 0.95]
- **App rules discovery and contribution workflow** — tools_dump_rules_from_adb, concept_curated_app_rules_db, docs_adding_apps, tools_mqtt_simulator [INFERRED 0.85]
- **Upstreaming mirror: live rules + evaluator -> upstream module -> PR proposal** — fire2mqtt_rules_curated_rules, upstream_state_detection_rules_state_detection_rules, upstream_issue_draft_proposal [INFERRED 0.75]
- **MQTT Contract Three-Way Sync** — claude_md_payloads_kt, claude_md_schema_py, claude_md_mqtt_schema_md [EXTRACTED 1.00]

## Communities (46 total, 5 thin omitted)

### Community 0 - "HA Entity Layer"
Cohesion: 0.05
Nodes (56): AppInfo, BinarySensorEntity, ButtonEntity, AddEntitiesCallback, bool, Fire2MqttCoordinator, HomeAssistant, AddEntitiesCallback (+48 more)

### Community 1 - "APK Service & Boot"
Cohesion: 0.05
Nodes (29): Flow, Context, Intent, Int, String, Boolean, Flow, Flow (+21 more)

### Community 2 - "Architecture Docs"
Cohesion: 0.05
Nodes (33): APK (Android App), data/apps.py, Bad-Payload Policy, CommandRouter, tests/conftest.py, const.py, coordinator.py, Fire2MQTT Project (+25 more)

### Community 3 - "HA Test Fixtures"
Cohesion: 0.07
Nodes (35): ConfigEntry, mock_mqtt_subscribe(), HomeAssistant, MockConfigEntry, pytest fixtures for Fire2MQTT integration tests., Mock mqtt.async_subscribe to capture subscriptions and replay test messages., setup_integration(), online() (+27 more)

### Community 4 - "Config Flow & Apps DB"
Cohesion: 0.06
Nodes (34): ConfigFlowResult, bool, ConfigEntry, str, Curated app database for Fire TV devices.  Each entry maps a short key to metada, media_session_state integer mapping, state/playback payload spec, CURATED_APPS (+26 more)

### Community 5 - "APK Command Routing"
Cohesion: 0.07
Nodes (6): String, String, CommandRouter, Int, String, CommandRouter

### Community 6 - "Media Player Entity"
Cohesion: 0.10
Nodes (10): AddEntitiesCallback, bool, HomeAssistant, str, async_setup_entry(), Fire2MQTT media player entity., Fire2MqttEntity, float (+2 more)

### Community 7 - "APK App & Foreground"
Cohesion: 0.10
Nodes (12): Boolean, String, Flow, String, Context, PackageManager, PackageManager, String (+4 more)

### Community 8 - "State Detection Rules"
Cohesion: 0.10
Nodes (24): Any, bool, str, Any, bool, str, _conditions_match(), evaluate() (+16 more)

### Community 9 - "MQTT Payload Fixtures"
Cohesion: 0.15
Nodes (26): app_crunchyroll, app_home, name, package, ts, playback_idle, album, app (+18 more)

### Community 10 - "Automations & Concepts"
Cohesion: 0.11
Nodes (22): Client, Curated app state detection rule database, Push-only state architecture, Fire Stick APK sideloading via ADB, python-androidtv upstream contribution plan, docs/adding-apps.md, docs/installing-apk.md, docs/upstream-pr.md (+14 more)

### Community 11 - "Media Player Tests"
Cohesion: 0.17
Nodes (21): online(), HomeAssistant, Integration tests for the Fire2MQTT media_player entity., test_entity_created(), test_goes_back_offline(), test_idle_when_online(), test_media_attributes(), test_media_pause_publishes() (+13 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (20): en.json translations, mqtt_not_configured, config, abort, error, step, device_id, device_name (+12 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (13): MagicMock, make_msg(), str, Tests for the Fire2MQTT coordinator., test_app_callback_updates_data(), test_async_setup_subscribes_all_topics(), test_async_teardown_calls_all_unsubs(), test_device_info_callback_updates_data() (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (19): mqtt_not_configured, config, abort, error, step, device_id, device_name, enabled_apps (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (15): bool, HomeAssistant, int, state/app payload spec, state/screen payload spec, Fire2MqttData, Fire2MQTT coordinator — MQTT-driven, push-only (no polling)., MqttBus (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (18): config_entry_with_options(), _enable_custom(), _patch_apk_check(), _patch_mqtt_client(), bool, HomeAssistant, MockConfigEntry, Tests for the Fire2MQTT config flow and options flow. (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (3): Int, AudioManager, VolumeController

### Community 18 - "Community 18"
Cohesion: 0.16
Nodes (10): Bundle, Boolean, Context, String, AppCompatActivity, Bundle, PreferenceFragmentCompat, SharedPreferences (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.17
Nodes (8): Boolean, Flow, String, Retained MQTT State Cache (pre-seed before connect), Mqtt5AsyncClient, Fire2MqttClient, Pair, Unit

### Community 20 - "Community 20"
Cohesion: 0.18
Nodes (7): Fire2MQTT MQTT Schema v1 wire contract, PlaybackPayload, Models the ``state/playback`` MQTT topic payload., Tests for the Fire2MQTT schema / payload models., TestAppPayload, TestDevicePayload, TestVolumePayload

### Community 21 - "Community 21"
Cohesion: 0.22
Nodes (13): Any, bool, int, str, _coerce_bool(), _coerce_int(), _coerce_str(), Schema / payload models for Fire2MQTT MQTT messages.  Each payload class is a fr (+5 more)

### Community 22 - "Community 22"
Cohesion: 0.17
Nodes (7): Any, str, state/device payload spec, schema_version contract / breaking-change policy, Publish a command to the Fire Stick.          *cmd_template* may be either a for, DevicePayload, Models the ``state/device`` MQTT topic payload.

### Community 23 - "Community 23"
Cohesion: 0.22
Nodes (7): Int, Int, Arguments, python-androidtv media_session_state Schema Convention, playingStates(), stoppedStates(), Stream

### Community 24 - "Community 24"
Cohesion: 0.23
Nodes (11): bool, _async_options_updated(), async_setup_entry(), async_unload_entry(), Fire2MqttRuntimeData, Fire2MQTT — Fire TV Stick → MQTT → Home Assistant., Fire2MqttConfigEntry, content_in_root (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.21
Nodes (7): AccessibilityEvent, AccessibilityService, android, Boolean, Int, sendKey(), AccessibilityService Key Injection Pattern

### Community 26 - "Community 26"
Cohesion: 0.21
Nodes (4): Boolean, String, String, DNS Rebinding Protection via IP Pinning

### Community 27 - "Community 27"
Cohesion: 0.20
Nodes (7): Any, HomeAssistant, str, Format a state-topic template., Format a command-topic template., Subscribe to *template* (formatted) and track the unsub callable., Publish *payload* to the formatted command topic.          String payloads are s

### Community 28 - "Community 28"
Cohesion: 0.28
Nodes (7): state/volume payload spec, Models the ``state/volume`` MQTT topic payload., VolumePayload, MagicMock, MqttBus.publish JSON-encodes dicts before calling async_publish., MqttBus.publish passes string payloads through without JSON encoding., TestMqttBus

### Community 29 - "Community 29"
Cohesion: 0.22
Nodes (3): PlaybackPayload, The original string-vs-int bug: APK may send "3" as a string., PlaybackPayload.from_raw coerces str→int so evaluate() returns 'playing'.

### Community 30 - "Community 30"
Cohesion: 0.32
Nodes (5): make_msg(), str, On bad JSON the previous data.playback value is preserved., Bad JSON on a fresh coordinator leaves data.playback as {}., TestCoordinatorKeepLastGood

### Community 31 - "Community 31"
Cohesion: 0.43
Nodes (4): color_for(), on_message(), pretty(), str

## Knowledge Gaps
- **121 isolated node(s):** `String`, `Boolean`, `String`, `android`, `AccessibilityEvent` (+116 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Fire2MqttCoordinator` connect `HA Entity Layer` to `Community 32`, `HA Test Fixtures`, `Media Player Entity`, `Community 13`, `Community 15`, `Community 20`, `Community 22`, `Community 24`, `Community 28`, `Community 29`, `Community 30`?**
  _High betweenness centrality (0.441) - this node is a cross-community bridge._
- **Why does `PlaybackPayload` connect `Community 29` to `HA Entity Layer`, `APK Service & Boot`, `Config Flow & Apps DB`, `State Detection Rules`, `Community 15`, `Community 20`, `Community 22`, `Community 28`?**
  _High betweenness centrality (0.364) - this node is a cross-community bridge._
- **Why does `homeassistant` connect `Community 24` to `HA Entity Layer`, `Architecture Docs`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Are the 65 inferred relationships involving `Fire2MqttCoordinator` (e.g. with `AddEntitiesCallback` and `AppInfo`) actually correct?**
  _`Fire2MqttCoordinator` has 65 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `Fire2MqttEntity` (e.g. with `AddEntitiesCallback` and `AppInfo`) actually correct?**
  _`Fire2MqttEntity` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `Fire2MQTT media player entity.` (e.g. with `ScreenOnSensor` and `Fire2MqttCoordinator`) actually correct?**
  _`Fire2MQTT media player entity.` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `MqttBus` (e.g. with `Any` and `bool`) actually correct?**
  _`MqttBus` has 17 INFERRED edges - model-reasoned connections that need verification._