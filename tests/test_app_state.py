from __future__ import annotations

from sip_indoor_station.app.events import AppEvent
from sip_indoor_station.app.state import AppState, apply_event_to_state, command_rejected_payload, event_payload


def test_state_payload_includes_derived_booleans() -> None:
    state = AppState(registered=True, call_state="ringing")
    payload = state.to_dict()
    assert payload["registered"] is True
    assert payload["ringing"] is True
    assert payload["in_call"] is False


def test_incoming_call_event_updates_state() -> None:
    state = AppState()
    apply_event_to_state(
        state,
        AppEvent(
            "incoming_call",
            call_id="call-1",
            data={"remote_ip": "192.168.0.10", "selected_audio_codec": "PCMU", "selected_audio_payload_type": 0},
        ),
    )
    assert state.call_state == "ringing"
    assert state.ringing is True
    assert state.call_id == "call-1"
    assert state.remote_ip == "192.168.0.10"
    assert state.selected_audio_codec == "PCMU"
    assert state.selected_audio_payload_type == 0


def test_answered_event_sets_in_call() -> None:
    state = AppState(call_state="ringing", call_id="call-1")
    apply_event_to_state(state, AppEvent("call_answered", call_id="call-1"))
    assert state.call_state == "answered"
    assert state.in_call is True


def test_event_payloads_are_plain_dicts_for_http_api() -> None:
    event = event_payload("registered", data={"source": "test"})
    assert event["event"] == "registered"
    assert event["data"] == {"source": "test"}
    assert event["timestamp"].endswith("Z")

    rejected = command_rejected_payload("answer", "no_ringing_call")
    assert rejected["event"] == "command_rejected"
    assert rejected["command"] == "answer"
    assert rejected["reason"] == "no_ringing_call"
