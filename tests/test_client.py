from google.protobuf import any_pb2

from altertable_flightsql.client import Client
from altertable_flightsql.generated import arrow_flight_pb2 as flight_pb2


class FakeFlightClient:
    def __init__(self):
        self.actions = []

    def do_action(self, action):
        self.actions.append(action)
        return []


def _action_body_bytes(action) -> bytes:
    body = action.body
    if hasattr(body, "to_pybytes"):
        return body.to_pybytes()
    return bytes(body)


def test_set_options_serializes_flight_session_request_without_any():
    flight_client = FakeFlightClient()
    client = Client.__new__(Client)
    client._client = flight_client

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
