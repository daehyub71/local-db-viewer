"""
Main window for Local DB Viewer.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QKeySequence

from app.core.connectors import (
    BaseConnector, ConnectorFactory, TableSchema,
    ConnectionError, UnsupportedDatabaseError
)
from app.ui.database_tree import DatabaseTreeWidget
from app.ui.schema_viewer import SchemaViewer
from app.ui.data_viewer import DataViewer
from app.ui.query_editor import QueryEditor
from app.ui.history_viewer import HistoryViewer

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.connector: Optional[BaseConnector] = None
        self.current_table: Optional[str] = None

        self._setup_ui()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        self._connect_signals()

        logger.info("MainWindow initialized")

    def _setup_ui(self):
        """Setup the main UI layout."""
        self.setWindowTitle("Local DB Viewer")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter for left/right panels
        self.splitter = QSplitter(Qt.Horizontal)

        # Left panel - Database tree
        self.database_tree = DatabaseTreeWidget()
        self.database_tree.setMinimumWidth(200)
        self.database_tree.setMaximumWidth(400)

        # Right panel - Tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.schema_viewer = SchemaViewer()
        self.data_viewer = DataViewer()
        self.query_editor = QueryEditor()
        self.history_viewer = HistoryViewer()

        self.tab_widget.addTab(self.schema_viewer, "Schema")
        self.tab_widget.addTab(self.data_viewer, "Data")
        self.tab_widget.addTab(self.query_editor, "Query")
        self.tab_widget.addTab(self.history_viewer, "History")

        # Add to splitter
        self.splitter.addWidget(self.database_tree)
        self.splitter.addWidget(self.tab_widget)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)

        main_layout.addWidget(self.splitter)

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        self.action_open = QAction("Open Database...", self)
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_open.triggered.connect(self._on_open_database)
        file_menu.addAction(self.action_open)

        self.action_close = QAction("Close Database", self)
        self.action_close.setShortcut(QKeySequence("Ctrl+W"))
        self.action_close.triggered.connect(self._on_close_database)
        self.action_close.setEnabled(False)
        file_menu.addAction(self.action_close)

        file_menu.addSeparator()

        self.action_exit = QAction("Exit", self)
        self.action_exit.setShortcut(QKeySequence.Quit)
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        self.action_copy = QAction("Copy", self)
        self.action_copy.setShortcut(QKeySequence.Copy)
        edit_menu.addAction(self.action_copy)

        # Query menu
        query_menu = menubar.addMenu("Query")

        self.action_execute = QAction("Execute Query", self)
        self.action_execute.setShortcut(QKeySequence("F5"))
        self.action_execute.triggered.connect(self._on_execute_query)
        self.action_execute.setEnabled(False)
        query_menu.addAction(self.action_execute)

        self.action_cancel = QAction("Cancel Query", self)
        self.action_cancel.setShortcut(QKeySequence("Ctrl+Break"))
        self.action_cancel.setEnabled(False)
        query_menu.addAction(self.action_cancel)

        query_menu.addSeparator()

        self.action_clear = QAction("Clear Editor", self)
        self.action_clear.triggered.connect(self._on_clear_editor)
        query_menu.addAction(self.action_clear)

        # View menu
        view_menu = menubar.addMenu("View")

        self.action_refresh = QAction("Refresh", self)
        self.action_refresh.setShortcut(QKeySequence.Refresh)
        self.action_refresh.triggered.connect(self._on_refresh)
        self.action_refresh.setEnabled(False)
        view_menu.addAction(self.action_refresh)

        # Help menu
        help_menu = menubar.addMenu("Help")

        self.action_about = QAction("About", self)
        self.action_about.triggered.connect(self._on_about)
        help_menu.addAction(self.action_about)

    def _create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Open button
        self.btn_open = QAction("Open", self)
        self.btn_open.setToolTip("Open Database (Ctrl+O)")
        self.btn_open.triggered.connect(self._on_open_database)
        toolbar.addAction(self.btn_open)

        # Refresh button
        self.btn_refresh = QAction("Refresh", self)
        self.btn_refresh.setToolTip("Refresh (F5)")
        self.btn_refresh.triggered.connect(self._on_refresh)
        self.btn_refresh.setEnabled(False)
        toolbar.addAction(self.btn_refresh)

        toolbar.addSeparator()

        # Execute button
        self.btn_execute = QAction("Execute", self)
        self.btn_execute.setToolTip("Execute Query (F5)")
        self.btn_execute.triggered.connect(self._on_execute_query)
        self.btn_execute.setEnabled(False)
        toolbar.addAction(self.btn_execute)

        # Cancel button
        self.btn_cancel = QAction("Cancel", self)
        self.btn_cancel.setToolTip("Cancel Query")
        self.btn_cancel.setEnabled(False)
        toolbar.addAction(self.btn_cancel)

        toolbar.addSeparator()

        # Export button
        self.btn_export = QAction("Export", self)
        self.btn_export.setToolTip("Export Results")
        self.btn_export.triggered.connect(self._on_export)
        self.btn_export.setEnabled(False)
        toolbar.addAction(self.btn_export)

    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Connection status label
        self.status_connection = QLabel("Not connected")
        self.status_bar.addWidget(self.status_connection)

        # Table count label
        self.status_tables = QLabel("")
        self.status_bar.addPermanentWidget(self.status_tables)

        # Row count label
        self.status_rows = QLabel("")
        self.status_bar.addPermanentWidget(self.status_rows)

        # Query time label
        self.status_query_time = QLabel("")
        self.status_bar.addPermanentWidget(self.status_query_time)

    def _connect_signals(self):
        """Connect widget signals."""
        # Database tree signals
        self.database_tree.database_opened.connect(self._on_database_opened)
        self.database_tree.table_selected.connect(self._on_table_selected)
        self.database_tree.open_requested.connect(self._on_open_database)

        # Query editor signals
        self.query_editor.query_executed.connect(self._on_query_result)
        self.query_editor.execute_requested.connect(self._on_execute_query)

        # History viewer signals
        self.history_viewer.query_selected.connect(self._on_history_query_selected)

    @Slot()
    def _on_open_database(self):
        """Open a database file."""
        file_filter = ConnectorFactory.get_all_filters()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Database",
            "",
            file_filter
        )

        if file_path:
            self._open_database(file_path)

    def _open_database(self, file_path: str):
        """Open the specified database file."""
        try:
            # Close existing connection
            if self.connector:
                self.connector.disconnect()

            # Create connector and connect
            self.connector = ConnectorFactory.create_connector(file_path)
            self.connector.connect(file_path)

            # Update UI
            self.database_tree.set_database(self.connector)
            self.query_editor.set_connector(self.connector)

            # Enable actions
            self.action_close.setEnabled(True)
            self.action_execute.setEnabled(True)
            self.action_refresh.setEnabled(True)
            self.btn_refresh.setEnabled(True)
            self.btn_execute.setEnabled(True)

            # Update status bar
            db_name = Path(file_path).name
            tables = self.connector.get_tables()
            self.status_connection.setText(f"Connected: {db_name}")
            self.status_tables.setText(f"Tables: {len(tables)}")

            logger.info(f"Opened database: {file_path}")

        except (ConnectionError, UnsupportedDatabaseError) as e:
            QMessageBox.critical(self, "Error", f"Failed to open database:\n{e}")
            logger.error(f"Failed to open database: {e}")

    @Slot()
    def _on_close_database(self):
        """Close the current database connection."""
        if self.connector:
            self.connector.disconnect()
            self.connector = None

        # Clear UI
        self.database_tree.clear_database()
        self.schema_viewer.clear()
        self.data_viewer.clear()
        self.query_editor.clear()

        # Disable actions
        self.action_close.setEnabled(False)
        self.action_execute.setEnabled(False)
        self.action_refresh.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.btn_execute.setEnabled(False)
        self.btn_export.setEnabled(False)

        # Update status bar
        self.status_connection.setText("Not connected")
        self.status_tables.setText("")
        self.status_rows.setText("")
        self.status_query_time.setText("")

        self.current_table = None
        logger.info("Database closed")

    @Slot(str)
    def _on_database_opened(self, file_path: str):
        """Handle database opened from tree widget."""
        self._open_database(file_path)

    @Slot(str)
    def _on_table_selected(self, table_name: str):
        """Handle table selection from tree widget."""
        if not self.connector:
            return

        self.current_table = table_name

        # Load schema
        try:
            schema = self.connector.get_schema(table_name)
            self.schema_viewer.set_schema(schema)
            self.status_rows.setText(f"Rows: {schema.row_count:,}")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")

        # Load data
        try:
            self.data_viewer.set_table(self.connector, table_name)
        except Exception as e:
            logger.error(f"Failed to load data: {e}")

        # Switch to schema tab
        self.tab_widget.setCurrentWidget(self.schema_viewer)

    @Slot()
    def _on_execute_query(self):
        """Execute the current query."""
        if not self.connector:
            return

        # Switch to query tab and execute
        self.tab_widget.setCurrentWidget(self.query_editor)
        self.query_editor.execute_query()

    @Slot(dict)
    def _on_query_result(self, result: dict):
        """Handle query execution result."""
        if result.get('success'):
            execution_time = result.get('execution_time', 0)
            row_count = result.get('row_count', 0)
            self.status_query_time.setText(f"Time: {execution_time:.3f}s")
            self.status_rows.setText(f"Rows: {row_count:,}")
            self.btn_export.setEnabled(row_count > 0)
        else:
            self.status_query_time.setText("")
            self.btn_export.setEnabled(False)

    @Slot()
    def _on_clear_editor(self):
        """Clear the query editor."""
        self.query_editor.clear()

    @Slot()
    def _on_refresh(self):
        """Refresh the current view."""
        if not self.connector:
            return

        # Refresh tree
        self.database_tree.refresh()

        # Refresh current table if selected
        if self.current_table:
            self._on_table_selected(self.current_table)

    @Slot()
    def _on_export(self):
        """Export query results."""
        self.query_editor.export_results()

    @Slot(str)
    def _on_history_query_selected(self, query: str):
        """Handle query selection from history."""
        self.query_editor.set_query(query)
        self.tab_widget.setCurrentWidget(self.query_editor)

    @Slot()
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Local DB Viewer",
            "<h3>Local DB Viewer</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A desktop application for viewing local database files.</p>"
            "<p>Supported formats: SQLite (.db, .sqlite, .sqlite3)</p>"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        if self.connector:
            self.connector.disconnect()
        event.accept()
