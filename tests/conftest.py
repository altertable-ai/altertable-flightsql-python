"""
pytest configuration and fixtures for integration tests.

This module provides fixtures for managing the Altertable service connection,
either using an existing service (via environment variables) or starting one
using testcontainers.
"""

import os
from collections.abc import Generator
from dataclasses import dataclass

import pytest
from testcontainers.core.container import DockerContainer, LogMessageWaitStrategy

from altertable_flightsql import Client


@dataclass(frozen=True)
class SchemaInfo:
    """Information about a test schema."""

    catalog: str
    schema: str
    full_name: str


@dataclass(frozen=True)
class TableInfo:
    """Information about a test table."""

    catalog: str
    schema: str
    table: str
    full_name: str


class AltertableContainer(DockerContainer):
    """Testcontainer for Altertable mock service."""

    def __init__(
        self,
        image: str = "ghcr.io/altertable-ai/altertable-mock:latest",
        port: int = 15002,
        platform: str = "linux/amd64",
    ):
        # Force the mock service to run on linux/amd64 so Apple Silicon hosts use the
        # correct architecture (via emulation when needed).
        super().__init__(image, platform=platform)
        self.port = port
        self.with_exposed_ports(port)
        self.with_env("ALTERTABLE_MOCK_FLIGHT_PORT", str(port))
        self.with_env("ALTERTABLE_MOCK_USERS", "altertable-test:lk_test")
        self.waiting_for(LogMessageWaitStrategy("Starting Flight SQL server on"))

    def get_connection_params(self) -> dict:
        """Get connection parameters for the container."""
        return {
            "host": self.get_container_host_ip(),
            "port": int(self.get_exposed_port(self.port)),
            "username": "altertable-test",
            "password": "lk_test",
            "tls": False,
            "catalog": None,
            "schema": None,
        }


@pytest.fixture(scope="session")
def altertable_service() -> Generator[dict, None, None]:
    """
    Provide Altertable service connection parameters.

    This fixture checks for environment variables to determine if an existing
    service is available. If not, it starts a testcontainer.

    Environment variables:
        ALTERTABLE_HOST: Hostname of existing service
        ALTERTABLE_PORT: Port of existing service
        ALTERTABLE_USERNAME: Username for authentication
        ALTERTABLE_PASSWORD: Password for authentication
        ALTERTABLE_CATALOG: Catalog for the connection
        ALTERTABLE_SCHEMA: Schema for the connection

    Yields:
        dict: Connection parameters (host, port, username, password, tls)
    """
    host = os.getenv("ALTERTABLE_HOST")
    port = os.getenv("ALTERTABLE_PORT")
    username = os.getenv("ALTERTABLE_USERNAME")
    password = os.getenv("ALTERTABLE_PASSWORD")
    catalog = os.getenv("ALTERTABLE_CATALOG")
    schema = os.getenv("ALTERTABLE_SCHEMA")
    tls = os.getenv("ALTERTABLE_TLS", "true").lower() == "true"

    if host and port:
        # Use existing service
        yield {
            "host": host,
            "port": int(port),
            "username": username,
            "password": password,
            "tls": tls,
            "catalog": catalog,
            "schema": schema,
        }
    else:
        with AltertableContainer() as container:
            print(container.get_logs())
            yield container.get_connection_params()


@pytest.fixture
def altertable_client(altertable_service: dict) -> Generator[Client, None, None]:
    """
    Provide an Altertable client connected to the test service.

    This fixture creates a fresh client for each test and ensures proper cleanup.

    Args:
        altertable_service: Service connection parameters from fixture

    Yields:
        Client: Connected Altertable client
    """
    with Client(**altertable_service) as client:
        yield client


@pytest.fixture
def test_catalog(altertable_client: Client) -> Generator[str, None, None]:
    """
    Create a test catalog via ATTACH and clean it up after the test.

    Args:
        altertable_client: Client fixture

    Yields:
        str: Catalog name to use in tests
    """
    import uuid

    catalog_name = f"test_catalog_{uuid.uuid4().hex[:8]}"

    # Create catalog by attaching a memory database
    altertable_client.execute(f"ATTACH ':memory:' AS {catalog_name}")

    yield catalog_name

    # Cleanup: detach the catalog
    try:
        altertable_client.execute(f"DETACH {catalog_name}")
    except Exception as e:
        # Ignore cleanup errors
        print(f"Warning: Failed to detach catalog {catalog_name}: {e}")


@pytest.fixture
def test_schema(altertable_client: Client, test_catalog: str) -> Generator[SchemaInfo, None, None]:
    """
    Create a test schema in the test catalog and clean it up after the test.

    Args:
        altertable_client: Client fixture
        test_catalog: Test catalog fixture

    Yields:
        SchemaInfo: Schema information with catalog, schema, and full_name
    """
    import uuid

    schema_name = f"test_schema_{uuid.uuid4().hex[:8]}"
    fully_qualified_schema = f"{test_catalog}.{schema_name}"

    # Create schema in the test catalog
    altertable_client.execute(f"CREATE SCHEMA {fully_qualified_schema}")

    schema_info = SchemaInfo(
        catalog=test_catalog, schema=schema_name, full_name=fully_qualified_schema
    )

    yield schema_info

    # Cleanup: drop the schema
    try:
        altertable_client.execute(f"DROP SCHEMA IF EXISTS {fully_qualified_schema} CASCADE")
    except Exception as e:
        # Ignore cleanup errors
        print(f"Warning: Failed to drop schema {fully_qualified_schema}: {e}")


@pytest.fixture
def test_table(
    altertable_client: Client, test_schema: SchemaInfo
) -> Generator[TableInfo, None, None]:
    """
    Create a test table in the test schema and clean it up after the test.

    The table has columns: id (INT), name (VARCHAR), value (INT)

    Args:
        altertable_client: Client fixture
        test_schema: Test schema fixture

    Yields:
        TableInfo: Table information with catalog, schema, table, and full_name
    """
    import uuid

    table_name = f"test_table_{uuid.uuid4().hex[:8]}"
    fully_qualified_table = f"{test_schema.full_name}.{table_name}"

    altertable_client.execute(
        f"CREATE TABLE {fully_qualified_table} (id INT, name VARCHAR, value INT)"
    )

    altertable_client.execute(
        f"INSERT INTO {fully_qualified_table} (id, name, value) VALUES (1, 'Alice', 100), (2, 'Bob', 200), (3, 'Charlie', 300)"
    )

    table_info = TableInfo(
        catalog=test_schema.catalog,
        schema=test_schema.schema,
        table=table_name,
        full_name=fully_qualified_table,
    )

    yield table_info

    # Cleanup: drop the table
    try:
        altertable_client.execute(f"DROP TABLE IF EXISTS {fully_qualified_table}")
    except Exception as e:
        # Ignore cleanup errors
        print(f"Warning: Failed to drop table {fully_qualified_table}: {e}")
