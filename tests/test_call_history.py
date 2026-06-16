from __future__ import annotations

import asyncio
import sqlite3
import uuid
from pathlib import Path

from aiohttp import web

from sip_indoor_station.app.events import AppEvent, EventBus
from sip_indoor_station.calls.history import CallHistoryStore
from sip_indoor_station.sip.server import Snapshot


class FakeSnapshotProvider:
    async def capture_snapshot(self) -> Snapshot:
        return Snapshot(b"jpeg-bytes", "image/jpeg")


def test_call_history_creates_uuid_entry_without_codec_metadata(tmp_path: Path) -> None:
    async def run() -> None:
        event_bus = EventBus()
        history = CallHistoryStore(str(tmp_path / "history.sqlite"), 30, event_bus)

        await event_bus.publish(
            AppEvent(
                "incoming_call",
                call_id="sip-call-1",
                data={
                    "remote_ip": "192.168.1.20",
                    "selected_audio_codec": "PCMU",
                    "selected_audio_payload_type": 0,
                },
            )
        )

        entries = history.list_entries()
        assert len(entries) == 1
        entry = entries[0].to_dict()
        assert uuid.UUID(entry["id"])
        assert entry["id"] != "sip-call-1"
        assert entry["sip_call_id"] == "sip-call-1"
        assert entry["status"] == "ringing"
        assert entry["remote_ip"] == "192.168.1.20"
        assert "selected_audio_codec" not in entry
        assert "selected_audio_payload_type" not in entry

    asyncio.run(run())


def test_cancelled_ringing_call_is_stored_as_missed(tmp_path: Path) -> None:
    async def run() -> None:
        event_bus = EventBus()
        history = CallHistoryStore(str(tmp_path / "history.sqlite"), 30, event_bus)

        await event_bus.publish(AppEvent("incoming_call", call_id="sip-call-1"))
        await event_bus.publish(AppEvent("call_cancelled", call_id="sip-call-1"))

        entry = history.list_entries()[0]
        assert entry.status == "missed"
        assert entry.ended_at is not None

    asyncio.run(run())


def test_answered_call_keeps_answered_status_after_end(tmp_path: Path) -> None:
    async def run() -> None:
        event_bus = EventBus()
        history = CallHistoryStore(str(tmp_path / "history.sqlite"), 30, event_bus)

        await event_bus.publish(AppEvent("incoming_call", call_id="sip-call-1"))
        await event_bus.publish(AppEvent("call_answered", call_id="sip-call-1"))
        await event_bus.publish(AppEvent("call_ended", call_id="sip-call-1"))

        entry = history.list_entries()[0]
        assert entry.status == "answered"
        assert entry.answered_at is not None
        assert entry.ended_at is not None

    asyncio.run(run())


def test_snapshot_is_stored_in_sqlite_database(tmp_path: Path) -> None:
    async def run() -> None:
        event_bus = EventBus()
        history = CallHistoryStore(str(tmp_path / "history.sqlite"), 30, event_bus, FakeSnapshotProvider())

        await event_bus.publish(AppEvent("incoming_call", call_id="sip-call-1"))
        for _ in range(10):
            if history.list_entries()[0].has_snapshot:
                break
            await asyncio.sleep(0)

        entry = history.list_entries()[0]
        assert entry.has_snapshot is True
        assert entry.snapshot_content_type == "image/jpeg"
        assert entry.snapshot_url == f"/api/call_history/{entry.id}/snapshot"
        assert history.snapshot_by_id(entry.id) == (b"jpeg-bytes", "image/jpeg")

    asyncio.run(run())


def test_delete_entry_removes_history_and_snapshot(tmp_path: Path) -> None:
    async def run() -> None:
        event_bus = EventBus()
        history = CallHistoryStore(str(tmp_path / "history.sqlite"), 30, event_bus, FakeSnapshotProvider())

        await event_bus.publish(AppEvent("incoming_call", call_id="sip-call-1"))
        for _ in range(10):
            if history.list_entries()[0].has_snapshot:
                break
            await asyncio.sleep(0)

        entry = history.list_entries()[0]
        assert history.delete_entry_by_id(entry.id) is True
        assert history.list_entries() == []
        assert history.snapshot_by_id(entry.id) is None

    asyncio.run(run())


def test_retention_deletes_old_entries(tmp_path: Path) -> None:
    db_path = tmp_path / "history.sqlite"
    event_bus = EventBus()
    history = CallHistoryStore(str(db_path), 1, event_bus)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO call_history (id, status, started_at, created_at, updated_at)
            VALUES ('old', 'missed', '2000-01-01T00:00:00Z', '2000-01-01T00:00:00Z', '2000-01-01T00:00:00Z')
            """
        )

    history.cleanup_retention()

    assert history.get_entry_by_id("old") is None


def test_call_history_registers_api_routes(tmp_path: Path) -> None:
    event_bus = EventBus()
    history = CallHistoryStore(str(tmp_path / "history.sqlite"), 30, event_bus)
    app = web.Application()

    history.register_routes(app)

    routes = {(route.method, route.resource.canonical) for route in app.router.routes()}
    assert ("GET", "/api/call_history") in routes
    assert ("DELETE", "/api/call_history") in routes
    assert ("GET", "/api/call_history/{history_id}") in routes
    assert ("DELETE", "/api/call_history/{history_id}") in routes
    assert ("GET", "/api/call_history/{history_id}/snapshot") in routes
