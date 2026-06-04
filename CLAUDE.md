# CLAUDE.md

Guidance for working in this repo. Read this before answering codebase questions or making changes.

## What this is

Fire2MQTT gives Home Assistant real-time Fire TV state via MQTT. Two halves talk over a fixed MQTT contract:

- **APK** (`apk/`) — a sideloaded Android app (Kotlin, kotlinx.serialization, HiveMQ MQTT 5). Watches media/app/screen/volume and **publishes** state; **subscribes** to command topics. Push-only — no polling.
- **HA integration** (`custom_components/fire2mqtt/`) — a HACS custom component (Python). Subscribes to state topics, exposes entities; publishes commands. Also push-only.

The two never call each other — they only agree on the **MQTT wire contract** (see below). Changing a payload field means changing it in three places at once.

## Repo layout

```
apk/                              Android app (Kotlin)
  app/src/main/kotlin/.../mqtt/   Payloads.kt, TopicSchema.kt, MqttClient.kt  ← wire contract source
  app/src/main/kotlin/.../media/  MediaSessionWatcher, PlaybackStateMapper
  app/src/main/kotlin/.../system/ Foreground/Screen/Volume watchers
  app/src/main/kotlin/.../commands/ CommandRouter + executors
custom_components/fire2mqtt/      HA integration (Python)
  coordinator.py                  push-only DataUpdateCoordinator; subscribes, parses, sends commands
  mqtt_bus.py                     MqttBus — MQTT transport (topic building, subscribe, publish, teardown)
  schema.py                       payload validation models (from_raw coerces + normalizes)
  state_detection.py              pure evaluate() — maps playback payload → HA state string
  data/apps.py, data/rules.py     CURATED_APPS (13 apps) + CURATED_RULES
  entity.py, media_player.py, sensor.py, binary_sensor.py, button.py, remote.py
  const.py                        DOMAIN, SCHEMA_VERSION, all topic templates, config keys
tests/                            pytest suite (HA test harness) + fixtures/mqtt_payloads.json
tools/                            mqtt_simulator.py (fake Fire Stick), dump_rules_from_adb.py
docs/                             mqtt-schema.md (the contract), upstream/ (python-androidtv PR prep)
examples/automations/            sample HA automations
```

## Commands

```bash
# Python tests (run from repo root; venv has homeassistant + pytest installed)
.venv/bin/python -m pytest              # full suite
.venv/bin/python -m pytest -q tests/test_schema.py

# APK build
cd apk && ./gradlew assembleDebug       # debug APK
cd apk && ./gradlew test                # unit tests

# Fake a Fire Stick against a local broker (no hardware needed)
.venv/bin/python tools/mqtt_simulator.py
```

Tests import `custom_components.fire2mqtt.*` directly and inject fake MQTT messages via the `mock_mqtt_subscribe` fixture in `tests/conftest.py` (`.deliver(topic, payload)`), so the coordinator can be exercised without a broker.

## The MQTT wire contract (the load-bearing invariant)

The contract is defined in **three places that must stay in sync**:
1. `apk/.../mqtt/Payloads.kt` — the `@Serializable` data classes + `@SerialName` wire names (what the APK actually sends).
2. `custom_components/fire2mqtt/schema.py` — the `*Payload.from_raw()` validators on the HA side.
3. `docs/mqtt-schema.md` — the human spec. `tests/fixtures/mqtt_payloads.json` mirrors it.

`const.SCHEMA_VERSION` (currently 1) rides on the `state/device` payload; `DevicePayload.from_raw` warns on mismatch. Topics: `{prefix}/{device_id}/state/{playback,app,screen,volume,device}` (retained), `{prefix}/{device_id}/status` (LWT online/offline), `{prefix}/{device_id}/cmd/{launch,key,media,volume,power}`. All `ts` fields are **epoch milliseconds**.

## Conventions & gotchas

- **Push-only.** The coordinator has `update_interval=None`. State changes arrive via MQTT callbacks and call `async_set_updated_data`. Never add polling.
- **`coordinator.data.*` are plain dicts**, not typed objects. Entities read them with `.get(...)`. `schema.py` validates/coerces incoming JSON but **returns a normalized dict** so entities stay dict-based — do not change this without touching every entity accessor.
- **Bad-payload policy: coerce + warn + keep last good.** `_parse_json` returns `None` on malformed JSON and the callback returns early (keeps the previous value); `from_raw` coerces wrong-typed fields (e.g. `"3"` → `3`) and logs rather than raising. Don't make payload handling blank out entities on one bad message.
- **`state_detection.evaluate()` is pure** (no HA imports) on purpose — it's a format-compatible port of python-androidtv's rule logic, slated for upstreaming (`docs/upstream/`). Keep `data/rules.py` format-compatible.
- **Transport vs. logic.** `MqttBus` owns all MQTT I/O; `coordinator.py` owns parsing/state/commands. `async_send_command` on the coordinator is a thin wrapper kept because `media_player.async_turn_off` passes a pre-formatted topic.
- **No new runtime deps.** `manifest.json` `requirements` is `[]` — HA bundles what's needed (mqtt, voluptuous). Don't add pydantic etc.

## Using the knowledge graph (graphify)

A prebuilt graph of this repo lives in `graphify-out/` (gitignored). For "how does X work / what connects to Y / trace the flow through Z" questions, query it instead of grepping cold:

```bash
graphify query "how does a playback MQTT message become an HA media_player state"
graphify explain "Fire2MqttCoordinator"
graphify path "PlaybackPayload" "Fire2MqttMediaPlayer"
```

`graphify-out/GRAPH_REPORT.md` lists the hub nodes (`Fire2MqttCoordinator`, the five `*Payload` models, `MqttBus`) and cross-module connections. After code changes, refresh with `/graphify . --update`.
