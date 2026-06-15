from __future__ import annotations

import logging
from typing import Any

from sip_indoor_station.vendor.hikvision.client import HikvisionIsapiClient
from sip_indoor_station.vendor.hikvision.errors import IsapiError

LOGGER = logging.getLogger(__name__)


class HikvisionCallApi:
    def __init__(self, client: HikvisionIsapiClient) -> None:
        self.client = client

    async def get_call_status(self) -> str:
        try:
            response = await self.client.get("/ISAPI/VideoIntercom/callStatus?format=json", expect_json=True)
        except IsapiError as exc:
            LOGGER.warning("isapi_call_status_failed reason=%s", exc)
            return "unknown"
        LOGGER.debug("isapi_call_status_response data=%s", response.json_data)
        return self.normalize_call_status(response.json_data)

    async def send_call_signal(self, cmd_type: str) -> bool:
        payload = {"CallSignal": {"cmdType": cmd_type}}
        try:
            await self.client.put("/ISAPI/VideoIntercom/callSignal?format=json", json_payload=payload)
            LOGGER.info("isapi_call_signal_sent cmd_type=%s", cmd_type)
            return True
        except IsapiError as exc:
            LOGGER.warning("isapi_call_signal_failed cmd_type=%s reason=%s", cmd_type, exc)
            return False

    async def reject_call(self) -> bool:
        return await self.send_call_signal("reject")

    async def hangup_call(self) -> bool:
        return await self.send_call_signal("hangUp")

    @staticmethod
    def normalize_call_status(data: Any) -> str:
        if not isinstance(data, dict):
            return "unknown"
        candidates = [
            data.get("CallStatus"),
            data.get("callStatus"),
            data.get("status"),
            data.get("CallStatus", {}).get("status") if isinstance(data.get("CallStatus"), dict) else None,
            data.get("CallStatus", {}).get("callStatus") if isinstance(data.get("CallStatus"), dict) else None,
            data.get("CallStatus", {}).get("callState") if isinstance(data.get("CallStatus"), dict) else None,
        ]
        for value in candidates:
            if isinstance(value, str):
                normalized = value.strip()
                if normalized in {"idle", "ring", "onCall"}:
                    return normalized
                lowered = normalized.lower()
                if lowered == "idle":
                    return "idle"
                if lowered == "ring":
                    return "ring"
                if lowered in {"oncall", "on_call", "on-call"}:
                    return "onCall"
        return "unknown"
