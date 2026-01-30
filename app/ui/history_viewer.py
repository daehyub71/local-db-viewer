"""
Query history viewer widget.
"""

import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot

from app.db.query_history import QueryHistoryDB, QueryRecord

logger = logging.getLogger(__name__)


class HistoryViewer(QWidget):
    """
    Widget for displaying query history.

    Features:
    - View query history
    - Search queries
    - Double-click to load query into editor
    - Clear history

    Signals:
        query_selected(str): Emitted when a query is selected
    """

    query_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.history_db = QueryHistoryDB()

        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()

        header_label = QLabel("Query History")
        header_label.setProperty("heading", "true")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search queries...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._on_search_changed)
        header_layout.addWidget(self.search_input)

        # Refresh button
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setProperty("secondary", "true")
        self.btn_refresh.clicked.connect(self._load_history)
        header_layout.addWidget(self.btn_refresh)

        # Clear button
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setProperty("secondary", "true")
        self.btn_clear.clicked.connect(self._on_clear_history)
        header_layout.addWidget(self.btn_clear)

        layout.addLayout(header_layout)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Query", "Time (s)", "Rows", "Status"
        ])

        # Column widths
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.doubleClicked.connect(self._on_double_clicked)

        layout.addWidget(self.history_table)

        # Statistics label
        self.stats_label = QLabel("")
        layout.addWidget(self.stats_label)

    def _load_history(self):
        """Load query history from database."""
        search_term = self.search_input.text().strip()

        if search_term:
            records = self.history_db.search_history(search_term)
        else:
            records = self.history_db.get_history(limit=200)

        self._display_records(records)

        # Update statistics
        stats = self.history_db.get_statistics()
        if stats:
            self.stats_label.setText(
                f"Total: {stats.get('total', 0)} queries | "
                f"Success: {stats.get('success', 0)} | "
                f"Failed: {stats.get('failed', 0)} | "
                f"Avg time: {stats.get('avg_execution_time', 0):.3f}s"
            )

    def _display_records(self, records: list):
        """Display query records in table."""
        self.history_table.setRowCount(len(records))

        for row_idx, record in enumerate(records):
            # Timestamp
            try:
                dt = datetime.fromisoformat(record.timestamp)
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                timestamp_str = record.timestamp

            timestamp_item = QTableWidgetItem(timestamp_str)
            timestamp_item.setData(Qt.UserRole, record)
            self.history_table.setItem(row_idx, 0, timestamp_item)

            # Query (truncated)
            query_text = record.query_text.replace('\n', ' ').strip()
            if len(query_text) > 100:
                query_text = query_text[:100] + "..."
            self.history_table.setItem(row_idx, 1, QTableWidgetItem(query_text))

            # Execution time
            time_item = QTableWidgetItem(f"{record.execution_time:.3f}")
            time_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.history_table.setItem(row_idx, 2, time_item)

            # Row count
            rows_item = QTableWidgetItem(f"{record.row_count:,}")
            rows_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.history_table.setItem(row_idx, 3, rows_item)

            # Status
            status_text = "OK" if record.success else "Error"
            status_item = QTableWidgetItem(status_text)
            if not record.success:
                status_item.setForeground(Qt.red)
                status_item.setToolTip(record.error_message)
            self.history_table.setItem(row_idx, 4, status_item)

    def add_query(self, query: str, database_path: str, execution_time: float,
                  row_count: int, success: bool, error_message: str = ""):
        """
        Add a query to history.

        Args:
            query: SQL query text
            database_path: Path to database file
            execution_time: Query execution time in seconds
            row_count: Number of rows returned/affected
            success: Whether query succeeded
            error_message: Error message if failed
        """
        record = QueryRecord(
            database_path=database_path,
            query_text=query,
            execution_time=execution_time,
            row_count=row_count,
            success=success,
            error_message=error_message,
        )

        self.history_db.add_query(record)
        self._load_history()

    @Slot()
    def _on_search_changed(self):
        """Handle search input change."""
        self._load_history()

    @Slot()
    def _on_double_clicked(self):
        """Handle double click on history item."""
        current_row = self.history_table.currentRow()
        if current_row >= 0:
            timestamp_item = self.history_table.item(current_row, 0)
            if timestamp_item:
                record = timestamp_item.data(Qt.UserRole)
                if record:
                    self.query_selected.emit(record.query_text)
                    logger.debug(f"Selected query from history: {record.query_text[:50]}...")

    @Slot()
    def _on_clear_history(self):
        """Handle clear history button click."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all query history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.history_db.clear_history():
                self._load_history()
                logger.info("Query history cleared")
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to clear query history"
                )
