"""
SQL query editor widget.
"""

import logging
import csv
import json
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QTextEdit, QFileDialog,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from app.core.connectors import BaseConnector, QueryResult
from app.utils.sql_highlighter import SQLSyntaxHighlighter

logger = logging.getLogger(__name__)


class QueryEditor(QWidget):
    """
    SQL query editor with syntax highlighting and result display.

    Signals:
        query_executed(dict): Emitted when query execution completes
        execute_requested(): Emitted when execute is requested
    """

    query_executed = Signal(dict)
    execute_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.connector: Optional[BaseConnector] = None
        self.last_result: Optional[QueryResult] = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Splitter for editor and results
        splitter = QSplitter(Qt.Vertical)

        # Top section - Query editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(4)

        # Editor header
        editor_header = QHBoxLayout()
        editor_header.addWidget(QLabel("SQL Query"))
        editor_header.addStretch()

        self.btn_execute = QPushButton("Execute (F5)")
        self.btn_execute.clicked.connect(self.execute_query)
        editor_header.addWidget(self.btn_execute)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setProperty("secondary", "true")
        self.btn_clear.clicked.connect(self.clear)
        editor_header.addWidget(self.btn_clear)

        editor_layout.addLayout(editor_header)

        # SQL editor
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Enter SQL query here...\nExample: SELECT * FROM table_name LIMIT 100")
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        self.editor.setTabStopDistance(40)  # 4 spaces

        # Syntax highlighter
        self.highlighter = SQLSyntaxHighlighter(self.editor.document())

        editor_layout.addWidget(self.editor)

        splitter.addWidget(editor_widget)

        # Bottom section - Results
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(4)

        # Results header
        results_header = QHBoxLayout()

        self.results_label = QLabel("Results")
        results_header.addWidget(self.results_label)

        results_header.addStretch()

        self.time_label = QLabel("")
        results_header.addWidget(self.time_label)

        self.btn_export = QPushButton("Export")
        self.btn_export.setProperty("secondary", "true")
        self.btn_export.clicked.connect(self.export_results)
        self.btn_export.setEnabled(False)
        results_header.addWidget(self.btn_export)

        results_layout.addLayout(results_header)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        results_layout.addWidget(self.results_table)

        # Error display
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setMaximumHeight(100)
        self.error_text.setStyleSheet("color: #f44336; background-color: #2d1e1e;")
        self.error_text.hide()
        results_layout.addWidget(self.error_text)

        splitter.addWidget(results_widget)

        # Set splitter sizes
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def set_connector(self, connector: BaseConnector):
        """Set the database connector."""
        self.connector = connector

    def set_query(self, query: str):
        """Set the query text."""
        self.editor.setPlainText(query)

    def get_query(self) -> str:
        """Get the current query text."""
        return self.editor.toPlainText().strip()

    def clear(self):
        """Clear the editor and results."""
        self.editor.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.error_text.clear()
        self.error_text.hide()
        self.results_label.setText("Results")
        self.time_label.setText("")
        self.btn_export.setEnabled(False)
        self.last_result = None

    @Slot()
    def execute_query(self):
        """Execute the current query."""
        if not self.connector:
            self._show_error("No database connected")
            return

        query = self.get_query()
        if not query:
            self._show_error("Please enter a query")
            return

        # Clear previous results
        self.error_text.hide()
        self.results_table.setRowCount(0)

        try:
            result = self.connector.execute_query(query)
            self.last_result = result

            if result.success:
                self._display_result(result)
                self.query_executed.emit({
                    'success': True,
                    'execution_time': result.execution_time,
                    'row_count': result.row_count,
                    'query': query,
                })
                logger.info(f"Query executed: {result.row_count} rows in {result.execution_time:.3f}s")
            else:
                self._show_error(result.error or "Unknown error")
                self.query_executed.emit({
                    'success': False,
                    'error': result.error,
                    'query': query,
                })

        except Exception as e:
            self._show_error(str(e))
            self.query_executed.emit({
                'success': False,
                'error': str(e),
                'query': query,
            })
            logger.error(f"Query execution failed: {e}")

    def _display_result(self, result: QueryResult):
        """Display query result in table."""
        # Update header
        self.results_label.setText(f"Results ({result.row_count:,} rows)")
        self.time_label.setText(f"Execution time: {result.execution_time:.3f}s")

        # Setup columns
        self.results_table.setColumnCount(len(result.columns))
        self.results_table.setHorizontalHeaderLabels(result.columns)

        # Populate data
        self.results_table.setRowCount(len(result.rows))
        for row_idx, row in enumerate(result.rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "NULL")
                if value is None:
                    item.setForeground(Qt.gray)
                self.results_table.setItem(row_idx, col_idx, item)

        # Resize columns
        self.results_table.resizeColumnsToContents()

        # Enable export
        self.btn_export.setEnabled(result.row_count > 0)

    def _show_error(self, error: str):
        """Display error message."""
        self.error_text.setText(f"Error: {error}")
        self.error_text.show()
        self.results_label.setText("Results")
        self.time_label.setText("")
        self.btn_export.setEnabled(False)

    @Slot()
    def export_results(self):
        """Export query results to file."""
        if not self.last_result or not self.last_result.success:
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "query_results.csv",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            path = Path(file_path)
            if path.suffix.lower() == '.json':
                self._export_json(path)
            else:
                self._export_csv(path)

            QMessageBox.information(
                self,
                "Export Complete",
                f"Results exported to:\n{file_path}"
            )
            logger.info(f"Exported results to {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export results:\n{e}"
            )
            logger.error(f"Export failed: {e}")

    def _export_csv(self, path: Path):
        """Export results to CSV."""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.last_result.columns)
            writer.writerows(self.last_result.rows)

    def _export_json(self, path: Path):
        """Export results to JSON."""
        data = []
        for row in self.last_result.rows:
            record = {}
            for col_idx, col_name in enumerate(self.last_result.columns):
                value = row[col_idx]
                # Convert non-serializable types
                if isinstance(value, bytes):
                    value = value.hex()
                record[col_name] = value
            data.append(record)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
