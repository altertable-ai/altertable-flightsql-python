"""
Altertable client implementation.

This module provides a high-level Python client for Altertable.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union

import pyarrow as pa
import pyarrow.flight as flight
from google.protobuf import any_pb2

from altertable_flightsql.generated import arrow_flight_sql_pb2 as sql_pb2


def _pack_command(cmd) -> bytes:
    """Pack a Flight SQL command into an Any protobuf message."""
    any_msg = any_pb2.Any()
    any_msg.Pack(cmd)
    return any_msg.SerializeToString()


def _unpack_command(bytes, packed):
    any_msg = any_pb2.Any()
    any_msg.ParseFromString(bytes)
    any_msg.Unpack(packed)


class BearerAuthMiddleware(flight.ClientMiddleware):
    """Client middleware that adds Bearer token authentication to all requests."""

    def __init__(self, token: bytes):
        """
        Initialize the middleware with a Bearer token.

        Args:
            token: The Bearer token
        """
        self._token = token

    def sending_headers(self):
        """A callback before headers are sent."""
        return {b"authorization": self._token}


class BearerAuthMiddlewareFactory(flight.ClientMiddlewareFactory):
    """Factory for creating Bearer authentication middleware."""

    def __init__(self, token: bytes):
        """
        Initialize the factory with credentials.

        Args:
            token: The Bearer token
        """
        self._token = token

    def start_call(self, info):
        """Create middleware instance for a new call."""
        return BearerAuthMiddleware(self._token)


class Client:
    """
    High-level client for Altertable.

    This client provides convenient methods for executing SQL queries
    and managing database metadata on Altertable.

    Example:
        >>> client = Client(username="user", password="pass")
        >>> result = client.query("SELECT * FROM users")
        >>> for batch in result:
        ...     print(batch.to_pandas())
    """

    def __init__(
        self,
        username: str,
        password: str,
        *,
        catalog: Optional[str] = "altertable",
        schema: Optional[str] = "main",
        host: str = "flight.altertable.ai",
        port: int = 443,
        tls: bool = True,
        auto_commit: bool = False,
    ):
        """
        Initialize an Altertable client.

        Args:
            username: Altertable username (required).
            password: Altertable password (required).
            catalog: Default catalog name (default: "altertable").
            schema: Default schema name (default: "main").
            host: Altertable server hostname (default: "flight.altertable.ai").
            port: Server port (default: 443).
            tls: Whether to use TLS/SSL (default: True).
            auto_commit: Whether to auto-commit transactions (default: False).
        """

        # Build location URI
        scheme = "grpc+tls" if tls else "grpc"
        location_uri = f"{scheme}://{host}:{port}"
        location = flight.Location(location_uri)

        self._location = location
        self._username = username
        self._password = password
        self._auto_commit = auto_commit
        self._transaction = None

        token = self._handshake()
        auth_middleware = BearerAuthMiddlewareFactory(token)
        self._client = flight.FlightClient(location, middleware=[auth_middleware])

        options = {}
        if catalog:
            options["catalog"] = sql_pb2.SessionOptionValue(string_value=catalog)

        if schema:
            options["schema"] = sql_pb2.SessionOptionValue(string_value=schema)

        if options:
            self._set_options(options)

    def _handshake(self) -> bytes:
        """
        Perform authentication handshake with the server.

        Returns:
            bytes: The Bearer token returned by the server
        """
        with flight.FlightClient(self._location) as client:
            header = client.authenticate_basic_token(self._username, self._password)
            return header[1]

    def _set_options(self, options: Mapping[str, sql_pb2.SessionOptionValue]):
        cmd = sql_pb2.SetSessionOptionsRequest(session_options=options)
        action = flight.Action("SetSessionOptions", _pack_command(cmd))
        list(self._client.do_action(action))

    def _execute_query_command(self, cmd) -> flight.FlightStreamReader:
        """Execute a Flight SQL query command and return the result stream."""
        descriptor = flight.FlightDescriptor.for_command(_pack_command(cmd))
        info = self._client.get_flight_info(descriptor)
        return self._client.do_get(info.endpoints[0].ticket)

    def _get_transaction_id(self, transaction: Optional["Transaction"]) -> Optional[bytes]:
        """Get transaction ID from explicit transaction or current transaction."""
        if transaction:
            return transaction._transaction_id
        elif self._transaction:
            return self._transaction._transaction_id
        return None

    def set_catalog(self, catalog: str):
        self._set_options({"catalog": sql_pb2.SessionOptionValue(string_value=catalog)})

    def set_schema(self, schema: str):
        self._set_options({"schema": sql_pb2.SessionOptionValue(string_value=schema)})

    def query(
        self,
        query: str,
        *,
        transaction: Optional["Transaction"] = None,
    ) -> flight.FlightStreamReader:
        """
        Execute a SQL query and return a result stream.

        Args:
            query: SQL query string to execute.
            transaction: Optional transaction to execute query within.

        Returns:
            FlightStreamReader for reading query results.

        Example:
            >>> reader = client.query("SELECT * FROM users WHERE age > 18")
            >>> for batch in reader:
            ...     print(batch.to_pandas())
        """
        # Create SQL query command
        cmd = sql_pb2.CommandStatementQuery()
        cmd.query = query
        if txn_id := self._get_transaction_id(transaction):
            cmd.transaction_id = txn_id

        # Create Flight descriptor
        descriptor = flight.FlightDescriptor.for_command(_pack_command(cmd))

        # Get flight info and create reader
        info = self._client.get_flight_info(descriptor)
        endpoint = info.endpoints[0]

        return self._client.do_get(endpoint.ticket)

    def execute(
        self,
        query: str,
        *,
        transaction: Optional["Transaction"] = None,
    ) -> int:
        """
        Execute a SQL update statement (INSERT, UPDATE, DELETE, etc.).

        Args:
            query: SQL update statement to execute.
            transaction: Optional transaction to execute within.

        Returns:
            Number of rows affected.

        Example:
            >>> rows = client.execute("INSERT INTO users (name) VALUES ('Alice')")
            >>> print(f"Inserted {rows} rows")
        """
        # Create SQL update command
        cmd = sql_pb2.CommandStatementUpdate()
        cmd.query = query
        if txn_id := self._get_transaction_id(transaction):
            cmd.transaction_id = txn_id

        # Create Flight descriptor
        descriptor = flight.FlightDescriptor.for_command(_pack_command(cmd))

        # Execute via DoPut
        writer, reader = self._client.do_put(descriptor, pa.schema([]))
        writer.close()

        # Read result from metadata
        result = sql_pb2.DoPutUpdateResult()
        metadata = reader.read()
        if metadata:
            result.ParseFromString(metadata)

        return result.record_count

    def prepare(
        self,
        query: str,
        *,
        transaction: Optional["Transaction"] = None,
    ) -> "PreparedStatement":
        """
        Create a prepared statement.

        Args:
            query: SQL query to prepare.
            transaction: Optional transaction to prepare within.

        Returns:
            PreparedStatement object.

        Example:
            >>> stmt = client.prepare("SELECT * FROM users WHERE id = ?")
            >>> result = stmt.query(parameters={"id": 42})
        """
        # Create prepared statement request
        request = sql_pb2.ActionCreatePreparedStatementRequest(query=query)
        if txn_id := self._get_transaction_id(transaction):
            request.transaction_id = txn_id

        # Execute action
        action = flight.Action("CreatePreparedStatement", _pack_command(request))
        results = list(self._client.do_action(action))

        # Parse result
        result = sql_pb2.ActionCreatePreparedStatementResult()
        _unpack_command(results[0].body.to_pybytes(), result)

        # Extract parameter schema if available
        parameter_schema = None
        if result.parameter_schema:
            parameter_schema = pa.ipc.read_schema(pa.py_buffer(result.parameter_schema))

        return PreparedStatement(
            self._client, result.prepared_statement_handle, parameter_schema=parameter_schema
        )

    def get_catalogs(self) -> flight.FlightStreamReader:
        """
        Get list of catalogs from the server.

        Returns:
            FlightStreamReader with catalog information.
        """
        cmd = sql_pb2.CommandGetCatalogs()
        return self._execute_query_command(cmd)

    def get_schemas(
        self,
        *,
        catalog: Optional[str] = None,
        schema_pattern: Optional[str] = None,
    ) -> flight.FlightStreamReader:
        """
        Get list of schemas from the server.

        Args:
            catalog: Optional catalog name filter (defaults to client catalog).
            schema_pattern: Optional schema name pattern (SQL LIKE syntax).

        Returns:
            FlightStreamReader with schema information.
        """
        cmd = sql_pb2.CommandGetDbSchemas()
        if catalog:
            cmd.catalog = catalog
        if schema_pattern:
            cmd.db_schema_filter_pattern = schema_pattern

        return self._execute_query_command(cmd)

    def get_tables(
        self,
        *,
        catalog: Optional[str] = None,
        schema_pattern: Optional[str] = None,
        table_pattern: Optional[str] = None,
        include_schema: bool = False,
    ) -> flight.FlightStreamReader:
        """
        Get list of tables from the server.

        Args:
            catalog: Optional catalog name filter (defaults to client catalog).
            schema_pattern: Optional schema name pattern (defaults to client schema).
            table_pattern: Optional table name pattern.
            include_schema: Whether to include table schema in results.

        Returns:
            FlightStreamReader with table information.
        """
        cmd = sql_pb2.CommandGetTables()
        if catalog:
            cmd.catalog = catalog
        if schema_pattern:
            cmd.db_schema_filter_pattern = schema_pattern
        if table_pattern:
            cmd.table_name_filter_pattern = table_pattern
        cmd.include_schema = include_schema

        return self._execute_query_command(cmd)

    def begin_transaction(self) -> "Transaction":
        """
        Begin a new transaction.

        Returns:
            Transaction context manager.

        Example:
            >>> # Using a transaction object
            >>> txn = client.begin_transaction()
            >>> client.execute("INSERT INTO users (name) VALUES ('Alice')", transaction=txn)
            >>> client.execute("INSERT INTO users (name) VALUES ('Bob')", transaction=txn)
            >>> client.commit_transaction(txn)

            >>> # Using a context manager
            >>> with client.begin_transaction():
            >>>     client.execute("INSERT INTO users (name) VALUES ('Alice')")
            >>>     client.execute("INSERT INTO users (name) VALUES ('Bob')")
        """
        request = sql_pb2.ActionBeginTransactionRequest()
        action = flight.Action("BeginTransaction", _pack_command(request))
        results = list(self._client.do_action(action))

        result = sql_pb2.ActionBeginTransactionResult()
        _unpack_command(results[0].body.to_pybytes(), result)
        transaction = Transaction(self, result.transaction_id)
        return transaction

    def commit_transaction(self, transaction: "Transaction") -> None:
        """
        Commit a transaction.

        Args:
            transaction: Transaction to commit.
        """
        self._end_transaction(transaction, commit=True)

    def rollback_transaction(self, transaction: "Transaction") -> None:
        """
        Rollback a transaction.

        Args:
            transaction: Transaction to rollback.
        """
        self._end_transaction(transaction, commit=False)

    def _end_transaction(self, transaction: "Transaction", commit: bool) -> None:
        """Internal method to end a transaction."""
        request = sql_pb2.ActionEndTransactionRequest()
        request.transaction_id = transaction._transaction_id
        transaction._closed = True
        if self._transaction and self._transaction._transaction_id == transaction._transaction_id:
            self._transaction = None

        request.action = (
            sql_pb2.ActionEndTransactionRequest.END_TRANSACTION_COMMIT
            if commit
            else sql_pb2.ActionEndTransactionRequest.END_TRANSACTION_ROLLBACK
        )

        action = flight.Action("EndTransaction", _pack_command(request))
        list(self._client.do_action(action))

    def close(self) -> None:
        """Close the client connection."""
        self._client.close()

    def __enter__(self) -> "Client":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


class Transaction:
    def __init__(self, client: Client, transaction_id: bytes):
        self._client = client
        self._transaction_id = transaction_id
        self._closed = False

    def __enter__(self) -> "Transaction":
        self._client._transaction = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._closed:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()

    def commit(self) -> None:
        self._client.commit_transaction(self)

    def rollback(self) -> None:
        self._client.rollback_transaction(self)


class PreparedStatement:
    """
    Represents a prepared SQL statement.

    Prepared statements can be executed multiple times with different parameters.
    """

    def __init__(
        self,
        client: flight.FlightClient,
        handle: bytes,
        parameter_schema: Optional[pa.Schema] = None,
    ):
        """
        Initialize a prepared statement.

        Args:
            client: FlightClient instance.
            handle: Prepared statement handle from server.
            parameter_schema: Optional parameter schema for the prepared statement.
        """
        self._client = client
        self._handle = handle
        self._parameter_schema = parameter_schema

    def query(
        self,
        *,
        parameters: Optional[
            Union[pa.Table, pa.RecordBatch, Mapping[str, Any], Sequence[Any]]
        ] = None,
    ) -> flight.FlightStreamReader:
        """
        Execute the prepared statement query.

        Args:
            parameters: Optional parameters for the query. Can be:
                - pyarrow.Table: A table of parameter values
                - pyarrow.RecordBatch: A batch of parameter values
                - Mapping[str, Any]: A dictionary mapping parameter names to values
                - Sequence[Any]: A list of positional parameter values

        Returns:
            FlightStreamReader with query results.

        Example:
            >>> # Using a dictionary
            >>> stmt.query(parameters={"id": 42, "name": "Alice"})

            >>> # Using a list
            >>> stmt.query(parameters=[42, "Alice"])

            >>> # Using a RecordBatch
            >>> batch = pa.record_batch({"id": [42], "name": ["Alice"]})
            >>> stmt.query(parameters=batch)
        """
        cmd = sql_pb2.CommandPreparedStatementQuery()
        cmd.prepared_statement_handle = self._handle

        descriptor = flight.FlightDescriptor.for_command(_pack_command(cmd))
        info = self._client.get_flight_info(descriptor)

        if parameters is not None:
            as_pyarrow = self._get_parameter_as_pyarrow(parameters)
            writer, _ = self._client.do_put(descriptor, as_pyarrow.schema)
            writer.write(as_pyarrow)
            writer.close()

        return self._client.do_get(info.endpoints[0].ticket)

    def close(self) -> None:
        """Close the prepared statement and release server resources."""
        request = sql_pb2.ActionClosePreparedStatementRequest(
            prepared_statement_handle=self._handle
        )

        action = flight.Action("ClosePreparedStatement", _pack_command(request))
        list(self._client.do_action(action))

    def __enter__(self) -> "PreparedStatement":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def _get_parameter_as_pyarrow(
        self, parameters: Union[pa.Table, pa.RecordBatch, Mapping[str, Any], Sequence[Any]]
    ) -> Union[pa.Table, pa.RecordBatch]:
        if isinstance(parameters, pa.Table):
            return parameters
        elif isinstance(parameters, pa.RecordBatch):
            return parameters
        elif isinstance(parameters, Mapping):
            return pa.record_batch({key: [value] for (key, value) in parameters.items()})
        elif isinstance(parameters, Sequence):
            if self._parameter_schema is None:
                raise ValueError(
                    "Cannot use positional parameters without parameter schema. "
                    "Use a dictionary (Mapping[str, Any]) instead."
                )

            # Create record batch with positional parameters
            if len(parameters) != len(self._parameter_schema):
                raise ValueError(
                    f"Expected {len(self._parameter_schema)} parameters, "
                    f"but got {len(parameters)}"
                )
            param_dict = {
                field.name: [value] for field, value in zip(self._parameter_schema, parameters)
            }

            return pa.record_batch(param_dict)
        else:
            raise TypeError(
                f"Unsupported parameter type: {type(parameters)}. "
                "Expected Table, RecordBatch, Mapping, or Sequence."
            )
