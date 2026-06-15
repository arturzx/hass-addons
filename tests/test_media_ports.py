import pytest

from sip_indoor_station.media.ports import PortAllocationError, RtpPortAllocator


def test_port_allocation_allocates_and_releases_udp_port() -> None:
    allocator = RtpPortAllocator(45000, 45001)
    allocator._can_bind = lambda _host, _port: True  # type: ignore[method-assign]
    port = allocator.allocate("127.0.0.1")
    assert port in {45000, 45001}
    allocator.release(port)
    assert allocator.allocate("127.0.0.1") == port


def test_port_allocation_skips_bound_port() -> None:
    allocator = RtpPortAllocator(45010, 45011)
    allocator._can_bind = lambda _host, port: port == 45011  # type: ignore[method-assign]
    assert allocator.allocate("127.0.0.1") == 45011


def test_port_allocation_raises_when_range_busy() -> None:
    allocator = RtpPortAllocator(45020, 45020)
    allocator._can_bind = lambda _host, _port: False  # type: ignore[method-assign]
    with pytest.raises(PortAllocationError):
        allocator.allocate("127.0.0.1")
