from __future__ import annotations

import json
from typing import Any


def parse_ws_message(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    if not isinstance(payload, dict) or "type" not in payload:
        raise ValueError("WebSocket message must be a JSON object with a type field")
    return payload


def ws_message(type_: str, **payload: Any) -> str:
    return json.dumps({"type": type_, **payload}, separators=(",", ":"))
