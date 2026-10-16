"""
altertable-flightsql: Python client library for Altertable.

This library provides a high-level Python client for connecting to Altertable,
enabling high-performance SQL queries and data analysis.
"""

__version__ = "0.4.1"

from altertable_flightsql.client import Client, ComputeSize, PreparedStatement

__all__ = [
    "__version__",
    "Client",
    "ComputeSize",
    "PreparedStatement",
]
