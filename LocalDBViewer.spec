# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Local DB Viewer.

Build command:
    pyinstaller LocalDBViewer.spec --clean --noconfirm
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Resource files
added_files = [
    ('resources/styles', 'resources/styles'),
    ('resources/icons', 'resources/icons'),
]

# Collect PySide6 data
pyside6_data = collect_data_files('PySide6')

# Hidden imports
hidden_imports = collect_submodules('PySide6')
hidden_imports.extend([
    'sqlite3',
])

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=added_files + pyside6_data,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'IPython',
        'pytest',
        'pytest_qt',
        'pytest_cov',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LocalDBViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='resources/icons/app_icon.ico',  # Uncomment when icon is available
)
