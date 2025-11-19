"""
Integration tests for transaction management.

Tests transaction begin, commit, rollback, and context manager functionality.
"""

from altertable_flightsql import Client
from tests.conftest import TableInfo


class TestBasicTransactions:
    """Test basic transaction operations."""

    def test_commit_transaction(self, altertable_client: Client, test_table: TableInfo):
        """Test committing a transaction."""
        with altertable_client.begin_transaction():
            altertable_client.execute(
                f"INSERT INTO {test_table.full_name} (id, name, value) VALUES (999, 'Robert', 600)",
            )

        # Verify data was committed
        reader = altertable_client.query(f"SELECT name FROM {test_table.full_name} WHERE id = 999")
        df = reader.read_pandas()
        assert len(df) == 1
        assert df["name"].iloc[0] == "Robert"

    def test_rollback_transaction(self, altertable_client: Client, test_table: TableInfo):
        """Test rolling back a transaction."""
        with altertable_client.begin_transaction() as txn:
            altertable_client.execute(
                f"INSERT INTO {test_table.full_name} (id, name, value) VALUES (999, 'Robert', 600)",
            )

            reader = altertable_client.query(
                f"SELECT name FROM {test_table.full_name} WHERE id = 999"
            )
            df = reader.read_pandas()
            assert len(df) == 1
            assert df["name"].iloc[0] == "Robert"

            txn.rollback()

        # Verify data was not committed
        reader = altertable_client.query(f"SELECT * FROM {test_table.full_name} WHERE id = 999")
        df = reader.read_pandas()
        assert len(df) == 0
