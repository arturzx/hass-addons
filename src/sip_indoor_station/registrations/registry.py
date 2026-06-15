from __future__ import annotations

import re
import time
from dataclasses import dataclass

from sip_indoor_station.sip.messages import SipRequest


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
    def __init__(self, default_ttl: int = 3600) -> None:
        self.default_ttl = default_ttl
        self._registrations: dict[str, Registration] = {}

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
        return registration

    def unregister(self, username: str) -> None:
        self._registrations.pop(username, None)

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
