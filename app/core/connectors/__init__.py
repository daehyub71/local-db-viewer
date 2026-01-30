"""
Database connectors package.

Provides abstract base class and implementations for connecting
to various local database file formats.
"""

from .base_connector import (
    BaseConnector,
    TableSchema,
    ColumnInfo,
    IndexInfo,
    QueryResult,
    DatabaseError,
    ConnectionError,
    QueryError,
    UnsupportedDatabaseError,
)
from .sqlite_connector import SQLiteConnector
from .connector_factory import ConnectorFactory

__all__ = [
    # Base classes
    'BaseConnector',
    'TableSchema',
    'ColumnInfo',
    'IndexInfo',
    'QueryResult',
    # Exceptions
    'DatabaseError',
    'ConnectionError',
    'QueryError',
    'UnsupportedDatabaseError',
    # Implementations
    'SQLiteConnector',
    'ConnectorFactory',
]
