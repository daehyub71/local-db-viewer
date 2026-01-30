"""
Factory for creating database connectors based on file extension.
"""

from pathlib import Path
from typing import Dict, List, Type

from .base_connector import BaseConnector, UnsupportedDatabaseError
from .sqlite_connector import SQLiteConnector


class ConnectorFactory:
    """
    Factory for creating appropriate database connectors based on file extension.

    Usage:
        connector = ConnectorFactory.create_connector("/path/to/database.db")
        connector.connect("/path/to/database.db")
    """

    # Mapping of file extensions to connector classes
    _connectors: Dict[str, Type[BaseConnector]] = {
        '.db': SQLiteConnector,
        '.sqlite': SQLiteConnector,
        '.sqlite3': SQLiteConnector,
        # Future connectors:
        # '.duckdb': DuckDBConnector,
        # '.mdb': AccessConnector,
        # '.accdb': AccessConnector,
    }

    @classmethod
    def create_connector(cls, file_path: str) -> BaseConnector:
        """
        Create a connector based on file extension.

        Args:
            file_path: Path to the database file

        Returns:
            Appropriate BaseConnector subclass instance

        Raises:
            UnsupportedDatabaseError: If file extension is not supported
        """
        ext = Path(file_path).suffix.lower()

        if ext not in cls._connectors:
            supported = ', '.join(cls.get_supported_extensions())
            raise UnsupportedDatabaseError(
                f"Unsupported file type: {ext}. Supported types: {supported}"
            )

        connector_class = cls._connectors[ext]
        return connector_class()

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List of extension strings (e.g., ['.db', '.sqlite', '.sqlite3'])
        """
        return list(cls._connectors.keys())

    @classmethod
    def get_file_filter(cls) -> str:
        """
        Get file dialog filter string for supported databases.

        Returns:
            Filter string for QFileDialog (e.g., "Database Files (*.db *.sqlite)")
        """
        exts = ' '.join(f'*{ext}' for ext in cls._connectors.keys())
        return f"Database Files ({exts})"

    @classmethod
    def get_all_filters(cls) -> str:
        """
        Get complete file dialog filter with individual type filters.

        Returns:
            Multi-line filter string for QFileDialog
        """
        filters = [cls.get_file_filter()]

        # Add individual type filters
        filters.append("SQLite Database (*.db *.sqlite *.sqlite3)")

        # Future:
        # filters.append("DuckDB Database (*.duckdb)")
        # filters.append("Access Database (*.mdb *.accdb)")

        filters.append("All Files (*)")

        return ";;".join(filters)

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        Check if a file type is supported.

        Args:
            file_path: Path to the database file

        Returns:
            True if file type is supported
        """
        ext = Path(file_path).suffix.lower()
        return ext in cls._connectors

    @classmethod
    def register_connector(
        cls,
        extension: str,
        connector_class: Type[BaseConnector]
    ) -> None:
        """
        Register a new connector for an extension.

        Args:
            extension: File extension (e.g., '.duckdb')
            connector_class: BaseConnector subclass
        """
        if not extension.startswith('.'):
            extension = '.' + extension

        cls._connectors[extension.lower()] = connector_class

    @classmethod
    def get_database_type(cls, file_path: str) -> str:
        """
        Get database type name for a file.

        Args:
            file_path: Path to the database file

        Returns:
            Database type name (e.g., 'SQLite')

        Raises:
            UnsupportedDatabaseError: If file type is not supported
        """
        connector = cls.create_connector(file_path)
        return connector.database_type
