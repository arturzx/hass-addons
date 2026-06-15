from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Transaction:
    branch: str
    method: str
    state: str = "trying"
