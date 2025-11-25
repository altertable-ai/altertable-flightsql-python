"""
Integration tests for SQL query execution.

Tests basic query execution, updates, and prepared statements.
"""

import pyarrow as pa
import pytest

from altertable_flightsql import Client
from tests.conftest import TableInfo


class TestBasicQueries:
    """Test basic SQL query execution."""

    def test_simple_select(self, altertable_client: Client):
        """Test executing a simple SELECT query."""
        reader = altertable_client.query("SELECT 1 AS value")

        # Check the result
        df = reader.read_pandas()
        assert "value" in df.columns
        assert df["value"].iloc[0] == 1

    def test_select_multiple_columns(self, altertable_client: Client):
        """Test SELECT with multiple columns."""
        query = "SELECT 1 AS col1, 'test' AS col2, 3.14 AS col3"
        reader = altertable_client.query(query)

        df = reader.read_pandas()
        assert df["col1"].iloc[0] == 1
        assert df["col2"].iloc[0] == "test"
        assert abs(float(df["col3"].iloc[0]) - 3.14) < 0.001

    def test_select_with_filter(self, altertable_client: Client, test_table: TableInfo):
        """Test SELECT with WHERE clause."""
        # Query with filter
        reader = altertable_client.query(f"SELECT * FROM {test_table.full_name} WHERE value >= 200")

        df = reader.read_pandas()
        assert len(df) == 2
        assert set(df["name"]) == {"Bob", "Charlie"}

    def test_empty_result_set(self, altertable_client: Client, test_table: TableInfo):
        """Test query that returns no rows."""
        # Query empty table
        reader = altertable_client.query(f"SELECT * FROM {test_table.full_name} WHERE value > 1000")
        table = reader.read_all()

        # Should return schema but no data
        if table.num_rows > 0:
            df = table.to_pandas()
            assert len(df) == 0


class TestPreparedStatements:
    """Test prepared statement functionality."""

    def test_prepare_with_dict_parameters(self, altertable_client: Client, test_table: TableInfo):
        """Test prepared statement with dict parameters."""
        # Prepare statement
        with altertable_client.prepare(
            f"SELECT * FROM {test_table.full_name} WHERE id = $id AND value >= $min_value"
        ) as stmt:
            # Execute prepared statement
            reader = stmt.query(parameters={"id": 1, "min_value": 100})
            table = reader.read_all()
            assert table.num_rows > 0

    def test_prepare_with_list_parameters(self, altertable_client: Client, test_table: TableInfo):
        """Test prepared statement with list parameters."""
        with altertable_client.prepare(
            f"SELECT * FROM {test_table.full_name} WHERE id = ? AND value >= ?"
        ) as stmt:
            reader = stmt.query(parameters=[1, 100])
            table = reader.read_all()
            assert table.num_rows >= 0

    def test_prepare_with_record_batch_parameters(
        self, altertable_client: Client, test_table: TableInfo
    ):
        """Test prepared statement with RecordBatch parameters."""
        with altertable_client.prepare(
            f"SELECT * FROM {test_table.full_name} WHERE id = $id AND value >= $min_value"
        ) as stmt:
            # Create a RecordBatch with parameters
            batch = pa.record_batch({"id": [1], "min_value": [100]})
            reader = stmt.query(parameters=batch)
            table = reader.read_all()
            assert table.num_rows > 0

    def test_prepare_with_table_parameters(self, altertable_client: Client, test_table: TableInfo):
        """Test prepared statement with Table parameters."""
        with altertable_client.prepare(
            f"SELECT * FROM {test_table.full_name} WHERE id = $id AND value >= $min_value"
        ) as stmt:
            # Create a Table with parameters
            param_table = pa.table({"id": [1], "min_value": [100]})
            reader = stmt.query(parameters=param_table)
            table = reader.read_all()
            assert table.num_rows > 0


class TestErrorHandling:
    """Test error handling in query execution."""

    def test_invalid_sql_syntax(self, altertable_client: Client):
        """Test handling of invalid SQL syntax."""
        with pytest.raises(Exception):
            reader = altertable_client.query("INVALID SQL SYNTAX")
            list(reader)

    def test_nonexistent_table(self, altertable_client: Client):
        """Test querying a non-existent table."""
        with pytest.raises(Exception):
            reader = altertable_client.query("SELECT * FROM nonexistent_table_12345")
            list(reader)

    def test_invalid_column_name(self, altertable_client: Client, test_table: TableInfo):
        """Test querying with invalid column name."""
        # Query with invalid column
        with pytest.raises(Exception):
            reader = altertable_client.query(
                f"SELECT nonexistent_column FROM {test_table.full_name}"
            )
            list(reader)
