from __future__ import annotations

import asyncio
import logging

from sip_indoor_station.app.http_server import AppHttpServer
from sip_indoor_station.api.state_api import StateApi
from sip_indoor_station.app.config import load_config
from sip_indoor_station.app.events import AppEvent, EventBus
from sip_indoor_station.sip.server import SipServer


async def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = load_config()
    event_bus = EventBus()
    door_opener = None
    maintenance = None
    if config.isapi_enabled and config.isapi_host:
        from sip_indoor_station.vendor.hikvision.client import HikvisionIsapiClient
        from sip_indoor_station.vendor.hikvision.door import HikvisionDoorApi
        from sip_indoor_station.vendor.hikvision.maintenance import HikvisionMaintenanceApi
        from sip_indoor_station.vendor.hikvision.models import IsapiClientConfig

        isapi_client = HikvisionIsapiClient(
            IsapiClientConfig(
                host=config.isapi_host,
                port=config.isapi_port,
                username=config.isapi_username,
                password=config.isapi_password,
                use_https=config.isapi_use_https,
                timeout_seconds=config.isapi_timeout_seconds,
                verify_ssl=config.isapi_verify_ssl,
            )
        )
        door_opener = HikvisionDoorApi(isapi_client, door_id=config.isapi_door_id)
        maintenance = HikvisionMaintenanceApi(isapi_client)
    sip_server = SipServer(config, event_bus=event_bus, door_opener=door_opener, maintenance=maintenance)
    state_api = StateApi(event_bus, sip_server)
    for registration in sip_server.registrations.active():
        await event_bus.publish(
            AppEvent(
                "registration_success",
                data={
                    "username": registration.username,
                    "contact_uri": registration.contact_uri,
                    "source": f"{registration.source_ip}:{registration.source_port}",
                    "user_agent": registration.user_agent,
                    "restored": True,
                },
            )
        )
    http_server = AppHttpServer(config, event_bus, sip_server.active_media_session, state_api)
    await sip_server.start()
    await http_server.start()
    try:
        await asyncio.Event().wait()
    finally:
        await http_server.stop()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
