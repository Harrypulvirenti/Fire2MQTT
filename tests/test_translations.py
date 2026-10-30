"""Translation strings must survive the HA frontend's ICU message parser."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_COMPONENT = Path(__file__).parent.parent / "custom_components" / "fire2mqtt"
_FILES = [_COMPONENT / "strings.json", *sorted((_COMPONENT / "translations").glob("*.json"))]

# The frontend formats strings with intl-messageformat, which treats `<word>` as a rich-text tag;
# an unmatched one (e.g. an `<ip>` placeholder in a code sample) renders "Translation error:
# UNCLOSED_TAG" instead of the step. Use bare placeholders like FIRE_TV_IP.
_TAG = re.compile(r"</?[A-Za-z][\w-]*>")


def _strings(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(value, f"{path}.{key}")
    elif isinstance(node, str):
        yield path, node


@pytest.mark.parametrize("path", _FILES, ids=lambda p: p.name)
def test_no_tag_like_placeholders(path: Path) -> None:
    offenders = [key for key, text in _strings(json.loads(path.read_text())) if _TAG.search(text)]
    assert not offenders, f"{path.name}: tag-like text in {offenders}"
