from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass


def md5_hex(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def parse_digest_header(header_value: str) -> dict[str, str]:
    value = header_value.strip()
    if value.lower().startswith("digest "):
        value = value[7:].strip()

    params: dict[str, str] = {}
    token = []
    in_quotes = False
    escaped = False
    parts: list[str] = []
    for char in value:
        if escaped:
            token.append(char)
            escaped = False
        elif char == "\\" and in_quotes:
            escaped = True
        elif char == '"':
            in_quotes = not in_quotes
            token.append(char)
        elif char == "," and not in_quotes:
            parts.append("".join(token).strip())
            token = []
        else:
            token.append(char)
    if token:
        parts.append("".join(token).strip())

    for part in parts:
        if "=" not in part:
            continue
        name, raw_value = part.split("=", 1)
        raw_value = raw_value.strip()
        if len(raw_value) >= 2 and raw_value[0] == '"' and raw_value[-1] == '"':
            raw_value = raw_value[1:-1]
        params[name.strip().lower()] = raw_value
    return params


@dataclass
class NonceStore:
    ttl: int = 300

    def __post_init__(self) -> None:
        self._nonces: dict[str, float] = {}

    def generate(self) -> str:
        nonce = secrets.token_urlsafe(24)
        self._nonces[nonce] = time.time() + self.ttl
        return nonce

    def validate(self, nonce: str) -> bool:
        self.prune()
        expires_at = self._nonces.get(nonce)
        return expires_at is not None and expires_at >= time.time()

    def prune(self) -> None:
        now = time.time()
        expired = [nonce for nonce, expires_at in self._nonces.items() if expires_at < now]
        for nonce in expired:
            self._nonces.pop(nonce, None)


def build_www_authenticate(realm: str, nonce: str) -> str:
    return f'Digest realm="{realm}", nonce="{nonce}", algorithm=MD5, qop="auth"'


def calculate_digest_response(
    method: str,
    username: str,
    realm: str,
    password: str,
    uri: str,
    nonce: str,
    qop: str | None = None,
    nc: str | None = None,
    cnonce: str | None = None,
) -> str:
    ha1 = md5_hex(f"{username}:{realm}:{password}")
    ha2 = md5_hex(f"{method}:{uri}")
    if qop:
        return md5_hex(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}")
    return md5_hex(f"{ha1}:{nonce}:{ha2}")


def validate_digest_response(
    method: str,
    params: dict[str, str],
    username: str,
    password: str,
    realm: str,
    nonce_store: NonceStore,
    expected_uri: str | None = None,
) -> bool:
    required = {"username", "realm", "nonce", "uri", "response"}
    if not required.issubset(params):
        return False
    if params["username"] != username or params["realm"] != realm:
        return False
    if expected_uri is not None and params["uri"] != expected_uri:
        return False
    if params.get("algorithm", "MD5").upper() != "MD5":
        return False
    if not nonce_store.validate(params["nonce"]):
        return False

    qop = params.get("qop")
    if qop:
        if qop != "auth" or not params.get("nc") or not params.get("cnonce"):
            return False

    expected = calculate_digest_response(
        method=method,
        username=username,
        realm=realm,
        password=password,
        uri=params["uri"],
        nonce=params["nonce"],
        qop=qop,
        nc=params.get("nc"),
        cnonce=params.get("cnonce"),
    )
    return hmac.compare_digest(expected, params["response"])
