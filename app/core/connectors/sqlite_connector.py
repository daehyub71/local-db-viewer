"""
SQLite database connector implementation.
"""

import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from .base_connector import (
    BaseConnector,
    TableSchema,
    ColumnInfo,
    IndexInfo,
    QueryResult,
    ConnectionError,
    QueryError,
)


class SQLiteConnector(BaseConnector):
    """
    SQLite database connector using Python's built-in sqlite3 module.
    """

    SUPPORTED_EXTENSIONS = ['.db', '.sqlite', '.sqlite3']

    def __init__(self):
        self._connection: Optional[sqlite3.Connection] = None
        self._file_path: Optional[str] = None

    def connect(self, file_path: str) -> bool:
        """Connect to a SQLite database file."""
        path = Path(file_path)

        if not path.exists():
            raise ConnectionError(f"File not found: {file_path}")

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ConnectionError(
                f"Unsupported file extension: {path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        try:
            # Close existing connection if any
            if self._connection:
                self.disconnect()

            self._connection = sqlite3.connect(
                file_path,
                check_same_thread=False,
                timeout=30.0
            )
            # Enable foreign key support
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._file_path = file_path
            return True

        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._connection:
            try:
                self._connection.close()
            except sqlite3.Error:
                pass
            finally:
                self._connection = None
                self._file_path = None

    def get_tables(self) -> List[str]:
        """Get list of table names in the database."""
        if not self._connection:
            return []

        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            return [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            raise QueryError(f"Failed to get tables: {e}")

    def get_schema(self, table_name: str) -> TableSchema:
        """Get schema information for a table."""
        if not self._connection:
            raise QueryError("Not connected to database")

        try:
            cursor = self._connection.cursor()

            # Get column information
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = []
            primary_keys = []

            for row in cursor.fetchall():
                cid, name, data_type, notnull, default_value, pk = row
                column = ColumnInfo(
                    name=name,
                    data_type=data_type or "BLOB",
                    nullable=not notnull,
                    default_value=default_value,
                    is_primary_key=bool(pk),
                )
                columns.append(column)
                if pk:
                    primary_keys.append(name)

            # Get foreign key information
            cursor.execute(f"PRAGMA foreign_key_list('{table_name}')")
            foreign_keys = []
            for row in cursor.fetchall():
                fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = row
                foreign_keys.append({
                    'column': from_col,
                    'ref_table': ref_table,
                    'ref_column': to_col,
                })
                # Update column with FK info
                for col in columns:
                    if col.name == from_col:
                        col.foreign_key = f"{ref_table}.{to_col}"

            # Get index information
            cursor.execute(f"PRAGMA index_list('{table_name}')")
            indexes = []
            for row in cursor.fetchall():
                idx_seq, idx_name, is_unique, origin, partial = row
                # Get columns in this index
                cursor.execute(f"PRAGMA index_info('{idx_name}')")
                idx_columns = [r[2] for r in cursor.fetchall()]
                indexes.append(IndexInfo(
                    name=idx_name,
                    columns=idx_columns,
                    is_unique=bool(is_unique),
                ))

            # Get row count
            row_count = self.get_row_count(table_name)

            # Get DDL
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            ddl_row = cursor.fetchone()
            ddl = ddl_row[0] if ddl_row else ""

            return TableSchema(
                name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                indexes=indexes,
                row_count=row_count,
                ddl=ddl,
            )

        except sqlite3.Error as e:
            raise QueryError(f"Failed to get schema for {table_name}: {e}")

    def get_table_data(
        self,
        table_name: str,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> QueryResult:
        """Get paginated data from a table."""
        if not self._connection:
            raise QueryError("Not connected to database")

        # Build query with proper escaping
        query = f'SELECT * FROM "{table_name}"'

        if order_by:
            direction = "DESC" if order_desc else "ASC"
            query += f' ORDER BY "{order_by}" {direction}'

        query += f" LIMIT {limit} OFFSET {offset}"

        return self.execute_query(query)

    def execute_query(self, query: str, timeout: int = 30) -> QueryResult:
        """Execute a SQL query."""
        if not self._connection:
            return QueryResult(error="Not connected to database")

        start_time = time.time()

        try:
            # Set timeout
            self._connection.execute(f"PRAGMA busy_timeout = {timeout * 1000}")

            cursor = self._connection.cursor()
            cursor.execute(query)

            # Check if it's a SELECT query
            if query.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                execution_time = time.time() - start_time

                return QueryResult(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    execution_time=execution_time,
                )
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE)
                self._connection.commit()
                execution_time = time.time() - start_time

                return QueryResult(
                    columns=["affected_rows"],
                    rows=[(cursor.rowcount,)],
                    row_count=cursor.rowcount,
                    execution_time=execution_time,
                )

        except sqlite3.Error as e:
            execution_time = time.time() - start_time
            return QueryResult(
                execution_time=execution_time,
                error=str(e),
            )

    def get_row_count(self, table_name: str) -> int:
        """Get total row count for a table."""
        if not self._connection:
            return 0

        try:
            cursor = self._connection.cursor()
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            result = cursor.fetchone()
            return result[0] if result else 0

        except sqlite3.Error:
            return 0

    @property
    def is_connected(self) -> bool:
        """Check if connected to a database."""
        return self._connection is not None

    @property
    def file_path(self) -> Optional[str]:
        """Get the connected database file path."""
        return self._file_path

    @property
    def database_type(self) -> str:
        """Get the database type name."""
        return "SQLite"

    def get_views(self) -> List[str]:
        """Get list of view names in the database."""
        if not self._connection:
            return []

        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='view'
                ORDER BY name
            """)
            return [row[0] for row in cursor.fetchall()]

        except sqlite3.Error:
            return []

    def get_database_info(self) -> dict:
        """Get database metadata."""
        if not self._connection:
            return {}

        try:
            cursor = self._connection.cursor()

            # Get SQLite version
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]

            # Get page size
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            # Get page count
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            # Get encoding
            cursor.execute("PRAGMA encoding")
            encoding = cursor.fetchone()[0]

            return {
                'sqlite_version': version,
                'page_size': page_size,
                'page_count': page_count,
                'file_size': page_size * page_count,
                'encoding': encoding,
            }

        except sqlite3.Error:
            return {}
