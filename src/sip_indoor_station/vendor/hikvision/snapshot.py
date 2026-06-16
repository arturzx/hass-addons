from __future__ import annotations

from sip_indoor_station.sip.server import Snapshot
from sip_indoor_station.vendor.hikvision.client import HikvisionIsapiClient


class HikvisionSnapshotProvider:
    def __init__(self, client: HikvisionIsapiClient, channel: int = 101) -> None:
        self.client = client
        self.channel = channel

    async def capture_snapshot(self) -> Snapshot | None:
        response = await self.client.get_bytes(f"/ISAPI/Streaming/channels/{self.channel}/picture")
        if not response.body:
            return None
        return Snapshot(response.body, response.content_type or "image/jpeg")
