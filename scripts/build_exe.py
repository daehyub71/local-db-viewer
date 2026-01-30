#!/usr/bin/env python3
"""
Build script for Local DB Viewer.

Creates a portable EXE using PyInstaller.

Usage:
    python scripts/build_exe.py
    python scripts/build_exe.py --clean
    python scripts/build_exe.py --debug
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


class EXEBuilder:
    """Automated PyInstaller build with validation."""

    def __init__(self, project_root: Path, debug: bool = False):
        self.project_root = project_root
        self.debug = debug
        self.spec_file = project_root / "LocalDBViewer.spec"
        self.dist_dir = project_root / "dist"
        self.build_dir = project_root / "build"

    def pre_check(self) -> bool:
        """Verify preconditions for build."""
        print("=== Pre-build checks ===")

        # Check spec file exists
        if not self.spec_file.exists():
            print(f"ERROR: Spec file not found: {self.spec_file}")
            return False
        print(f"  [OK] Spec file: {self.spec_file}")

        # Check entry point exists
        entry_point = self.project_root / "app" / "main.py"
        if not entry_point.exists():
            print(f"ERROR: Entry point not found: {entry_point}")
            return False
        print(f"  [OK] Entry point: {entry_point}")

        # Check resources directory
        resources_dir = self.project_root / "resources"
        if not resources_dir.exists():
            print(f"WARNING: Resources directory not found: {resources_dir}")
        else:
            print(f"  [OK] Resources: {resources_dir}")

        # Check PyInstaller is installed
        try:
            import PyInstaller
            print(f"  [OK] PyInstaller version: {PyInstaller.__version__}")
        except ImportError:
            print("ERROR: PyInstaller not installed. Run: pip install pyinstaller")
            return False

        # Check PySide6 is installed
        try:
            import PySide6
            print(f"  [OK] PySide6 version: {PySide6.__version__}")
        except ImportError:
            print("ERROR: PySide6 not installed. Run: pip install PySide6")
            return False

        print()
        return True

    def clean_build(self):
        """Remove previous build artifacts."""
        print("=== Cleaning previous build ===")

        if self.dist_dir.exists():
            print(f"  Removing: {self.dist_dir}")
            shutil.rmtree(self.dist_dir)

        if self.build_dir.exists():
            print(f"  Removing: {self.build_dir}")
            shutil.rmtree(self.build_dir)

        print()

    def build(self) -> bool:
        """Execute PyInstaller build."""
        print("=== Building EXE ===")

        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(self.spec_file)
        ]

        if self.debug:
            cmd.append("--log-level=DEBUG")

        print(f"  Command: {' '.join(cmd)}")
        print()

        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            print(f"ERROR: Build failed with return code {result.returncode}")
            return False

        print()
        return True

    def post_check(self) -> bool:
        """Verify build output."""
        print("=== Post-build checks ===")

        # Check EXE was created
        exe_name = "LocalDBViewer.exe" if sys.platform == "win32" else "LocalDBViewer"
        exe_path = self.dist_dir / exe_name

        if not exe_path.exists():
            print(f"ERROR: EXE not found: {exe_path}")
            return False

        # Get file size
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  [OK] EXE created: {exe_path}")
        print(f"  [OK] Size: {size_mb:.2f} MB")

        print()
        return True

    def create_portable_package(self):
        """Create portable package structure."""
        print("=== Creating portable package ===")

        portable_dir = self.dist_dir / "LocalDBViewer_Portable"
        portable_dir.mkdir(exist_ok=True)

        # Copy EXE
        exe_name = "LocalDBViewer.exe" if sys.platform == "win32" else "LocalDBViewer"
        src_exe = self.dist_dir / exe_name
        dst_exe = portable_dir / exe_name

        if src_exe.exists():
            shutil.copy2(src_exe, dst_exe)
            print(f"  Copied: {dst_exe}")

        # Create data directory
        data_dir = portable_dir / "data"
        data_dir.mkdir(exist_ok=True)
        print(f"  Created: {data_dir}")

        # Create logs directory
        logs_dir = portable_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        print(f"  Created: {logs_dir}")

        # Create README
        readme_path = portable_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("""Local DB Viewer - Portable Edition
===================================

A desktop application for viewing local database files.

Supported Formats:
- SQLite (.db, .sqlite, .sqlite3)

Usage:
1. Double-click LocalDBViewer to start
2. Click "Open Database" to select a database file
3. Browse tables, view data, and execute SQL queries

Directories:
- data/   - Query history database
- logs/   - Application logs

Version: 1.0.0
""")
        print(f"  Created: {readme_path}")

        print(f"\n  Portable package: {portable_dir}")
        print()

    def run(self, clean: bool = True):
        """Execute full build pipeline."""
        print("=" * 60)
        print("Local DB Viewer - EXE Build")
        print("=" * 60)
        print()

        if not self.pre_check():
            return False

        if clean:
            self.clean_build()

        if not self.build():
            return False

        if not self.post_check():
            return False

        self.create_portable_package()

        print("=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        return True


def main():
    parser = argparse.ArgumentParser(description="Build Local DB Viewer EXE")
    parser.add_argument("--clean", action="store_true", default=True,
                        help="Clean previous build (default: True)")
    parser.add_argument("--no-clean", action="store_true",
                        help="Skip cleaning previous build")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug output")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    builder = EXEBuilder(project_root, debug=args.debug)

    success = builder.run(clean=not args.no_clean)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
