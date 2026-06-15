from sip_indoor_station.app.config import Config, SipUser
from sip_indoor_station.sip.digest import calculate_digest_response, parse_digest_header
from sip_indoor_station.sip.messages import SipRequest, parse_sip_message
from sip_indoor_station.sip.server import SipServer


def make_server() -> SipServer:
    config = Config(
        sip_realm="sip.local",
        sip_users={"door": SipUser(username="door", password="secret", realm="sip.local")},
    )
    return SipServer(config)


def register_message(auth: str | None = None, expires: str | None = None) -> SipRequest:
    headers = [
        "REGISTER sip:server SIP/2.0",
        "Via: SIP/2.0/UDP 192.168.1.20:5060;branch=z9hG4bK-1",
        "From: <sip:door@sip.local>;tag=abc",
        "To: <sip:door@sip.local>",
        "Call-ID: call-1",
        "CSeq: 1 REGISTER",
        "Contact: <sip:door@192.168.1.20:5060>",
        "User-Agent: DoorStation",
    ]
    if expires is not None:
        headers.append(f"Expires: {expires}")
    if auth:
        headers.append(f"Authorization: {auth}")
    headers.append("Content-Length: 0")
    msg = parse_sip_message("\r\n".join(headers) + "\r\n\r\n")
    assert isinstance(msg, SipRequest)
    return msg


def authorization(server: SipServer, qop: bool = True) -> str:
    nonce = server.nonce_store.generate()
    if qop:
        response = calculate_digest_response(
            "REGISTER", "door", "sip.local", "secret", "sip:server", nonce, "auth", "00000001", "abc"
        )
        return (
            f'Digest username="door", realm="sip.local", nonce="{nonce}", uri="sip:server", '
            f'response="{response}", algorithm=MD5, qop=auth, nc=00000001, cnonce="abc"'
        )
    response = calculate_digest_response("REGISTER", "door", "sip.local", "secret", "sip:server", nonce)
    return (
        f'Digest username="door", realm="sip.local", nonce="{nonce}", uri="sip:server", '
        f'response="{response}", algorithm=MD5'
    )


def test_register_without_authorization_gets_challenge() -> None:
    server = make_server()
    response = server.handle_register(register_message(), ("192.168.1.20", 5060))
    assert response.status_code == 401
    assert parse_digest_header(response.headers["WWW-Authenticate"])["realm"] == "sip.local"


def test_storing_successful_registration() -> None:
    server = make_server()
    response = server.handle_register(register_message(authorization(server)), ("192.168.1.20", 5060))
    assert response.status_code == 200
    registration = server.registrations.get("door")
    assert registration is not None
    assert registration.contact_uri == "sip:door@192.168.1.20:5060"
    assert registration.source_ip == "192.168.1.20"
    assert registration.source_port == 5060
    assert registration.user_agent == "DoorStation"


def test_unregistering_with_expires_zero() -> None:
    server = make_server()
    server.handle_register(register_message(authorization(server)), ("192.168.1.20", 5060))
    assert server.registrations.get("door") is not None
    response = server.handle_register(register_message(authorization(server), expires="0"), ("192.168.1.20", 5060))
    assert response.status_code == 200
    assert server.registrations.get("door") is None
