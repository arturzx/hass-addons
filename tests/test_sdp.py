from sip_indoor_station.sip.sdp import build_sdp_answer, parse_sdp, select_audio_codec


SDP = (
    "v=0\r\n"
    "o=- 1 1 IN IP4 192.168.1.20\r\n"
    "s=DoorStation\r\n"
    "c=IN IP4 192.168.1.20\r\n"
    "t=0 0\r\n"
    "m=audio 4002 RTP/AVP 0 8 96\r\n"
    "a=rtpmap:0 PCMU/8000\r\n"
    "a=rtpmap:8 PCMA/8000\r\n"
    "a=sendonly\r\n"
)


def test_parse_invite_sdp() -> None:
    offer = parse_sdp(SDP)
    assert offer.remote_ip == "192.168.1.20"
    assert offer.audio_port == 4002
    assert offer.payload_types == [0, 8, 96]
    assert offer.codec_mappings[8] == "PCMA"
    assert offer.direction == "sendonly"


def test_parse_invite_sdp_with_video() -> None:
    offer = parse_sdp(
        SDP
        + "m=video 4004 RTP/AVP 96 97\r\n"
        + "a=rtpmap:96 H264/90000\r\n"
        + "a=rtpmap:97 MP4V-ES/90000\r\n"
    )
    assert offer.video_offered is True
    assert offer.video_payload_types == [96, 97]


def test_selecting_pcma_over_pcmu() -> None:
    assert select_audio_codec(parse_sdp(SDP)) == ("PCMA", 8)


def test_falling_back_to_pcmu() -> None:
    offer = parse_sdp(SDP.replace("0 8 96", "0 96").replace("a=rtpmap:8 PCMA/8000\r\n", ""))
    assert select_audio_codec(offer) == ("PCMU", 0)


def test_sdp_answer_rejects_offered_video_with_zero_port() -> None:
    answer = build_sdp_answer("192.168.1.10", 40000, "PCMA", 8, reject_video_payload_types=[96, 97])
    assert "m=audio 40000 RTP/AVP 8\r\n" in answer
    assert "m=video 0 RTP/AVP 96 97\r\n" in answer
