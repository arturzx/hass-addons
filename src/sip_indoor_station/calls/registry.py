from __future__ import annotations

from sip_indoor_station.calls.session import CallSession


class CallRegistry:
    def __init__(self) -> None:
        self._calls: dict[str, CallSession] = {}

    def add(self, session: CallSession) -> None:
        self._calls[session.call_id] = session

    def get(self, call_id: str | None) -> CallSession | None:
        if call_id is None:
            return None
        return self._calls.get(call_id)

    def remove(self, call_id: str | None) -> CallSession | None:
        if call_id is None:
            return None
        return self._calls.pop(call_id, None)

    def current(self) -> CallSession | None:
        if not self._calls:
            return None
        return next(reversed(self._calls.values()))
