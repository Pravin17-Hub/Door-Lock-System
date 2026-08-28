# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification Script for FaceSecure Desktop Application
Builds a single-folder or standalone Windows executable bundling assets, database, and UI modules.
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect custom assets, data folders, and database templates
datas = [
    ('assets', 'assets'),
    ('data', 'data'),
    ('database', 'database'),
]

hiddenimports = [
    'customtkinter',
    'cv2',
    'PIL',
    'serial',
    'serial.tools.list_ports',
    'sqlite3',
    'pickle',
    'json',
    'logging',
    'csv',
]

# Add face_recognition if available
try:
    import face_recognition
    hiddenimports.extend(collect_submodules('face_recognition'))
    datas.extend(collect_data_files('face_recognition'))
except ImportError:
    pass

a = Analysis(
    ['../main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FaceSecure',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # GUI application without CMD prompt window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/logo.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FaceSecure',
)
