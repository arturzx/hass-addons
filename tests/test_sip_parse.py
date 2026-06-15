from sip_indoor_station.sip.messages import SipRequest, SipResponse, build_sip_message, parse_sip_message, response_from_request


REGISTER = (
    "REGISTER sip:192.168.1.10 SIP/2.0\r\n"
    "Via: SIP/2.0/UDP 192.168.1.20:5060;branch=z9hG4bK-1\r\n"
    "Via: SIP/2.0/UDP 10.0.0.2:5060;branch=z9hG4bK-2\r\n"
    "From: <sip:door@sip.local>;tag=abc\r\n"
    "To: <sip:door@sip.local>\r\n"
    "Call-ID: call-1\r\n"
    "CSeq: 1 REGISTER\r\n"
    "Contact: <sip:door@192.168.1.20:5060>\r\n"
    "Max-Forwards: 70\r\n"
    "User-Agent: DoorStation\r\n"
    "Content-Length: 0\r\n"
    "\r\n"
)


def test_parse_register_request() -> None:
    message = parse_sip_message(REGISTER)
    assert isinstance(message, SipRequest)
    assert message.method == "REGISTER"
    assert message.uri == "sip:192.168.1.10"
    assert message.headers.get("from") == "<sip:door@sip.local>;tag=abc"
    assert message.headers.get_all("Via") == [
        "SIP/2.0/UDP 192.168.1.20:5060;branch=z9hG4bK-1",
        "SIP/2.0/UDP 10.0.0.2:5060;branch=z9hG4bK-2",
    ]


def test_parse_status_response() -> None:
    message = parse_sip_message("SIP/2.0 200 OK\r\nCall-ID: call-1\r\nContent-Length: 0\r\n\r\n")
    assert isinstance(message, SipResponse)
    assert message.status_code == 200
    assert message.reason == "OK"


def test_response_builder_copies_required_headers() -> None:
    request = parse_sip_message(REGISTER)
    assert isinstance(request, SipRequest)
    response = response_from_request(request, 200, "OK")
    raw = build_sip_message(response).decode()
    assert raw.startswith("SIP/2.0 200 OK")
    assert raw.count("Via:") == 2
    assert "From: <sip:door@sip.local>;tag=abc" in raw
    assert "To: <sip:door@sip.local>" in raw
    assert "Call-ID: call-1" in raw
    assert "CSeq: 1 REGISTER" in raw
