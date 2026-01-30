"""
Data viewer widget for displaying table data with pagination.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QComboBox, QSpinBox, QHeaderView
)
from PySide6.QtCore import Qt, Slot

from app.core.connectors import BaseConnector, QueryResult

logger = logging.getLogger(__name__)


class DataViewer(QWidget):
    """
    Widget for displaying table data with pagination.

    Features:
    - Paginated data display
    - Column sorting
    - Page size selection
    - Navigation buttons
    """

    PAGE_SIZES = [50, 100, 200, 500, 1000]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.connector: Optional[BaseConnector] = None
        self.table_name: Optional[str] = None
        self.current_page = 1
        self.page_size = 100
        self.total_rows = 0
        self.order_by: Optional[str] = None
        self.order_desc = False

        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        self.header_label = QLabel("Select a table to view data")
        self.header_label.setProperty("heading", "true")
        layout.addWidget(self.header_label)

        # Data table
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self.data_table.horizontalHeader().setSectionsClickable(True)
        layout.addWidget(self.data_table)

        # Pagination controls
        pagination_widget = QWidget()
        pagination_layout = QHBoxLayout(pagination_widget)
        pagination_layout.setContentsMargins(0, 0, 0, 0)
        pagination_layout.setSpacing(8)

        # First/Previous buttons
        self.btn_first = QPushButton("<<")
        self.btn_first.setProperty("secondary", "true")
        self.btn_first.setMaximumWidth(40)
        self.btn_first.clicked.connect(self._on_first_page)
        pagination_layout.addWidget(self.btn_first)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setProperty("secondary", "true")
        self.btn_prev.setMaximumWidth(40)
        self.btn_prev.clicked.connect(self._on_prev_page)
        pagination_layout.addWidget(self.btn_prev)

        # Page info
        self.page_label = QLabel("Page 0 of 0")
        pagination_layout.addWidget(self.page_label)

        # Page number input
        self.page_input = QSpinBox()
        self.page_input.setMinimum(1)
        self.page_input.setMaximum(1)
        self.page_input.setMaximumWidth(80)
        self.page_input.valueChanged.connect(self._on_page_changed)
        pagination_layout.addWidget(self.page_input)

        # Next/Last buttons
        self.btn_next = QPushButton(">")
        self.btn_next.setProperty("secondary", "true")
        self.btn_next.setMaximumWidth(40)
        self.btn_next.clicked.connect(self._on_next_page)
        pagination_layout.addWidget(self.btn_next)

        self.btn_last = QPushButton(">>")
        self.btn_last.setProperty("secondary", "true")
        self.btn_last.setMaximumWidth(40)
        self.btn_last.clicked.connect(self._on_last_page)
        pagination_layout.addWidget(self.btn_last)

        pagination_layout.addStretch()

        # Page size selector
        pagination_layout.addWidget(QLabel("Rows per page:"))
        self.page_size_combo = QComboBox()
        for size in self.PAGE_SIZES:
            self.page_size_combo.addItem(str(size), size)
        self.page_size_combo.setCurrentIndex(1)  # Default 100
        self.page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        pagination_layout.addWidget(self.page_size_combo)

        # Total rows label
        self.total_label = QLabel("Total: 0 rows")
        pagination_layout.addWidget(self.total_label)

        layout.addWidget(pagination_widget)

    def set_table(self, connector: BaseConnector, table_name: str):
        """
        Set the table to display.

        Args:
            connector: Database connector
            table_name: Name of the table
        """
        self.connector = connector
        self.table_name = table_name
        self.current_page = 1
        self.order_by = None
        self.order_desc = False

        # Get total rows
        self.total_rows = connector.get_row_count(table_name)
        self._update_pagination_controls()
        self._load_data()

    def clear(self):
        """Clear the data display."""
        self.connector = None
        self.table_name = None
        self.current_page = 1
        self.total_rows = 0
        self.order_by = None
        self.order_desc = False

        self.header_label.setText("Select a table to view data")
        self.data_table.setRowCount(0)
        self.data_table.setColumnCount(0)
        self._update_pagination_controls()

    def set_query_result(self, result: QueryResult):
        """
        Display query result data.

        Args:
            result: QueryResult object
        """
        self.table_name = None
        self.total_rows = result.row_count
        self.current_page = 1

        self.header_label.setText(f"Query Results ({result.row_count:,} rows)")

        # Setup columns
        self.data_table.setColumnCount(len(result.columns))
        self.data_table.setHorizontalHeaderLabels(result.columns)

        # Populate data
        self.data_table.setRowCount(len(result.rows))
        for row_idx, row in enumerate(result.rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "NULL")
                if value is None:
                    item.setForeground(Qt.gray)
                self.data_table.setItem(row_idx, col_idx, item)

        # Resize columns
        self.data_table.resizeColumnsToContents()

        self._update_pagination_controls()

    def _load_data(self):
        """Load data for current page."""
        if not self.connector or not self.table_name:
            return

        offset = (self.current_page - 1) * self.page_size

        try:
            result = self.connector.get_table_data(
                self.table_name,
                offset=offset,
                limit=self.page_size,
                order_by=self.order_by,
                order_desc=self.order_desc
            )

            if result.success:
                self._display_result(result)
            else:
                logger.error(f"Failed to load data: {result.error}")

        except Exception as e:
            logger.error(f"Error loading data: {e}")

    def _display_result(self, result: QueryResult):
        """Display query result in table."""
        # Update header
        self.header_label.setText(
            f"Table: {self.table_name} (showing {len(result.rows):,} of {self.total_rows:,} rows)"
        )

        # Setup columns
        self.data_table.setColumnCount(len(result.columns))
        self.data_table.setHorizontalHeaderLabels(result.columns)

        # Populate data
        self.data_table.setRowCount(len(result.rows))
        for row_idx, row in enumerate(result.rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "NULL")
                if value is None:
                    item.setForeground(Qt.gray)
                self.data_table.setItem(row_idx, col_idx, item)

        # Resize columns to content
        self.data_table.resizeColumnsToContents()

    def _update_pagination_controls(self):
        """Update pagination control states."""
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)

        self.page_label.setText(f"Page {self.current_page} of {total_pages}")
        self.page_input.setMaximum(total_pages)
        self.page_input.setValue(self.current_page)
        self.total_label.setText(f"Total: {self.total_rows:,} rows")

        # Enable/disable navigation buttons
        self.btn_first.setEnabled(self.current_page > 1)
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < total_pages)
        self.btn_last.setEnabled(self.current_page < total_pages)

    @Slot()
    def _on_first_page(self):
        """Go to first page."""
        if self.current_page != 1:
            self.current_page = 1
            self._update_pagination_controls()
            self._load_data()

    @Slot()
    def _on_prev_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_pagination_controls()
            self._load_data()

    @Slot()
    def _on_next_page(self):
        """Go to next page."""
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self._update_pagination_controls()
            self._load_data()

    @Slot()
    def _on_last_page(self):
        """Go to last page."""
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page != total_pages:
            self.current_page = total_pages
            self._update_pagination_controls()
            self._load_data()

    @Slot(int)
    def _on_page_changed(self, page: int):
        """Handle page number input change."""
        if page != self.current_page and page >= 1:
            total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
            if page <= total_pages:
                self.current_page = page
                self._update_pagination_controls()
                self._load_data()

    @Slot(int)
    def _on_page_size_changed(self, index: int):
        """Handle page size change."""
        new_size = self.page_size_combo.currentData()
        if new_size and new_size != self.page_size:
            self.page_size = new_size
            self.current_page = 1
            self._update_pagination_controls()
            self._load_data()

    @Slot(int)
    def _on_header_clicked(self, column: int):
        """Handle column header click for sorting."""
        if not self.table_name:
            return

        column_name = self.data_table.horizontalHeaderItem(column).text()

        if self.order_by == column_name:
            # Toggle sort direction
            self.order_desc = not self.order_desc
        else:
            # New column, ascending
            self.order_by = column_name
            self.order_desc = False

        self.current_page = 1
        self._update_pagination_controls()
        self._load_data()

        logger.debug(f"Sorting by {self.order_by} {'DESC' if self.order_desc else 'ASC'}")
