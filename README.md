# altertable-flightsql

Python client library for Altertable.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Installation

```bash
pip install altertable-flightsql
```

## Quick Start

```python
from altertable_flightsql import Client

# Connect to Altertable
with Client(username="your_username", password="your_password") as client:
    # Execute a query
    reader = client.query("SELECT * FROM users WHERE age > 18")

    # Process results
    for batch in reader:
        df = batch.data.to_pandas()
        print(df)
```

### Connect to specific catalog/schema

```python
# Connect to custom host/port
client = Client(
    username="admin",
    password="secret",
    catalog="my_catalog",
    schema="my_schema"
)
```

### Queries and Updates

```python
# Execute SELECT query
reader = client.query("SELECT * FROM users")
for batch in reader:
    print(batch.data.to_pandas())

# Execute INSERT/UPDATE/DELETE
rows_affected = client.execute("INSERT INTO users (name) VALUES ('Alice')")
print(f"Affected {rows_affected} rows")
```

### Prepared Statements

```python
# Prepare once, execute multiple times
with client.prepare("SELECT * FROM users WHERE id = $id") as stmt:
    result = stmt.query(parameters={"id": 1}))
    for batch in result:
        print(batch.data.to_pandas())
```

### Transactions

```python
with client.begin_transaction():
    client.execute("INSERT INTO users ...")
    client.execute("UPDATE accounts ...")
```

### Metadata Queries

```python
# Get catalogs, schemas, tables
catalogs = client.get_catalogs()
schemas = client.get_schemas(catalog="my_db")
tables = client.get_tables(catalog="my_db", schema_pattern="public")
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/altertable-ai/altertable-flightsql-python.git
cd altertable-flightsql-python

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest                           # Run tests
```

### Code Quality

```bash
make lint                        # Run all linters (isort, black, ruff, mypy)
```

### Compiling Protocol Definitions

If you modify the `.proto` files, you need to recompile them:

```bash
make gen                         # Compile protobuf definitions
```

**Important:** The CI will fail if generated files are out of sync with the proto definitions. Always run `make gen` and commit the generated files after modifying `.proto` files.

## Examples

See the `examples/` directory for complete examples:

```bash
# High-level client examples
python examples/client_usage.py
```

## Testing

This package includes comprehensive integration tests that validate functionality against a real Altertable service.

### Running Tests

**Using testcontainers (local development):**

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
# Having the ghcr.io/altertable-ai/altertable-mock docker image locally will speed things up.
pytest tests/
```

**Using an existing service (CI/production):**

```bash
# Set environment variables
export ALTERTABLE_HOST=localhost
export ALTERTABLE_PORT=15002
export ALTERTABLE_USERNAME=altertable-test
export ALTERTABLE_PASSWORD=lk_test

# Run tests
pytest tests/
```

The test suite automatically detects whether to use testcontainers or an existing service based on environment variables. If `ALTERTABLE_HOST` and `ALTERTABLE_PORT` are set, tests will connect to that service. Otherwise, they'll start a Docker container with `altertable.ai/altertable-mock`.

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. If you modified `.proto` files, run `make gen`
5. Run code quality checks: `make lint` and `pytest`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style (enforced by Black, line length: 100)
- Add tests for new features
- Include docstrings (Google style)
- Update documentation as needed
- Run `make gen` and commit generated files when modifying `.proto` files
- Run `make lint` before committing to ensure code quality

## Architecture

```
altertable-flightsql/
├── src/altertable_flightsql/
│   ├── __init__.py              # Package exports
│   ├── client.py                # Main Client class
│   └── generated/               # Internal protocol definitions
├── tests/                       # Test suite
└── examples/                    # Usage examples
```

## License

MIT License - See [LICENSE](LICENSE) file for details.

Built on Apache Arrow Flight SQL protocol.

## Resources

- [Altertable](https://altertable.ai)
- [PyArrow Documentation](https://arrow.apache.org/docs/python/)

## Acknowledgments

Built on Apache Arrow Flight SQL protocol.
