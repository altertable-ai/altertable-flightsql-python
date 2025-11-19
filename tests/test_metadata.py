"""
Integration tests for metadata operations.

Tests catalog, schema, table, and primary key metadata queries.
"""

import uuid

from altertable_flightsql import Client
from tests.conftest import SchemaInfo, TableInfo


class TestCatalogs:
    """Test catalog metadata queries."""

    def test_get_catalogs(self, altertable_client: Client, test_catalog: str):
        """Test retrieving list of catalogs and finding created catalog."""
        reader = altertable_client.get_catalogs()
        table = reader.read_all()

        # Check structure
        df = table.to_pandas()
        assert "catalog_name" in df.columns

        # Should return some catalogs
        assert len(df) > 0

        # Verify our test catalog exists
        assert test_catalog in df["catalog_name"].values


class TestSchemas:
    """Test schema metadata queries."""

    def test_get_schemas(self, altertable_client: Client, test_schema: SchemaInfo):
        """Test retrieving list of schemas and finding created schema."""
        reader = altertable_client.get_schemas()

        df = reader.read_pandas()
        # Check expected columns
        assert "db_schema_name" in df.columns

        # Verify our test schema exists
        assert test_schema.schema in df["db_schema_name"].values

    def test_get_schemas_with_catalog(self, altertable_client: Client, test_schema: SchemaInfo):
        """Test retrieving schemas for a specific catalog."""
        # Get schemas for the test catalog
        reader = altertable_client.get_schemas(catalog=test_schema.catalog)
        table = reader.read_all()

        # Should return results for the catalog
        assert table.num_rows > 0

        df = table.to_pandas()
        # Check expected columns
        assert "db_schema_name" in df.columns

        # Verify our test schema exists
        assert test_schema.schema in df["db_schema_name"].values

    def test_get_schemas_with_pattern(self, altertable_client: Client, test_schema: SchemaInfo):
        """Test retrieving schemas with a filter pattern."""
        # Use pattern that should match our test schema
        pattern = f"{test_schema.schema[:15]}%"
        reader = altertable_client.get_schemas(schema_pattern=pattern)
        table = reader.read_all()

        # Should return results (pattern matches our schema)
        assert table.num_rows > 0

        df = table.to_pandas()
        # Our test schema should be in the results
        assert test_schema.schema in df["db_schema_name"].values

    def test_get_schemas_no_match_pattern(self, altertable_client: Client):
        """Test schema pattern that matches nothing."""
        # Use a pattern that shouldn't match anything
        reader = altertable_client.get_schemas(schema_pattern="nonexistent_schema_xyz_12345_999")
        table = reader.read_all()

        # Should return empty result or no batches
        if table.num_rows > 0:
            df = table.to_pandas()
            assert len(df) == 0


class TestTables:
    """Test table metadata queries."""

    def test_get_tables(self, altertable_client: Client, test_table: TableInfo):
        """Test retrieving list of tables and finding created table."""
        reader = altertable_client.get_tables()
        df = reader.read_pandas()
        # Check expected columns
        assert "table_name" in df.columns
        assert "table_type" in df.columns

        # Verify our test table exists
        assert test_table.table in df["table_name"].values

    def test_get_tables_with_pattern(self, altertable_client: Client, test_table: TableInfo):
        """Test retrieving tables with a filter pattern."""
        # Query with pattern matching our test table
        pattern = f"{test_table.table[:15]}%"
        reader = altertable_client.get_tables(table_pattern=pattern)
        df = reader.read_pandas()
        # Should find our test table
        assert test_table.table in df["table_name"].values

    def test_get_tables_no_match(self, altertable_client: Client):
        """Test table pattern that matches nothing."""
        reader = altertable_client.get_tables(table_pattern="nonexistent_table_xyz_99999_unique")
        table = reader.read_all()

        # Should return empty result
        if table.num_rows > 0:
            df = table.to_pandas()
            assert len(df) == 0


class TestOptions:
    """Test session options."""

    def test_set_catalog(self, altertable_client: Client):
        """Test setting the catalog."""
        catalog_name = f"test_catalog_{uuid.uuid4().hex[:8]}"
        query = "SELECT current_catalog() AS current_catalog"

        current_catalog = (
            altertable_client.query(query).read_all().to_pandas()["current_catalog"][0]
        )
        assert current_catalog != catalog_name

        altertable_client.execute(f"ATTACH ':memory:' AS {catalog_name}")

        altertable_client.set_catalog(catalog_name)

        current_catalog = (
            altertable_client.query(query).read_all().to_pandas()["current_catalog"][0]
        )
        assert current_catalog == catalog_name

    def test_set_schema(self, altertable_client: Client):
        """Test setting the schema."""
        schema_name = f"test_schema_{uuid.uuid4().hex[:8]}"
        query = "SELECT current_schema() AS current_schema"

        altertable_client.execute(f"CREATE SCHEMA {schema_name}")

        current_schema = altertable_client.query(query).read_all().to_pandas()["current_schema"][0]
        assert current_schema != schema_name

        altertable_client.set_schema(schema_name)
        current_schema = altertable_client.query(query).read_all().to_pandas()["current_schema"][0]
        assert current_schema == schema_name
