"""
Integration tests for altertable-flightsql.

This test suite provides comprehensive integration tests for the Altertable
Flight SQL client library.

Test Organization:
    - conftest.py: Test fixtures and container management
    - test_integration_queries.py: Query execution and data modification tests
    - test_integration_metadata.py: Metadata query tests (catalogs, schemas, tables)
    - test_integration_transactions.py: Transaction management tests

Environment Configuration:
    Tests can use either an existing Altertable service or start one via testcontainers.

    Environment variables:
        ALTERTABLE_HOST: Hostname of existing service (optional)
        ALTERTABLE_PORT: Port of existing service (optional)
        ALTERTABLE_USERNAME: Username for authentication (required)
        ALTERTABLE_PASSWORD: Password for authentication (required)

    If ALTERTABLE_HOST and ALTERTABLE_PORT are not set, tests will automatically
    start a testcontainer using altertable.ai/altertable-mock.

Running Tests:
    # Run all integration tests
    pytest tests/

    # Run specific test file
    pytest tests/test_integration_queries.py

    # Run with existing service
    ALTERTABLE_HOST=localhost ALTERTABLE_PORT=15002 ALTERTABLE_USERNAME=altertable-test ALTERTABLE_PASSWORD=lk_test pytest tests/
"""
