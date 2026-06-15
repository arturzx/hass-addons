from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MediaSession(ABC):
    @abstractmethod
    async def prepare(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def handle_webrtc_offer(self, sdp: str, type_: str = "offer") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def add_ice_candidate(self, candidate: dict[str, Any]) -> None:
        raise NotImplementedError

    def set_ice_candidate_callback(self, callback: Any) -> None:
        raise NotImplementedError

    async def close_peer(self) -> None:
        await self.stop()
