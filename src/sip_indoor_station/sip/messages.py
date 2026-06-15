from __future__ import annotations

from dataclasses import dataclass, field

from sip_indoor_station.sip.headers import Headers


@dataclass
class SipMessage:
    version: str = "SIP/2.0"
    headers: Headers = field(default_factory=Headers)
    body: str = ""

    @property
    def is_request(self) -> bool:
        return isinstance(self, SipRequest)


@dataclass
class SipRequest(SipMessage):
    method: str = ""
    uri: str = ""


@dataclass
class SipResponse(SipMessage):
    status_code: int = 0
    reason: str = ""


def parse_sip_message(data: bytes | str) -> SipMessage:
    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
    head, separator, body = text.partition("\r\n\r\n")
    if not separator:
        head, separator, body = text.partition("\n\n")
    lines = head.replace("\r\n", "\n").split("\n")
    if not lines or not lines[0].strip():
        raise ValueError("empty SIP message")

    start_line = lines[0].strip()
    headers = Headers()
    current_name: str | None = None
    current_value: list[str] = []

    def flush_header() -> None:
        nonlocal current_name, current_value
        if current_name is not None:
            headers.add(current_name, " ".join(current_value))
        current_name = None
        current_value = []

    for line in lines[1:]:
        if not line:
            continue
        if line[0] in " \t" and current_name is not None:
            current_value.append(line.strip())
            continue
        flush_header()
        if ":" not in line:
            raise ValueError(f"invalid SIP header line: {line}")
        name, value = line.split(":", 1)
        current_name = name.strip()
        current_value = [value.strip()]
    flush_header()

    content_length = headers.get("Content-Length")
    if content_length is not None:
        try:
            body = body[: int(content_length)]
        except ValueError:
            raise ValueError("invalid Content-Length") from None

    if start_line.startswith("SIP/"):
        parts = start_line.split(" ", 2)
        if len(parts) < 2:
            raise ValueError("invalid SIP status line")
        return SipResponse(
            version=parts[0],
            status_code=int(parts[1]),
            reason=parts[2] if len(parts) > 2 else "",
            headers=headers,
            body=body,
        )

    parts = start_line.split(" ", 2)
    if len(parts) != 3:
        raise ValueError("invalid SIP request line")
    return SipRequest(method=parts[0], uri=parts[1], version=parts[2], headers=headers, body=body)


def build_sip_message(message: SipMessage) -> bytes:
    if isinstance(message, SipRequest):
        start_line = f"{message.method} {message.uri} {message.version}"
    elif isinstance(message, SipResponse):
        start_line = f"{message.version} {message.status_code} {message.reason}".rstrip()
    else:
        raise TypeError("unsupported SIP message type")

    body = message.body or ""
    headers = Headers(message.headers.items())
    headers.set("Content-Length", str(len(body.encode("utf-8"))))
    lines = [start_line]
    lines.extend(f"{name}: {value}" for name, value in headers.items())
    return ("\r\n".join(lines) + "\r\n\r\n" + body).encode("utf-8")


def response_from_request(
    request: SipRequest,
    status_code: int,
    reason: str,
    extra_headers: list[tuple[str, str]] | None = None,
    body: str = "",
    content_type: str | None = None,
) -> SipResponse:
    headers = Headers()
    for via in request.headers.get_all("Via"):
        headers.add("Via", via)
    for name in ("From", "To", "Call-ID", "CSeq"):
        value = request.headers.get(name)
        if value is not None:
            headers.add(name, value)
    if content_type:
        headers.add("Content-Type", content_type)
    for name, value in extra_headers or []:
        headers.add(name, value)
    return SipResponse(status_code=status_code, reason=reason, headers=headers, body=body)
