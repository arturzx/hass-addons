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

This add-on contains three parts:
- minimal SIP server with RTP audio support for door station
- WebRTC transceiver with HTTP API for communication with client (integration and custom door station card). 
- optional calls history

Minimal configuration:

- `local_address`: Home Assistant host LAN address advertised in SIP/SDP and used as the first WebRTC host ICE candidate, for example `192.168.0.123`
- `webrtc_ice_candidates`: comma-separated host or host:port values to prepend as WebRTC host ICE candidates
- `call_history_enabled`: store recent calls in add-on SQLite storage. Enabled by default.
- `call_history_days`: number of days to keep call history. Defaults to `30`.
- `door_station_vendor`: required when API is enabled. Use `hikvision` (snapshots + maintenance + open door) or `dahua` (snapshots + open door).

The add-on always uses internal WebRTC ICE UDP port `8556`; use `host:port` in `webrtc_ice_candidates` when advertising a different public forwarded port.

The add-on exposes:

- `5060/udp` for SIP
- `40000/udp` for RTP from the door station
- `8556/udp` for WebRTC ICE media
- `8080/tcp` through Home Assistant ingress for the browser/WebRTC signaling page

## Door Station SIP Configuration

Configure the SIP account on the door station to register to this add-on:

- SIP server/proxy/registrar: the `local_address` value from the add-on configuration, for example `192.168.0.123`
- SIP port: `5060`
- Username/auth ID: `sip_username`
- Password: `sip_password`
- Realm/domain: `sip_realm`

For the default add-on options, configure the door station with username `door`, password `door`, and realm `sip.local`.

Ingress proxies HTTP/WebSocket signaling only. WebRTC media still uses ICE-selected UDP paths or TURN relay.
Home Assistant add-on port mappings do not support RTP port ranges, so this add-on uses a single RTP port for the current single-call design.

The add-on stores unexpired SIP registrations in `/data/sip_registrations.json` and restores them after restart.

For remote access, configure TURN and set:

```text
webrtc_ice_transport_policy: relay
```

API support is optional and disabled by default. Enable it only if local API access is enabled on the device. Door opening and snapshots are supported for both HikVision and Dahua. Reboot is supported only for HikVision.

## Call History

The add-on can store call history SQLite database.

Stored call states include:

- `ringing`
- `answered`
- `missed`
- `rejected`
- `failed`
- `ended`

History retention is controlled by:

```text
call_history_days: 30
```

The integration exposes this history to Home Assistant with summary entities such as last call, last missed call, and missed call count. The custom card includes a separate history card for browsing calls, viewing snapshots, and deleting entries.

### Snapshots

Snapshots are stored in the same database when a snapshot provider is available.

For HikVision snapshots and API actions, configure:

```text
door_station_vendor: hikvision
api_enabled: true
api_host: 192.168.0.234
api_username: admin
api_password: change-me
relays_count: 1
```

For HikVision snapshots, use:

```text
/ISAPI/Streaming/channels/101/picture
```

For Dahua snapshots, use:

```text
/cgi-bin/snapshot.cgi?channel=1
```

API credentials are also used for snapshots, door opening, and reboot actions.

## Complete Home Assistant Intercom

Use this add-on together with:

- [SIP Indoor Station Integration](https://github.com/arturzx/sip-indoor-station-integration): Home Assistant entities, actions, and WebRTC signaling proxy endpoints for the add-on.
- [SIP Indoor Station Card](https://github.com/arturzx/sip-indoor-station-card): Lovelace card for video, call controls, door opening, and in-dashboard intercom use.
