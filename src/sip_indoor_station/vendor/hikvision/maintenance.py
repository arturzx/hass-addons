from __future__ import annotations

import logging

from sip_indoor_station.vendor.hikvision.client import HikvisionIsapiClient
from sip_indoor_station.vendor.hikvision.errors import IsapiError

LOGGER = logging.getLogger(__name__)


class HikvisionMaintenanceApi:
    def __init__(self, client: HikvisionIsapiClient) -> None:
        self.client = client

    async def health_check(self) -> bool:
        try:
            await self.client.get("/ISAPI/System/deviceInfo")
            return True
        except IsapiError as exc:
            LOGGER.debug("isapi_health_check_failed reason=%s", exc)
            return False

    async def reboot(self) -> bool:
        try:
            await self.client.put("/ISAPI/System/reboot")
            LOGGER.info("isapi_reboot_command_sent")
            return True
        except IsapiError as exc:
            LOGGER.warning("isapi_reboot_failed reason=%s", exc)
            return False
