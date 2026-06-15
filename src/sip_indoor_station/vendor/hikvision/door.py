from __future__ import annotations

import logging

from sip_indoor_station.vendor.hikvision.client import HikvisionIsapiClient
from sip_indoor_station.vendor.hikvision.errors import IsapiError
from sip_indoor_station.vendor.hikvision.models import DoorCommandResult

LOGGER = logging.getLogger(__name__)


class HikvisionDoorApi:
    def __init__(self, client: HikvisionIsapiClient, door_id: int = 1) -> None:
        self.client = client
        self.door_id = door_id

    async def open_door(self) -> bool:
        path = f"/ISAPI/AccessControl/RemoteControl/door/{self.door_id}"
        payload = self.open_door_payload()
        try:
            response = await self.client.put(path, xml=payload)
        except IsapiError as exc:
            LOGGER.warning("isapi_open_door_failed reason=%s", exc)
            return False
        LOGGER.info("isapi_open_door_success status=%s", response.status)
        return True

    async def open_door_result(self) -> DoorCommandResult:
        path = f"/ISAPI/AccessControl/RemoteControl/door/{self.door_id}"
        try:
            response = await self.client.put(path, xml=self.open_door_payload())
            LOGGER.info("isapi_open_door_success status=%s", response.status)
            return DoorCommandResult(True, response.status, "door open command sent")
        except IsapiError as exc:
            LOGGER.warning("isapi_open_door_failed reason=%s", exc)
            return DoorCommandResult(False, None, str(exc))

    @staticmethod
    def open_door_payload() -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<RemoteControlDoor>"
            "<cmd>open</cmd>"
            "</RemoteControlDoor>"
        )
