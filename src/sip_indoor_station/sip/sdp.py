from __future__ import annotations

import secrets
from dataclasses import dataclass, field


@dataclass
class SdpOffer:
    remote_ip: str | None = None
    audio_port: int | None = None
    payload_types: list[int] = field(default_factory=list)
    video_offered: bool = False
    video_payload_types: list[int] = field(default_factory=list)
    video_codec_mappings: dict[int, str] = field(default_factory=dict)
    video_fmtp: dict[int, str] = field(default_factory=dict)
    codec_mappings: dict[int, str] = field(default_factory=dict)
    direction: str = "sendrecv"


def parse_sdp(body: str) -> SdpOffer:
    offer = SdpOffer()
    for raw_line in body.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("c="):
            parts = line[2:].split()
            if len(parts) >= 3 and parts[1].upper() == "IP4":
                offer.remote_ip = parts[2]
        elif line.startswith("m=audio"):
            parts = line[2:].split()
            if len(parts) >= 4:
                offer.audio_port = int(parts[1])
                offer.payload_types = [int(pt) for pt in parts[3:] if pt.isdigit()]
        elif line.startswith("m=video"):
            parts = line[2:].split()
            if len(parts) >= 4:
                offer.video_offered = True
                offer.video_payload_types = [int(pt) for pt in parts[3:] if pt.isdigit()]
        elif line.startswith("a=rtpmap:"):
            payload, codec = line[len("a=rtpmap:") :].split(None, 1)
            if payload.isdigit():
                payload_type = int(payload)
                codec_name = codec.split("/", 1)[0].upper()
                if offer.video_offered and payload_type in offer.video_payload_types:
                    offer.video_codec_mappings[payload_type] = codec
                else:
                    offer.codec_mappings[payload_type] = codec_name
        elif line.startswith("a=fmtp:"):
            payload, fmtp = line[len("a=fmtp:") :].split(None, 1)
            if payload.isdigit() and int(payload) in offer.video_payload_types:
                offer.video_fmtp[int(payload)] = fmtp.replace("; ", ";")
        elif line in ("a=sendrecv", "a=sendonly", "a=recvonly", "a=inactive"):
            offer.direction = line[2:]
    return offer


def select_audio_codec(offer: SdpOffer) -> tuple[str, int] | None:
    if 8 in offer.payload_types:
        return ("PCMA", 8)
    if 0 in offer.payload_types:
        return ("PCMU", 0)
    return None


def build_sdp_answer(
    local_ip: str,
    local_port: int,
    codec: str,
    payload_type: int,
    reject_video_payload_types: list[int] | None = None,
    reject_video_codec_mappings: dict[int, str] | None = None,
    reject_video_fmtp: dict[int, str] | None = None,
) -> str:
    session_id = secrets.randbelow(10_000_000_000)
    lines = [
        "v=0",
        f"o=- {session_id} 1 IN IP4 {local_ip}",
        "s=SIP Indoor Station",
        f"c=IN IP4 {local_ip}",
        "t=0 0",
        f"m=audio {local_port} RTP/AVP {payload_type}",
        f"a=rtpmap:{payload_type} {codec}/8000",
        "a=sendrecv",
    ]
    if reject_video_payload_types is not None:
        payloads = " ".join(str(payload_type) for payload_type in reject_video_payload_types) or "0"
        lines.append(f"m=video 0 RTP/AVP {payloads}")
        for video_payload_type in reject_video_payload_types:
            codec = (reject_video_codec_mappings or {}).get(video_payload_type)
            if codec:
                lines.append(f"a=rtpmap:{video_payload_type} {codec}")
            fmtp = (reject_video_fmtp or {}).get(video_payload_type)
            if fmtp:
                lines.append(f"a=fmtp:{video_payload_type} {fmtp}")
    lines.append("")
    return "\r\n".join(lines)
