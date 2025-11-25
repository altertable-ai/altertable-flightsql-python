"""
Integration tests for data ingestion.

Tests the ingest method for bulk data loading.
"""

import pyarrow as pa

from altertable_flightsql import Client
from altertable_flightsql.client import IngestIncrementalOptions
from tests.conftest import SchemaInfo


class TestBasicIngest:
    """Test basic ingest functionality."""

    def test_ingest_simple_table(self, altertable_client: Client, test_schema: SchemaInfo):
        """Test ingesting data into a new table."""
        import uuid

        table_name = f"test_ingest_{uuid.uuid4().hex[:8]}"
        fully_qualified_table = f"{test_schema.full_name}.{table_name}"

        # Define schema
        schema = pa.schema(
            [
                ("id", pa.int64()),
                ("name", pa.string()),
                ("value", pa.float64()),
            ]
        )

        # Create test data
        data = pa.record_batch(
            [
                [1, 2, 3, 4, 5],
                ["Alice", "Bob", "Charlie", "David", "Eve"],
                [100.5, 200.0, 300.75, 400.25, 500.5],
            ],
            schema=schema,
        )

        try:
            # Ingest data
            with altertable_client.ingest(
                table_name=table_name,
                schema=schema,
                schema_name=test_schema.schema,
                catalog_name=test_schema.catalog,
            ) as writer:
                writer.write(data)

            reader = altertable_client.query(f"SELECT * FROM {fully_qualified_table} ORDER BY id")
            result = reader.read_all()

            assert result.num_rows == 5
            result_df = result.to_pandas()
            assert list(result_df["id"]) == [1, 2, 3, 4, 5]
            assert list(result_df["name"]) == ["Alice", "Bob", "Charlie", "David", "Eve"]

        finally:
            # Cleanup
            try:
                altertable_client.execute(f"DROP TABLE IF EXISTS {fully_qualified_table}")
            except Exception as e:
                print(f"Warning: Failed to drop table {fully_qualified_table}: {e}")

    def test_ingest_multiple_batches(self, altertable_client: Client, test_schema: SchemaInfo):
        """Test ingesting multiple batches of data."""
        import uuid

        table_name = f"test_ingest_{uuid.uuid4().hex[:8]}"
        fully_qualified_table = f"{test_schema.full_name}.{table_name}"

        # Define schema
        schema = pa.schema(
            [
                ("id", pa.int64()),
                ("name", pa.string()),
            ]
        )

        try:
            # Ingest data
            with altertable_client.ingest(
                table_name=table_name,
                schema=schema,
                schema_name=test_schema.schema,
                catalog_name=test_schema.catalog,
            ) as writer:
                # Write multiple batches
                batch1 = pa.record_batch([[1, 2], ["Alice", "Bob"]], schema=schema)
                batch2 = pa.record_batch([[3, 4], ["Charlie", "David"]], schema=schema)
                batch3 = pa.record_batch([[5], ["Eve"]], schema=schema)

                writer.write(batch1)
                writer.write(batch2)
                writer.write(batch3)

            reader = altertable_client.query(f"SELECT * FROM {fully_qualified_table} ORDER BY id")
            result = reader.read_all()

            assert result.num_rows == 5
            result_df = result.to_pandas()
            assert list(result_df["id"]) == [1, 2, 3, 4, 5]
            assert list(result_df["name"]) == ["Alice", "Bob", "Charlie", "David", "Eve"]

        finally:
            # Cleanup
            try:
                altertable_client.execute(f"DROP TABLE IF EXISTS {fully_qualified_table}")
            except Exception as e:
                print(f"Warning: Failed to drop table {fully_qualified_table}: {e}")


class TestIngestWithPrimaryKey:
    """Test ingest with primary key specification."""

    def test_ingest_with_primary_key(self, altertable_client: Client, test_schema: SchemaInfo):
        """Test ingesting data with primary key constraint."""
        import uuid

        table_name = f"test_ingest_{uuid.uuid4().hex[:8]}"
        fully_qualified_table = f"{test_schema.full_name}.{table_name}"

        # Define schema
        schema = pa.schema(
            [
                ("id", pa.int64()),
                ("email", pa.string()),
                ("name", pa.string()),
                ("created_at", pa.int64()),
            ]
        )

        try:
            # Ingest data with primary key
            with altertable_client.ingest(
                table_name=table_name,
                schema=schema,
                schema_name=test_schema.schema,
                catalog_name=test_schema.catalog,
                incremental_options=IngestIncrementalOptions(
                    primary_key=["id"], cursor_field=["created_at"]
                ),
            ) as writer:
                writer.write(
                    pa.record_batch(
                        [
                            [1, 2, 3, 1],
                            [
                                "alice@example.com",
                                "bob@example.com",
                                "charlie@example.com",
                                "alice+1@example.com",
                            ],
                            ["Alice", "Bob", "Charlie", "Alice"],
                            [1, 2, 3, 4],
                        ],
                        schema=schema,
                    )
                )

            # Verify data was ingested
            reader = altertable_client.query(f"SELECT * FROM {fully_qualified_table} ORDER BY id")
            result = reader.read_all()

            assert result.num_rows == 3
            result_df = result.to_pandas()
            assert list(result_df["id"]) == [1, 2, 3]
            assert list(result_df["email"]) == [
                "alice+1@example.com",
                "bob@example.com",
                "charlie@example.com",
            ]
            assert list(result_df["name"]) == ["Alice", "Bob", "Charlie"]

        finally:
            # Cleanup
            try:
                altertable_client.execute(f"DROP TABLE IF EXISTS {fully_qualified_table}")
            except Exception as e:
                print(f"Warning: Failed to drop table {fully_qualified_table}: {e}")
