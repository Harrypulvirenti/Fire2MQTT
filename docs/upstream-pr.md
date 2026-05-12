# Upstreaming the state detection rules to python-androidtv

## Opportunity

`python-androidtv` ships an `APPS` dict (150+ entries, package → friendly name) but has
**no per-app state detection rule database**. Every user must write their own YAML rules.
Fire2MQTT's `data/rules.py` is structured to be a drop-in contribution.

## Target repo

`https://github.com/JeffLIrion/python-androidtv`

The relevant file is `androidtv/constants.py`. The existing `APPS` dict structure should be
extended with a companion `STATE_DETECTION_RULES` dict.

## Proposed contribution

1. Add to `androidtv/constants.py`:

```python
# Curated per-app state detection rules.
# Format: {package_id: [rule_list]} — same schema as CONF_STATE_DETECTION_RULES.
# Rules are evaluated in order; first match wins.
# media_session_state integers: 0=None, 1=Stopped, 2=Paused, 3=Playing
STATE_DETECTION_RULES: dict[str, list] = {
    "com.crunchyroll.crunchyroid": [
        {"playing": {"media_session_state": 3}},
        {"paused": {"media_session_state": 2}},
        "idle",
    ],
    # ... all entries from Fire2MQTT data/rules.py
}
```

2. Update `androidtv/basetv/basetv.py` to fall back to `STATE_DETECTION_RULES` when
   no user-provided rules exist for the current app.

3. Update the HA `androidtv` component to display a note that the curated database
   is available and user rules take precedence.

## Process

- Wait until Fire2MQTT has >2 real-world contributors verifying rules for each app.
- Open issue on python-androidtv first to gauge interest.
- Submit PR with: constants addition, fallback logic, tests, and docs update.
