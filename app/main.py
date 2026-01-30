"""
Local DB Viewer - Application entry point.

A PySide6 desktop application for viewing local database files.
"""

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_stylesheet() -> str:
    """Load the dark theme stylesheet."""
    style_path = Path(__file__).parent.parent / "resources" / "styles" / "dark_theme.qss"
    if style_path.exists():
        with open(style_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def main():
    """Application main entry point."""
    logger.info("Starting Local DB Viewer")

    # High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Local DB Viewer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Local DB Viewer")

    # Load stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
        logger.info("Dark theme loaded")

    # Import and create main window
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    logger.info("Application window shown")

    # Start event loop
    exit_code = app.exec()

    logger.info(f"Application exiting with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
