from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from sip_indoor_station.vendor.hikvision.errors import IsapiAuthError, IsapiConnectionError, IsapiResponseError
from sip_indoor_station.vendor.hikvision.models import IsapiBinaryResponse, IsapiClientConfig, IsapiResponse

LOGGER = logging.getLogger(__name__)


class HikvisionIsapiClient:
    def __init__(self, config: IsapiClientConfig) -> None:
        self.config = config

    @property
    def base_url(self) -> str:
        scheme = "https" if self.config.use_https else "http"
        return f"{scheme}://{self.config.host}:{self.config.port}"

    @property
    def configured(self) -> bool:
        return bool(self.config.host and self.config.username and self.config.password)

    async def get(self, path: str, *, expect_json: bool = False) -> IsapiResponse:
        return await self.request("GET", path, expect_json=expect_json)

    async def get_bytes(self, path: str) -> IsapiBinaryResponse:
        if not self.configured:
            raise IsapiConnectionError("ISAPI host, username, and password must be configured")
        url = self.url(path)
        LOGGER.debug("isapi_request method=GET url=%s", url)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        connector = aiohttp.TCPConnector(ssl=self.config.verify_ssl)
        middlewares = (aiohttp.DigestAuthMiddleware(self.config.username or "", self.config.password or ""),)

        try:
            async with aiohttp.ClientSession(timeout=timeout, connector=connector, middlewares=middlewares) as session:
                async with session.get(url) as response:
                    body = await response.read()
                    self.raise_for_status(response.status, body[:200].decode("utf-8", errors="replace"), path)
                    return IsapiBinaryResponse(response.status, body, response.headers.get("Content-Type"))
        except (IsapiAuthError, IsapiResponseError):
            raise
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise IsapiConnectionError(f"ISAPI request timed out: {path}") from exc
        except aiohttp.ClientError as exc:
            raise IsapiConnectionError(f"ISAPI connection failed for {path}: {exc}") from exc

    async def put(
        self,
        path: str,
        *,
        xml: str | None = None,
        json_payload: dict[str, Any] | None = None,
        expect_json: bool = False,
    ) -> IsapiResponse:
        return await self.request("PUT", path, xml=xml, json_payload=json_payload, expect_json=expect_json)

    async def post(
        self,
        path: str,
        *,
        xml: str | None = None,
        json_payload: dict[str, Any] | None = None,
        expect_json: bool = False,
    ) -> IsapiResponse:
        return await self.request("POST", path, xml=xml, json_payload=json_payload, expect_json=expect_json)

    async def request(
        self,
        method: str,
        path: str,
        *,
        xml: str | None = None,
        json_payload: dict[str, Any] | None = None,
        expect_json: bool = False,
    ) -> IsapiResponse:
        if not self.configured:
            raise IsapiConnectionError("ISAPI host, username, and password must be configured")
        url = self.url(path)
        headers: dict[str, str] = {}
        data: str | None = None
        if xml is not None:
            headers["Content-Type"] = "application/xml"
            data = xml
        elif json_payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(json_payload, separators=(",", ":"))

        LOGGER.debug("isapi_request method=%s url=%s", method, url)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        connector = aiohttp.TCPConnector(ssl=self.config.verify_ssl)
        middlewares = (aiohttp.DigestAuthMiddleware(self.config.username or "", self.config.password or ""),)

        try:
            async with aiohttp.ClientSession(timeout=timeout, connector=connector, middlewares=middlewares) as session:
                async with session.request(method, url, data=data, headers=headers) as response:
                    text = await response.text()
                    self.raise_for_status(response.status, text, path)
                    parsed_json = self.parse_json(text, path) if expect_json else None
                    return IsapiResponse(response.status, text, parsed_json)
        except (IsapiAuthError, IsapiResponseError):
            raise
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise IsapiConnectionError(f"ISAPI request timed out: {path}") from exc
        except aiohttp.ClientError as exc:
            raise IsapiConnectionError(f"ISAPI connection failed for {path}: {exc}") from exc

    def url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    @staticmethod
    def raise_for_status(status: int, body: str, path: str) -> None:
        if status in {401, 403}:
            raise IsapiAuthError(f"ISAPI authentication failed for {path}: HTTP {status}")
        if not 200 <= status < 300:
            body_preview = body[:200].replace("\n", " ")
            raise IsapiResponseError(f"ISAPI request failed for {path}: HTTP {status}: {body_preview}")

    @staticmethod
    def parse_json(text: str, path: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise IsapiResponseError(f"ISAPI returned invalid JSON for {path}") from exc
