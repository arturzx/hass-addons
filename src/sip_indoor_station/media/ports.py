from __future__ import annotations

import socket
from dataclasses import dataclass, field


class PortAllocationError(RuntimeError):
    pass


@dataclass
class RtpPortAllocator:
    port_min: int
    port_max: int
    _allocated: set[int] = field(default_factory=set)

    def allocate(self, bind_ip: str = "0.0.0.0") -> int:
        for port in range(self.port_min, self.port_max + 1):
            if port in self._allocated:
                continue
            if self._can_bind(bind_ip, port):
                self._allocated.add(port)
                return port
        raise PortAllocationError(f"no free UDP RTP port in range {self.port_min}-{self.port_max}")

    def release(self, port: int | None) -> None:
        if port is not None:
            self._allocated.discard(port)

    def _can_bind(self, bind_ip: str, port: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((bind_ip, port))
            return True
        except OSError:
            return False
        finally:
            sock.close()
