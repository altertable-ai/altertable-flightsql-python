"""
altertable-flightsql: Python client library for Altertable.

This library provides a high-level Python client for connecting to Altertable,
enabling high-performance SQL queries and data analysis.
"""

__version__ = "0.3.1"

from altertable_flightsql.client import Client, PreparedStatement
from altertable_flightsql.errors import AltertableFlightError, wrap_flight_error

__all__ = [
    "__version__",
    "AltertableFlightError",
    "Client",
    "PreparedStatement",
    "wrap_flight_error",
]
