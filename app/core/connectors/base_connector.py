"""
Base connector abstract class for database connections.

All database connectors must inherit from BaseConnector and implement
all abstract methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ColumnInfo:
    """Information about a table column."""
    name: str
    data_type: str
    nullable: bool = True
    default_value: Optional[str] = None
    is_primary_key: bool = False
    foreign_key: Optional[str] = None


@dataclass
class IndexInfo:
    """Information about a table index."""
    name: str
    columns: List[str] = field(default_factory=list)
    is_unique: bool = False


@dataclass
class TableSchema:
    """Complete schema information for a table."""
    name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[IndexInfo] = field(default_factory=list)
    row_count: int = 0
    ddl: str = ""


@dataclass
class QueryResult:
    """Result of a database query."""
    columns: List[str] = field(default_factory=list)
    rows: List[tuple] = field(default_factory=list)
    row_count: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if query was successful."""
        return self.error is None


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class ConnectionError(DatabaseError):
    """Exception for connection errors."""
    pass


class QueryError(DatabaseError):
    """Exception for query execution errors."""
    pass


class UnsupportedDatabaseError(DatabaseError):
    """Exception for unsupported database types."""
    pass


class BaseConnector(ABC):
    """
    Abstract base class for database connectors.

    All database-specific connectors must inherit from this class
    and implement all abstract methods.
    """

    @abstractmethod
    def connect(self, file_path: str) -> bool:
        """
        Connect to a database file.

        Args:
            file_path: Path to the database file

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close the database connection.
        """
        pass

    @abstractmethod
    def get_tables(self) -> List[str]:
        """
        Get list of table names in the database.

        Returns:
            List of table names
        """
        pass

    @abstractmethod
    def get_schema(self, table_name: str) -> TableSchema:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            TableSchema object with column and index information
        """
        pass

    @abstractmethod
    def get_table_data(
        self,
        table_name: str,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> QueryResult:
        """
        Get paginated data from a table.

        Args:
            table_name: Name of the table
            offset: Starting row index
            limit: Maximum number of rows to return
            order_by: Column name to sort by
            order_desc: Sort in descending order if True

        Returns:
            QueryResult with rows and metadata
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, timeout: int = 30) -> QueryResult:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            timeout: Query timeout in seconds

        Returns:
            QueryResult with results and metadata

        Raises:
            QueryError: If query execution fails
        """
        pass

    @abstractmethod
    def get_row_count(self, table_name: str) -> int:
        """
        Get total row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to a database."""
        pass

    @property
    @abstractmethod
    def file_path(self) -> Optional[str]:
        """Get the connected database file path."""
        pass

    @property
    @abstractmethod
    def database_type(self) -> str:
        """Get the database type name (e.g., 'SQLite', 'DuckDB')."""
        pass
