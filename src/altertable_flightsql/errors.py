"""Typed exceptions for altertable_flightsql.

The pyarrow.flight client raises typed exceptions (``FlightInternalError``,
``FlightTimedOutError``, etc.) whose ``str()`` produces a long gRPC debug
string that mixes the gRPC status, the server message, peer addresses, and
timestamps. Callers that want to react to errors programmatically (retry on
``ABORTED``, surface ``RESOURCE_EXHAUSTED`` differently from ``INTERNAL``,
decode the ``x-arrow-flight-error-extra-info`` trailer) end up substring-
matching that string.

``AltertableFlightError`` rewraps a pyarrow.flight exception with structured
fields:

- ``grpc_status``  -- gRPC status name (``"INTERNAL"``, ``"ABORTED"``, ...).
- ``server_message`` -- the server-provided message, no transport noise.
- ``extra_info``  -- raw bytes from the Flight ``error_details`` trailer
  when the server populates it; empty otherwise.

Use ``wrap_flight_error`` from an ``except`` block, or call it on a caught
exception to inspect it.
"""

from __future__ import annotations

import pyarrow.flight as flight

# pyarrow.flight exception class -> canonical gRPC status name.
# Sourced from pyarrow's own mapping of gRPC codes to FlightError subclasses.
_FLIGHT_ERROR_TO_GRPC_STATUS: dict[type[BaseException], str] = {
    flight.FlightCancelledError: "CANCELLED",
    flight.FlightTimedOutError: "DEADLINE_EXCEEDED",
    flight.FlightInternalError: "INTERNAL",
    flight.FlightServerError: "UNKNOWN",
    flight.FlightUnavailableError: "UNAVAILABLE",
    flight.FlightUnauthenticatedError: "UNAUTHENTICATED",
    flight.FlightUnauthorizedError: "PERMISSION_DENIED",
    flight.FlightWriteSizeExceededError: "RESOURCE_EXHAUSTED",
}


class AltertableFlightError(Exception):
    """A pyarrow.flight error rewrapped for structured introspection."""

    def __init__(
        self,
        *,
        grpc_status: str,
        server_message: str,
        extra_info: bytes = b"",
    ) -> None:
        self.grpc_status = grpc_status
        self.server_message = server_message
        self.extra_info = extra_info
        super().__init__(f"[{grpc_status}] {server_message}")


def wrap_flight_error(error: BaseException) -> AltertableFlightError:
    """Convert a pyarrow.flight exception into an ``AltertableFlightError``.

    The pyarrow exception class determines ``grpc_status``; the message and
    optional ``extra_info`` bytes come from the exception's own fields.
    Unknown exception types resolve to ``grpc_status="UNKNOWN"`` with the
    original ``str(error)`` as the message.
    """
    grpc_status = "UNKNOWN"
    for err_type, status in _FLIGHT_ERROR_TO_GRPC_STATUS.items():
        if isinstance(error, err_type):
            grpc_status = status
            break
    return AltertableFlightError(
        grpc_status=grpc_status,
        server_message=_extract_server_message(error),
        extra_info=getattr(error, "extra_info", b"") or b"",
    )


def _extract_server_message(error: BaseException) -> str:
    msg = getattr(error, "message", None)
    if isinstance(msg, str) and msg:
        return msg
    return str(error)
