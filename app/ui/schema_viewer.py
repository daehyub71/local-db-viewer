"""
Schema viewer widget for displaying table schema information.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QSplitter, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt

from app.core.connectors import TableSchema

logger = logging.getLogger(__name__)


class SchemaViewer(QWidget):
    """
    Widget for displaying table schema information.

    Shows:
    - Column information (name, type, nullable, primary key, foreign key)
    - Index information
    - Table DDL (CREATE TABLE statement)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.schema: Optional[TableSchema] = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        self.header_label = QLabel("Select a table to view its schema")
        self.header_label.setProperty("heading", "true")
        layout.addWidget(self.header_label)

        # Splitter for columns/indexes and DDL
        splitter = QSplitter(Qt.Vertical)

        # Top section - Columns and Indexes
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        # Columns group
        columns_group = QGroupBox("Columns")
        columns_layout = QVBoxLayout(columns_group)
        columns_layout.setContentsMargins(4, 4, 4, 4)

        self.columns_table = QTableWidget()
        self.columns_table.setColumnCount(6)
        self.columns_table.setHorizontalHeaderLabels([
            "Column", "Type", "Nullable", "Default", "PK", "FK"
        ])
        self.columns_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.columns_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.columns_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.columns_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.columns_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.columns_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.columns_table.setAlternatingRowColors(True)
        self.columns_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.columns_table.setSelectionBehavior(QTableWidget.SelectRows)
        columns_layout.addWidget(self.columns_table)

        top_layout.addWidget(columns_group, 3)

        # Indexes group
        indexes_group = QGroupBox("Indexes")
        indexes_layout = QVBoxLayout(indexes_group)
        indexes_layout.setContentsMargins(4, 4, 4, 4)

        self.indexes_table = QTableWidget()
        self.indexes_table.setColumnCount(3)
        self.indexes_table.setHorizontalHeaderLabels(["Index Name", "Columns", "Unique"])
        self.indexes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.indexes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.indexes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.indexes_table.setAlternatingRowColors(True)
        self.indexes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.indexes_table.setSelectionBehavior(QTableWidget.SelectRows)
        indexes_layout.addWidget(self.indexes_table)

        top_layout.addWidget(indexes_group, 2)

        splitter.addWidget(top_widget)

        # Bottom section - DDL
        ddl_group = QGroupBox("DDL (CREATE TABLE)")
        ddl_layout = QVBoxLayout(ddl_group)
        ddl_layout.setContentsMargins(4, 4, 4, 4)

        self.ddl_text = QTextEdit()
        self.ddl_text.setReadOnly(True)
        self.ddl_text.setFont(self.ddl_text.font())
        self.ddl_text.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace;")
        ddl_layout.addWidget(self.ddl_text)

        splitter.addWidget(ddl_group)

        # Set splitter sizes
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def set_schema(self, schema: TableSchema):
        """
        Set the schema to display.

        Args:
            schema: TableSchema object
        """
        self.schema = schema
        self._update_display()

    def clear(self):
        """Clear the schema display."""
        self.schema = None
        self.header_label.setText("Select a table to view its schema")
        self.columns_table.setRowCount(0)
        self.indexes_table.setRowCount(0)
        self.ddl_text.clear()

    def _update_display(self):
        """Update the display with current schema."""
        if not self.schema:
            self.clear()
            return

        # Update header
        row_count = self.schema.row_count
        self.header_label.setText(
            f"Table: {self.schema.name} ({row_count:,} rows)"
        )

        # Update columns table
        self.columns_table.setRowCount(len(self.schema.columns))
        for row, col in enumerate(self.schema.columns):
            self.columns_table.setItem(row, 0, QTableWidgetItem(col.name))
            self.columns_table.setItem(row, 1, QTableWidgetItem(col.data_type))
            self.columns_table.setItem(row, 2, QTableWidgetItem("YES" if col.nullable else "NO"))
            self.columns_table.setItem(row, 3, QTableWidgetItem(col.default_value or ""))
            self.columns_table.setItem(row, 4, QTableWidgetItem("YES" if col.is_primary_key else ""))
            self.columns_table.setItem(row, 5, QTableWidgetItem(col.foreign_key or ""))

            # Highlight primary key rows
            if col.is_primary_key:
                for c in range(6):
                    item = self.columns_table.item(row, c)
                    if item:
                        item.setBackground(Qt.darkBlue)

        # Update indexes table
        self.indexes_table.setRowCount(len(self.schema.indexes))
        for row, idx in enumerate(self.schema.indexes):
            self.indexes_table.setItem(row, 0, QTableWidgetItem(idx.name))
            self.indexes_table.setItem(row, 1, QTableWidgetItem(", ".join(idx.columns)))
            self.indexes_table.setItem(row, 2, QTableWidgetItem("YES" if idx.is_unique else ""))

        # Update DDL
        self.ddl_text.setText(self.schema.ddl or "DDL not available")

        logger.debug(f"Displayed schema for table: {self.schema.name}")
