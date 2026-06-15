# Home Assistant Add-on: SIP Indoor Station

<p align="center">
  <img src="icon.png" alt="SIP Indoor Station icon" width="96">
</p>

Simple SIP server for SIP capable door station acts as bridge to Home Assistant embedded intercom. Accessible from local and remote thanks to the WebRTC technology.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Farturzx%2Fhass-addons">
    <img src="https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg" alt="Add SIP Indoor Station add-on repository to Home Assistant">
  </a>
</p>

This add-on contains two parts:
- minimal SIP server with RTP audio support for door station
- WebRTC transceiver with HTTP API for communication with client (integration and custom door station card). 

Minimal configuration:

- `local_address`: Home Assistant host LAN address advertised in SIP/SDP and used as the first WebRTC host ICE candidate, for example `192.168.0.123`
- `webrtc_ice_candidates`: comma-separated host or host:port values to prepend as WebRTC host ICE candidates

The add-on always uses internal WebRTC ICE UDP port `8556`; use `host:port` in `webrtc_ice_candidates` when advertising a different public forwarded port.

The add-on exposes:

- `5060/udp` for SIP
- `40000/udp` for RTP from the door station
- `8556/udp` for WebRTC ICE media
- `8080/tcp` through Home Assistant ingress for the browser/WebRTC signaling page

Ingress proxies HTTP/WebSocket signaling only. WebRTC media still uses ICE-selected UDP paths or TURN relay.
Home Assistant add-on port mappings do not support RTP port ranges, so this add-on uses a single RTP port for the current single-call design.

The add-on stores unexpired SIP registrations in `/data/sip_registrations.json` and restores them after restart.

For remote access, configure TURN and set:

```text
webrtc_ice_transport_policy: relay
```

ISAPI (HikVision) is optional and disabled by default. Enable it only if local ISAPI access is enabled on the device. Currently support door opening and reboot functions.

## Complete Home Assistant Intercom

Use this add-on together with:

- [SIP Indoor Station Integration](https://github.com/arturzx/sip-indoor-station-integration): Home Assistant entities, actions, and WebRTC signaling proxy endpoints for the add-on.
- [SIP Indoor Station Card](https://github.com/arturzx/sip-indoor-station-card): Lovelace card for video, call controls, door opening, and in-dashboard intercom use.
