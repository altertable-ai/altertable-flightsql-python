#!/usr/bin/env python3
"""
Example usage of the Altertable Client.

This example demonstrates how to use the high-level client API to interact
with Altertable.
"""

import os

from altertable_flightsql import Client

ALTERTABLE_HOST = os.getenv("ALTERTABLE_HOST", "flight.altertable.ai")
ALTERTABLE_PORT = int(os.getenv("ALTERTABLE_PORT", "443"))
ALTERTABLE_USERNAME = os.getenv("ALTERTABLE_USERNAME")
ALTERTABLE_PASSWORD = os.getenv("ALTERTABLE_PASSWORD")
ALTERTABLE_CATALOG = os.getenv("ALTERTABLE_CATALOG", "memory")
ALTERTABLE_SCHEMA = os.getenv("ALTERTABLE_SCHEMA", "main")
ALTERTABLE_TLS = os.getenv("ALTERTABLE_TLS", "true").lower() == "true"

CONNECTION_SETTINGS = {
    "host": ALTERTABLE_HOST,
    "port": ALTERTABLE_PORT,
    "catalog": ALTERTABLE_CATALOG,
    "schema": ALTERTABLE_SCHEMA,
    "tls": ALTERTABLE_TLS,
}


def example_basic_query():
    """Execute a simple SQL query."""
    print("=" * 60)
    print("Example: Basic Query")
    print("=" * 60)

    # Connect to server
    with Client(
        username=ALTERTABLE_USERNAME,
        password=ALTERTABLE_PASSWORD,
        # Optional settings (default should work for most cases)
        **CONNECTION_SETTINGS,
    ) as client:
        # Execute query
        reader = client.query("SELECT * FROM users WHERE age > 18")

        # Read results
        for batch in reader:
            df = batch.data.to_pandas()
            print(df)

    print()


def example_updates():
    """Execute update statements."""
    print("=" * 60)
    print("Example: INSERT/UPDATE/DELETE")
    print("=" * 60)

    with Client(
        username=ALTERTABLE_USERNAME,
        password=ALTERTABLE_PASSWORD,
        **CONNECTION_SETTINGS,
    ) as client:
        # Create table
        client.execute(
            "CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, name VARCHAR, age INT)"
        )

        # Insert
        rows = client.execute("INSERT INTO users (id, name, age) VALUES (1, 'Alice', 25)")
        print(f"Inserted {rows} rows")

        # Update
        rows = client.execute("UPDATE users SET age = 26 WHERE name = 'Alice'")
        print(f"Updated {rows} rows")

        # Delete
        rows = client.execute("DELETE FROM users WHERE name = 'Alice'")
        print(f"Deleted {rows} rows")

    print()


def example_prepared_statement():
    """Use prepared statements."""
    print("=" * 60)
    print("Example: Prepared Statements")
    print("=" * 60)

    with Client(
        username=ALTERTABLE_USERNAME,
        password=ALTERTABLE_PASSWORD,
        **CONNECTION_SETTINGS,
    ) as client:
        # Prepare statement
        with client.prepare("SELECT * FROM users WHERE id = ?") as stmt:
            # Execute with different parameters
            for user_id in [1, 2, 3]:
                print(f"Fetching user {user_id}...")
                reader = stmt.query(parameters=[user_id])
                for batch in reader:
                    print(batch.data.to_pandas())

    print()


def example_transactions():
    """Use transactions."""
    print("=" * 60)
    print("Example: Transactions")
    print("=" * 60)

    with Client(
        username=ALTERTABLE_USERNAME,
        password=ALTERTABLE_PASSWORD,
        **CONNECTION_SETTINGS,
    ) as client:
        # Begin transaction
        with client.begin_transaction():
            # Execute queries in transaction
            client.execute(
                "INSERT INTO users (id, name, age) VALUES (2, 'Bob', 30)",
            )

            client.execute(
                "INSERT INTO users (id, name, age) VALUES (3, 'Carol', 28)",
            )

            # Transaction will be committed automatically or rollback
            # if the scope is left because of an exception.

    print()


def example_metadata():
    """Query database metadata."""
    print("=" * 60)
    print("Example: Metadata Queries")
    print("=" * 60)

    with Client(
        username=ALTERTABLE_USERNAME,
        password=ALTERTABLE_PASSWORD,
        **CONNECTION_SETTINGS,
    ) as client:
        # Get catalogs
        print("Catalogs:")
        reader = client.get_catalogs()
        for batch in reader:
            print(batch.data.to_pandas())

        # Get schemas
        print("\nSchemas:")
        reader = client.get_schemas(catalog=ALTERTABLE_CATALOG)
        for batch in reader:
            print(batch.data.to_pandas())

        # Get tables
        print("\nTables:")
        reader = client.get_tables(
            catalog=ALTERTABLE_CATALOG, schema_pattern=ALTERTABLE_SCHEMA, table_pattern="user%"
        )
        for batch in reader:
            print(batch.data.to_pandas())

    print()


if __name__ == "__main__":
    example_updates()
    example_basic_query()
    example_transactions()
    example_prepared_statement()
    example_metadata()
