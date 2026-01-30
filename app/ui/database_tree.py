"""
Database tree widget for displaying database structure.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QFileDialog
)
from PySide6.QtCore import Qt, Signal

from app.core.connectors import BaseConnector, ConnectorFactory

logger = logging.getLogger(__name__)


class DatabaseTreeWidget(QWidget):
    """
    Widget for displaying database structure as a tree.

    Signals:
        database_opened(str): Emitted when a database file is opened
        table_selected(str): Emitted when a table is selected
        open_requested(): Emitted when open button is clicked
    """

    database_opened = Signal(str)
    table_selected = Signal(str)
    open_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.connector: Optional[BaseConnector] = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header label
        header = QLabel("Database Explorer")
        header.setProperty("heading", "true")
        layout.addWidget(header)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

        # Open button
        self.btn_open = QPushButton("Open Database...")
        self.btn_open.clicked.connect(self._on_open_clicked)
        layout.addWidget(self.btn_open)

    def set_database(self, connector: BaseConnector):
        """
        Set the database connector and populate the tree.

        Args:
            connector: Database connector instance
        """
        self.connector = connector
        self._populate_tree()

    def clear_database(self):
        """Clear the database and tree."""
        self.connector = None
        self.tree.clear()

    def refresh(self):
        """Refresh the tree view."""
        if self.connector:
            self._populate_tree()

    def _populate_tree(self):
        """Populate the tree with database structure."""
        self.tree.clear()

        if not self.connector or not self.connector.is_connected:
            return

        # Create root node for database
        db_name = Path(self.connector.file_path).name if self.connector.file_path else "Database"
        db_item = QTreeWidgetItem([db_name])
        db_item.setData(0, Qt.UserRole, {"type": "database", "path": self.connector.file_path})
        self.tree.addTopLevelItem(db_item)

        # Add tables folder
        tables = self.connector.get_tables()
        if tables:
            tables_folder = QTreeWidgetItem(["Tables"])
            tables_folder.setData(0, Qt.UserRole, {"type": "folder", "name": "tables"})
            db_item.addChild(tables_folder)

            for table_name in tables:
                table_item = QTreeWidgetItem([table_name])
                table_item.setData(0, Qt.UserRole, {"type": "table", "name": table_name})
                tables_folder.addChild(table_item)

                # Add column info if we can get schema
                try:
                    schema = self.connector.get_schema(table_name)
                    for col in schema.columns:
                        col_text = f"{col.name} ({col.data_type})"
                        if col.is_primary_key:
                            col_text += " PK"
                        if not col.nullable:
                            col_text += " NOT NULL"
                        col_item = QTreeWidgetItem([col_text])
                        col_item.setData(0, Qt.UserRole, {
                            "type": "column",
                            "table": table_name,
                            "name": col.name
                        })
                        table_item.addChild(col_item)
                except Exception as e:
                    logger.warning(f"Failed to get schema for {table_name}: {e}")

            tables_folder.setExpanded(True)

        # Add views folder if there are views
        if hasattr(self.connector, 'get_views'):
            views = self.connector.get_views()
            if views:
                views_folder = QTreeWidgetItem(["Views"])
                views_folder.setData(0, Qt.UserRole, {"type": "folder", "name": "views"})
                db_item.addChild(views_folder)

                for view_name in views:
                    view_item = QTreeWidgetItem([view_name])
                    view_item.setData(0, Qt.UserRole, {"type": "view", "name": view_name})
                    views_folder.addChild(view_item)

        # Expand database item
        db_item.setExpanded(True)

        logger.info(f"Populated tree with {len(tables)} tables")

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get("type")

        if item_type == "table":
            table_name = data.get("name")
            self.table_selected.emit(table_name)
            logger.debug(f"Table selected: {table_name}")

        elif item_type == "view":
            view_name = data.get("name")
            self.table_selected.emit(view_name)
            logger.debug(f"View selected: {view_name}")

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double click."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get("type")

        if item_type in ("table", "view"):
            # Double click on table/view - emit selection signal
            name = data.get("name")
            self.table_selected.emit(name)

    def _on_open_clicked(self):
        """Handle open button click."""
        self.open_requested.emit()
