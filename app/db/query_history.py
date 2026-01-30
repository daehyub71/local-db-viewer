"""
Query history database for storing executed queries.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class QueryRecord:
    """Query history record."""
    id: Optional[int] = None
    database_path: str = ""
    query_text: str = ""
    timestamp: str = ""
    execution_time: float = 0.0
    row_count: int = 0
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class QueryHistoryDB:
    """
    SQLite database for storing query history.

    Stores:
    - Query text
    - Database path
    - Execution time
    - Row count
    - Success status
    - Error message (if any)
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to data directory
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "query_history.db")

        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Create database and tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    database_path TEXT NOT NULL,
                    query_text TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    execution_time REAL DEFAULT 0.0,
                    row_count INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    error_message TEXT DEFAULT ''
                )
            ''')

            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON query_history(timestamp DESC)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_database_path
                ON query_history(database_path)
            ''')

            conn.commit()
            conn.close()

            logger.info(f"Query history database initialized: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize query history database: {e}")

    def add_query(self, record: QueryRecord) -> int:
        """
        Add a query to history.

        Args:
            record: QueryRecord to add

        Returns:
            ID of inserted record
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Set timestamp if not provided
            if not record.timestamp:
                record.timestamp = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO query_history (
                    database_path, query_text, timestamp,
                    execution_time, row_count, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.database_path,
                record.query_text,
                record.timestamp,
                record.execution_time,
                record.row_count,
                int(record.success),
                record.error_message,
            ))

            conn.commit()
            record_id = cursor.lastrowid
            conn.close()

            logger.debug(f"Added query to history: {record_id}")
            return record_id

        except sqlite3.Error as e:
            logger.error(f"Failed to add query to history: {e}")
            return -1

    def get_history(
        self,
        limit: int = 100,
        database_path: Optional[str] = None
    ) -> List[QueryRecord]:
        """
        Get query history.

        Args:
            limit: Maximum number of records to return
            database_path: Filter by database path (optional)

        Returns:
            List of QueryRecord objects
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if database_path:
                cursor.execute('''
                    SELECT * FROM query_history
                    WHERE database_path = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (database_path, limit))
            else:
                cursor.execute('''
                    SELECT * FROM query_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

            records = []
            for row in cursor.fetchall():
                records.append(QueryRecord(
                    id=row[0],
                    database_path=row[1],
                    query_text=row[2],
                    timestamp=row[3],
                    execution_time=row[4],
                    row_count=row[5],
                    success=bool(row[6]),
                    error_message=row[7],
                ))

            conn.close()
            return records

        except sqlite3.Error as e:
            logger.error(f"Failed to get query history: {e}")
            return []

    def search_history(self, search_term: str, limit: int = 100) -> List[QueryRecord]:
        """
        Search query history.

        Args:
            search_term: Search term to look for in query text
            limit: Maximum number of records to return

        Returns:
            List of matching QueryRecord objects
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM query_history
                WHERE query_text LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{search_term}%', limit))

            records = []
            for row in cursor.fetchall():
                records.append(QueryRecord(
                    id=row[0],
                    database_path=row[1],
                    query_text=row[2],
                    timestamp=row[3],
                    execution_time=row[4],
                    row_count=row[5],
                    success=bool(row[6]),
                    error_message=row[7],
                ))

            conn.close()
            return records

        except sqlite3.Error as e:
            logger.error(f"Failed to search query history: {e}")
            return []

    def delete_record(self, record_id: int) -> bool:
        """
        Delete a specific record.

        Args:
            record_id: ID of record to delete

        Returns:
            True if deleted successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM query_history WHERE id = ?', (record_id,))

            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()

            if deleted:
                logger.debug(f"Deleted query history record: {record_id}")

            return deleted

        except sqlite3.Error as e:
            logger.error(f"Failed to delete query history record: {e}")
            return False

    def clear_history(self) -> bool:
        """
        Clear all query history.

        Returns:
            True if cleared successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM query_history')

            conn.commit()
            conn.close()

            logger.info("Cleared all query history")
            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to clear query history: {e}")
            return False

    def get_statistics(self) -> dict:
        """
        Get query history statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM query_history')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM query_history WHERE success = 1')
            success = cursor.fetchone()[0]

            cursor.execute('SELECT AVG(execution_time) FROM query_history WHERE success = 1')
            avg_time = cursor.fetchone()[0] or 0.0

            cursor.execute('SELECT COUNT(DISTINCT database_path) FROM query_history')
            unique_dbs = cursor.fetchone()[0]

            conn.close()

            return {
                'total': total,
                'success': success,
                'failed': total - success,
                'avg_execution_time': avg_time,
                'unique_databases': unique_dbs,
            }

        except sqlite3.Error as e:
            logger.error(f"Failed to get query history statistics: {e}")
            return {}
