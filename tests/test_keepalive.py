import contextlib
import socket
import threading
import time
from concurrent import futures

import grpc
import pyarrow.flight as flight
import pytest

from altertable_flightsql import client as client_module
from altertable_flightsql.client import Client

KEEPALIVE_MS = 1000
# Long enough for the client to exceed gRPC's default budget of two pings without sending data.
HEALTHY_SECONDS = 5


class BlockingFlightServer:
    """Flight server whose GetFlightInfo blocks like a long-running statement.

    Built on grpcio rather than pyarrow so it can accept frequent client pings like the
    production server; some pyarrow servers reject them with a "too_many_pings" GOAWAY.
    """

    def __init__(self):
        self.statement_started = threading.Event()
        self.release = threading.Event()
        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=4),
            options=[("grpc.http2.max_ping_strikes", 0)],
        )
        self._server.add_generic_rpc_handlers(
            (
                grpc.method_handlers_generic_handler(
                    "arrow.flight.protocol.FlightService",
                    {
                        "Handshake": grpc.stream_stream_rpc_method_handler(self._handshake),
                        "GetFlightInfo": grpc.unary_unary_rpc_method_handler(
                            self._get_flight_info
                        ),
                    },
                ),
            )
        )
        self.port = self._server.add_insecure_port("127.0.0.1:0")
        self._server.start()

    def shutdown(self):
        self._server.stop(grace=None)

    def _handshake(self, requests, context):
        for _ in requests:
            pass
        context.send_initial_metadata((("authorization", "Bearer test-token"),))
        return iter(())

    def _get_flight_info(self, request, context):
        self.statement_started.set()
        self.release.wait(timeout=60)
        context.abort(grpc.StatusCode.CANCELLED, "released")


class FreezableProxy:
    """TCP proxy that can silently stop forwarding bytes while keeping sockets open."""

    def __init__(self, upstream_port: int):
        self._upstream_port = upstream_port
        self._frozen = threading.Event()
        self._closed = threading.Event()
        self._sockets = []
        self._listener = socket.create_server(("127.0.0.1", 0))
        self.port = self._listener.getsockname()[1]
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def freeze(self):
        self._frozen.set()

    def close(self):
        self._closed.set()
        for sock in [self._listener, *self._sockets]:
            with contextlib.suppress(OSError):
                sock.close()

    def _accept_loop(self):
        while not self._closed.is_set():
            try:
                downstream, _ = self._listener.accept()
            except OSError:
                return
            upstream = socket.create_connection(("127.0.0.1", self._upstream_port))
            self._sockets += [downstream, upstream]
            threading.Thread(target=self._pump, args=(downstream, upstream), daemon=True).start()
            threading.Thread(target=self._pump, args=(upstream, downstream), daemon=True).start()

    def _pump(self, source: socket.socket, destination: socket.socket):
        while True:
            try:
                data = source.recv(65536)
                if not data:
                    return
                if not self._frozen.is_set():
                    destination.sendall(data)
            except OSError:
                return


@pytest.fixture
def blocking_server():
    server = BlockingFlightServer()
    yield server
    server.release.set()
    server.shutdown()


@pytest.fixture
def proxy(blocking_server):
    proxy = FreezableProxy(blocking_server.port)
    yield proxy
    proxy.close()


def test_connection_cut_during_long_statement_fails_the_call(monkeypatch, blocking_server, proxy):
    monkeypatch.setattr(client_module, "GRPC_KEEPALIVE_TIME_MS", KEEPALIVE_MS)
    monkeypatch.setattr(client_module, "GRPC_KEEPALIVE_TIMEOUT_MS", KEEPALIVE_MS)
    client = Client("user", "pass", host="127.0.0.1", port=proxy.port, tls=False)
    errors = []

    def run_statement():
        try:
            client.query("SELECT long_running()")
        except Exception as e:
            errors.append(e)

    try:
        statement = threading.Thread(target=run_statement, daemon=True)
        statement.start()
        assert blocking_server.statement_started.wait(timeout=10)
        time.sleep(HEALTHY_SECONDS)
        assert statement.is_alive(), f"statement failed on a healthy connection: {errors}"

        proxy.freeze()
        statement.join(timeout=15)

        assert not statement.is_alive(), "statement hung on a dead connection"
        assert len(errors) == 1
        assert isinstance(errors[0], flight.FlightUnavailableError)
    finally:
        with contextlib.suppress(Exception):
            client.close(timeout_seconds=1)
