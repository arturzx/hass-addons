#!/usr/bin/env bash
set -euo pipefail

OPTIONS=/data/options.json

opt() {
  jq -r --arg key "$1" '.[$key] // empty' "$OPTIONS"
}

export LISTEN_ADDRESS=0.0.0.0
export LOCAL_ADDRESS="$(opt local_address)"
export SIP_PORT=5060
export SIP_USERNAME="$(opt sip_username)"
export SIP_PASSWORD="$(opt sip_password)"
export SIP_REALM="$(opt sip_realm)"
export SIP_REGISTRATION_STORE_PATH=/data/sip_registrations.json

export RTP_PORT_MIN=40000
export RTP_PORT_MAX=40000

export HTTP_PORT=8080

export WEBRTC_ICE_CANDIDATES="$(opt webrtc_ice_candidates)"
export WEBRTC_ICE_UDP_PORT=8556
export WEBRTC_STUN_SERVERS="$(opt webrtc_stun_servers)"
export WEBRTC_TURN_SERVERS="$(opt webrtc_turn_servers)"
export WEBRTC_TURN_USERNAME="$(opt webrtc_turn_username)"
export WEBRTC_TURN_PASSWORD="$(opt webrtc_turn_password)"
export WEBRTC_ICE_TRANSPORT_POLICY="$(opt webrtc_ice_transport_policy)"

export API_ENABLED="$(opt api_enabled)"
export API_HOST="$(opt api_host)"
export API_USERNAME="$(opt api_username)"
export API_PASSWORD="$(opt api_password)"
export RELAYS_COUNT="$(opt relays_count)"

export DOOR_STATION_VENDOR="$(opt door_station_vendor)"
export CALL_HISTORY_ENABLED="$(opt call_history_enabled)"
export CALL_HISTORY_DAYS="$(opt call_history_days)"
export CALL_HISTORY_DB_PATH=/data/call_history.sqlite

exec sip-indoor-station
