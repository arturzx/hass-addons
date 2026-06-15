from __future__ import annotations


class IsapiError(Exception):
    """Base exception for Hikvision ISAPI failures."""


class IsapiAuthError(IsapiError):
    """Authentication or authorization failed."""


class IsapiConnectionError(IsapiError):
    """Connection, DNS, or timeout failure."""


class IsapiResponseError(IsapiError):
    """The device returned an unexpected response."""


class IsapiUnsupportedError(IsapiError):
    """The requested ISAPI operation is not supported by this client."""
