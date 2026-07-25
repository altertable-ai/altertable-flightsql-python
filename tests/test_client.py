from types import SimpleNamespace

import pyarrow.flight as flight
import pytest
from google.protobuf import any_pb2

from altertable_flightsql.client import Client
from altertable_flightsql.generated import arrow_flight_pb2 as flight_pb2


class FakeFlightClient:
    def __init__(self):
        self.actions = []
        self.options = []
        self.events = []
        self.closed = False
        close_result = flight_pb2.CloseSessionResult(status=flight_pb2.CloseSessionResult.CLOSED)
        self.action_results = [SimpleNamespace(body=close_result.SerializeToString())]

    def do_action(self, action, options=None):
        if self.closed:
            raise RuntimeError("FlightClient is closed")
        self.actions.append(action)
        self.options.append(options)
        self.events.append(("action", action.type))
        return self.action_results

    def close(self):
        self.closed = True
        self.events.append(("close", None))


class FailingCloseSessionFlightClient(FakeFlightClient):
    def do_action(self, action, options=None):
        super().do_action(action, options)
        raise RuntimeError("close session failed")


def _client_backed_by(flight_client) -> Client:
    client = Client.__new__(Client)
    client._client = flight_client
    client._closed = False
    return client


def _action_body_bytes(action) -> bytes:
    body = action.body
    if hasattr(body, "to_pybytes"):
        return body.to_pybytes()
    return bytes(body)


def test_set_options_serializes_flight_session_request_without_any():
    flight_client = FakeFlightClient()
    client = _client_backed_by(flight_client)

    session_options = {
        "catalog": flight_pb2.SessionOptionValue(string_value="test_catalog"),
    }
    client._set_options(session_options)

    action = flight_client.actions[0]
    request = flight_pb2.SetSessionOptionsRequest(session_options=session_options)
    wrapped_request = any_pb2.Any()
    wrapped_request.Pack(request)

    assert action.type == "SetSessionOptions"
    assert _action_body_bytes(action) == request.SerializeToString()
    assert _action_body_bytes(action) != wrapped_request.SerializeToString()


def test_close_closes_server_session_before_transport():
    flight_client = FakeFlightClient()
    client = _client_backed_by(flight_client)

    client.close()

    action = flight_client.actions[0]
    request = flight_pb2.CloseSessionRequest()

    assert flight_client.events == [("action", "CloseSession"), ("close", None)]
    assert _action_body_bytes(action) == request.SerializeToString()


def test_close_closes_transport_when_server_session_close_fails():
    flight_client = FailingCloseSessionFlightClient()
    client = _client_backed_by(flight_client)

    with pytest.raises(RuntimeError, match="close session failed"):
        client.close()

    assert flight_client.events == [("action", "CloseSession"), ("close", None)]


def test_close_rejects_unclosed_server_session():
    flight_client = FakeFlightClient()
    close_result = flight_pb2.CloseSessionResult(status=flight_pb2.CloseSessionResult.NOT_CLOSEABLE)
    flight_client.action_results = [SimpleNamespace(body=close_result.SerializeToString())]
    client = _client_backed_by(flight_client)

    with pytest.raises(RuntimeError, match="NOT_CLOSEABLE"):
        client.close()

    assert flight_client.events == [("action", "CloseSession"), ("close", None)]


def test_close_is_idempotent():
    flight_client = FakeFlightClient()
    client = _client_backed_by(flight_client)

    client.close()
    client.close()

    assert flight_client.events == [("action", "CloseSession"), ("close", None)]


def test_close_passes_bounded_timeout_to_do_action():
    flight_client = FakeFlightClient()
    client = _client_backed_by(flight_client)

    client.close()

    assert isinstance(flight_client.options[0], flight.FlightCallOptions)
