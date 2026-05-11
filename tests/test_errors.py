"""Unit tests for the typed-error wrapper."""

from __future__ import annotations

import pyarrow.flight as flight
import pytest

from altertable_flightsql import AltertableFlightError, wrap_flight_error


@pytest.mark.parametrize(
    ("flight_error", "expected_status"),
    [
        (flight.FlightCancelledError("cancelled"), "CANCELLED"),
        (flight.FlightTimedOutError("timeout"), "DEADLINE_EXCEEDED"),
        (flight.FlightInternalError("Internal error"), "INTERNAL"),
        (flight.FlightServerError("server-side"), "UNKNOWN"),
        (flight.FlightUnavailableError("unavailable"), "UNAVAILABLE"),
        (flight.FlightUnauthenticatedError("no creds"), "UNAUTHENTICATED"),
        (flight.FlightUnauthorizedError("forbidden"), "PERMISSION_DENIED"),
        (flight.FlightWriteSizeExceededError("too big", 1, 2), "RESOURCE_EXHAUSTED"),
    ],
)
def test_wrap_flight_error_maps_each_pyarrow_class_to_its_grpc_status(
    flight_error: BaseException, expected_status: str
) -> None:
    wrapped = wrap_flight_error(flight_error)

    assert isinstance(wrapped, AltertableFlightError)
    assert wrapped.grpc_status == expected_status


def test_wrap_flight_error_uses_unknown_grpc_status_for_non_flight_exception() -> None:
    not_a_flight_error = RuntimeError("something else entirely")

    wrapped = wrap_flight_error(not_a_flight_error)

    assert wrapped.grpc_status == "UNKNOWN"
    assert wrapped.server_message == "something else entirely"


def test_wrap_flight_error_preserves_server_message_from_flight_error_message_attr() -> None:
    server_message = "Conversion Error: Could not convert string 'queued' to INT64"
    flight_error = flight.FlightInternalError(server_message)

    wrapped = wrap_flight_error(flight_error)

    assert wrapped.server_message == server_message


def test_wrap_flight_error_keeps_extra_info_bytes_when_server_populates_the_trailer() -> None:
    flight_error = flight.FlightInternalError("anything", b'{"type": "DuckDBException"}')

    wrapped = wrap_flight_error(flight_error)

    assert wrapped.extra_info == b'{"type": "DuckDBException"}'


def test_wrap_flight_error_defaults_extra_info_to_empty_bytes_when_unset() -> None:
    flight_error = flight.FlightInternalError("no extras here")

    wrapped = wrap_flight_error(flight_error)

    assert wrapped.extra_info == b""


def test_altertable_flight_error_str_includes_grpc_status_and_server_message() -> None:
    wrapped = AltertableFlightError(
        grpc_status="ABORTED",
        server_message="TransactionContext Error: Transaction conflict",
    )

    assert str(wrapped) == "[ABORTED] TransactionContext Error: Transaction conflict"
