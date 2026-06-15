from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sip_indoor_station.sip.messages import SipRequest

LOGGER = logging.getLogger(__name__)


@dataclass
class Registration:
    username: str
    contact_uri: str
    source_ip: str
    source_port: int
    expires_at: float
    user_agent: str | None
    last_register_time: float


class RegistrationRegistry:
    def __init__(self, default_ttl: int = 3600, storage_path: str | Path | None = None) -> None:
        self.default_ttl = default_ttl
        self._registrations: dict[str, Registration] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        self.load()

    def register(
        self,
        username: str,
        contact_uri: str,
        source_ip: str,
        source_port: int,
        user_agent: str | None,
        expires: int | None = None,
    ) -> Registration | None:
        ttl = self.default_ttl if expires is None else expires
        if ttl <= 0:
            self.unregister(username)
            return None
        now = time.time()
        registration = Registration(
            username=username,
            contact_uri=contact_uri,
            source_ip=source_ip,
            source_port=source_port,
            expires_at=now + ttl,
            user_agent=user_agent,
            last_register_time=now,
        )
        self._registrations[username] = registration
        self.save()
        return registration

    def unregister(self, username: str) -> None:
        if self._registrations.pop(username, None) is not None:
            self.save()

    def get(self, username: str) -> Registration | None:
        registration = self._registrations.get(username)
        if registration and registration.expires_at < time.time():
            self.unregister(username)
            return None
        return registration

    def find_by_source(self, source_ip: str, source_port: int) -> Registration | None:
        for registration in list(self._registrations.values()):
            if registration.expires_at < time.time():
                self.unregister(registration.username)
                continue
            if registration.source_ip == source_ip and registration.source_port == source_port:
                return registration
        return None

    def active(self) -> list[Registration]:
        for registration in list(self._registrations.values()):
            if registration.expires_at < time.time():
                self.unregister(registration.username)
        return list(self._registrations.values())

    def load(self) -> None:
        if self.storage_path is None or not self.storage_path.exists():
            return
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("registration_store_load_failed path=%s error=%s", self.storage_path, exc)
            return

        registrations = payload.get("registrations") if isinstance(payload, dict) else None
        if not isinstance(registrations, list):
            LOGGER.warning("registration_store_load_failed path=%s error=invalid_payload", self.storage_path)
            return

        now = time.time()
        restored = 0
        for item in registrations:
            registration = self._registration_from_json(item)
            if registration is None or registration.expires_at <= now:
                continue
            self._registrations[registration.username] = registration
            restored += 1
        LOGGER.info("registration_store_loaded path=%s restored=%s", self.storage_path, restored)

    def save(self) -> None:
        if self.storage_path is None:
            return
        now = time.time()
        registrations = [
            asdict(registration)
            for registration in self._registrations.values()
            if registration.expires_at > now
        ]
        payload = {"version": 1, "registrations": registrations}
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.storage_path.with_suffix(f"{self.storage_path.suffix}.tmp")
            temporary_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
            temporary_path.replace(self.storage_path)
        except OSError as exc:
            LOGGER.warning("registration_store_save_failed path=%s error=%s", self.storage_path, exc)

    def _registration_from_json(self, item: Any) -> Registration | None:
        if not isinstance(item, dict):
            return None
        try:
            return Registration(
                username=str(item["username"]),
                contact_uri=str(item["contact_uri"]),
                source_ip=str(item["source_ip"]),
                source_port=int(item["source_port"]),
                expires_at=float(item["expires_at"]),
                user_agent=str(item["user_agent"]) if item.get("user_agent") is not None else None,
                last_register_time=float(item["last_register_time"]),
            )
        except (KeyError, TypeError, ValueError):
            return None


def contact_uri_from_header(contact: str | None) -> str | None:
    if not contact:
        return None
    match = re.search(r"<([^>]+)>", contact)
    if match:
        return match.group(1)
    return contact.split(";", 1)[0].strip()


def expires_from_register(request: SipRequest, default: int = 3600) -> int:
    contact = request.headers.get("Contact") or ""
    match = re.search(r"(?:^|;)\s*expires\s*=\s*(\d+)", contact, re.IGNORECASE)
    if match:
        return int(match.group(1))
    expires = request.headers.get("Expires")
    if expires is not None:
        return int(expires)
    return default
