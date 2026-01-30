# Local DB Viewer

A lightweight, portable desktop application for viewing and querying local database files. Built with PySide6 (Qt6) for offline/air-gapped environments.

[한국어 README](README_KO.md)

## Features

- **Multi-format Support**: SQLite (.db, .sqlite, .sqlite3) with extensible connector architecture
- **Database Explorer**: Tree view of tables, columns, and indexes
- **Schema Viewer**: Column types, constraints, primary/foreign keys, DDL
- **Data Viewer**: Paginated data display with column sorting
- **SQL Query Editor**: Syntax highlighting, execution time tracking
- **Query History**: Persistent history with search functionality
- **Export**: CSV and JSON export support
- **Dark Theme**: Modern VS Code-inspired dark UI
- **Portable**: Single EXE deployment for VDI/air-gapped environments

## Screenshots

```
+----------------------------------------------------------+
| File  Edit  Query  View  Help                             |
+----------------------------------------------------------+
| [Open] [Refresh] | [Execute F5] [Cancel] | [Export]       |
+----------------------------------------------------------+
|                  |                                        |
| Database Tree    | [Schema] [Data] [Query] [History]      |
|                  |                                        |
| + sample.db      |  Column   | Type    | Nullable | PK   |
|   - users        |  ---------|---------|----------|------|
|   - orders       |  id       | INTEGER | NO       | YES  |
|   - products     |  name     | TEXT    | NO       |      |
|                  |                                        |
+----------------------------------------------------------+
| Connected: sample.db | Tables: 3 | Query: 0.05s          |
+----------------------------------------------------------+
```

## Installation

### Prerequisites

- Python 3.9+
- PySide6

### Quick Start

```bash
# Clone repository
git clone https://github.com/daehyub71/local-db-viewer.git
cd local-db-viewer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python run.py
```

### Create Sample Database (Optional)

```bash
python scripts/create_sample_db.py
```

This creates a sample SQLite database at `data/sample/sample.db` with users, orders, and products tables.

## Usage

1. **Open Database**: Click "Open" or use `Ctrl+O` to select a database file
2. **Browse Tables**: Click on tables in the left panel tree view
3. **View Schema**: See column definitions, types, and constraints in the Schema tab
4. **View Data**: Browse paginated data in the Data tab (click headers to sort)
5. **Execute Queries**: Write SQL in the Query tab and press `F5` to execute
6. **Export Results**: Click "Export" to save results as CSV or JSON

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open database |
| `Ctrl+W` | Close database |
| `F5` | Execute query / Refresh |
| `Ctrl+Q` | Exit |

## Building Portable EXE

For deployment to air-gapped/VDI environments:

```bash
# Install PyInstaller
pip install pyinstaller

# Build EXE
python scripts/build_exe.py
```

Output: `dist/LocalDBViewer_Portable/`

The portable package includes:
- `LocalDBViewer.exe` - Main application
- `data/` - Query history storage
- `logs/` - Application logs
- `README.txt` - Quick start guide

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer (PySide6)                              │
│  - MainWindow, DatabaseTree, SchemaViewer, DataViewer      │
│  - QueryEditor, HistoryViewer                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│  Business Logic Layer                                       │
│  - BaseConnector (Abstract), SQLiteConnector                │
│  - ConnectorFactory, ExportService                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│  Data Layer                                                 │
│  - QueryHistoryDB (SQLite)                                  │
└─────────────────────────────────────────────────────────────┘
```

### Extensible Connector Architecture

Adding support for new database formats:

1. Create a new connector class inheriting from `BaseConnector`
2. Implement required methods: `connect()`, `get_tables()`, `get_schema()`, `execute_query()`, etc.
3. Register in `ConnectorFactory`

```python
# Example: Adding DuckDB support
class DuckDBConnector(BaseConnector):
    SUPPORTED_EXTENSIONS = ['.duckdb']

    def connect(self, file_path: str) -> bool:
        # Implementation
        pass

# Register
ConnectorFactory.register_connector('.duckdb', DuckDBConnector)
```

## Project Structure

```
local-db-viewer/
├── app/
│   ├── main.py                     # Entry point
│   ├── ui/                         # UI components
│   │   ├── main_window.py
│   │   ├── database_tree.py
│   │   ├── schema_viewer.py
│   │   ├── data_viewer.py
│   │   ├── query_editor.py
│   │   └── history_viewer.py
│   ├── core/connectors/            # Database connectors
│   │   ├── base_connector.py
│   │   ├── sqlite_connector.py
│   │   └── connector_factory.py
│   ├── db/query_history.py         # Query history persistence
│   └── utils/sql_highlighter.py    # SQL syntax highlighting
├── resources/styles/dark_theme.qss # Dark theme stylesheet
├── scripts/
│   ├── build_exe.py                # PyInstaller build script
│   └── create_sample_db.py         # Sample DB generator
├── run.py                          # Application launcher
├── LocalDBViewer.spec              # PyInstaller configuration
└── requirements.txt
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | ≥6.6.0 | Qt6 GUI framework |
| PyInstaller | ≥6.3.0 | EXE packaging (optional) |

**Note**: `sqlite3` is included in Python's standard library.

## Supported Database Formats

| Format | Extensions | Status |
|--------|------------|--------|
| SQLite | .db, .sqlite, .sqlite3 | ✅ Supported |
| DuckDB | .duckdb | 🔜 Planned |
| MS Access | .mdb, .accdb | 🔜 Planned |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [PySide6](https://doc.qt.io/qtforpython/) - Qt for Python
- [PyInstaller](https://pyinstaller.org/) - Python to EXE packaging
