"""
Integration tests for client.execute() DML row count reporting.

Verifies that execute() correctly returns the number of rows
affected by INSERT, UPDATE, and DELETE statements.
"""

from altertable_flightsql import Client
from tests.conftest import TableInfo


class TestExecuteRowCount:
    """Test that execute() returns the correct number of affected rows."""

    def test_insert_returns_row_count(self, altertable_client: Client, test_table: TableInfo):
        """Test that INSERT returns the number of inserted rows."""
        rows = altertable_client.execute(
            f"INSERT INTO {test_table.full_name} (id, name, value) VALUES (4, 'Dave', 400), (5, 'Eve', 500)"
        )
        assert rows == 2

    def test_update_returns_row_count(self, altertable_client: Client, test_table: TableInfo):
        """Test that UPDATE returns the number of updated rows."""
        rows = altertable_client.execute(
            f"UPDATE {test_table.full_name} SET value = 999 WHERE value >= 200"
        )
        assert rows == 2

    def test_delete_returns_row_count(self, altertable_client: Client, test_table: TableInfo):
        """Test that DELETE returns the number of deleted rows."""
        rows = altertable_client.execute(f"DELETE FROM {test_table.full_name} WHERE id IN (1, 2)")
        assert rows == 2

    def test_delete_no_match_returns_zero(self, altertable_client: Client, test_table: TableInfo):
        """Test that DELETE with no matching rows returns 0."""
        rows = altertable_client.execute(f"DELETE FROM {test_table.full_name} WHERE id = 9999")
        assert rows == 0

    def test_update_no_match_returns_zero(self, altertable_client: Client, test_table: TableInfo):
        """Test that UPDATE with no matching rows returns 0."""
        rows = altertable_client.execute(
            f"UPDATE {test_table.full_name} SET value = 0 WHERE id = 9999"
        )
        assert rows == 0
