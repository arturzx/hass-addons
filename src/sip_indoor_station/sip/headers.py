from __future__ import annotations

from collections.abc import Iterable


class Headers:
    def __init__(self, items: Iterable[tuple[str, str]] | None = None) -> None:
        self._items: list[tuple[str, str]] = []
        if items:
            for name, value in items:
                self.add(name, value)

    def add(self, name: str, value: str) -> None:
        self._items.append((name.strip(), value.strip()))

    def set(self, name: str, value: str) -> None:
        key = name.lower()
        self._items = [(n, v) for n, v in self._items if n.lower() != key]
        self.add(name, value)

    def get(self, name: str, default: str | None = None) -> str | None:
        key = name.lower()
        for header_name, value in self._items:
            if header_name.lower() == key:
                return value
        return default

    def get_all(self, name: str) -> list[str]:
        key = name.lower()
        return [value for header_name, value in self._items if header_name.lower() == key]

    def items(self) -> list[tuple[str, str]]:
        return list(self._items)

    def __contains__(self, name: str) -> bool:
        return self.get(name) is not None

    def __getitem__(self, name: str) -> str:
        value = self.get(name)
        if value is None:
            raise KeyError(name)
        return value
