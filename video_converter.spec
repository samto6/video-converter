# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import tkinterdnd2

# Get tkdnd library path
tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

block_cipher = None

a = Analysis(
    ['video_converter.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include tkdnd2 files
        (tkdnd_path, 'tkinterdnd2/tkdnd'),
        
        # Include FFmpeg binary (Windows)
        ('ffmpeg/ffmpeg.exe', '.'),
    ],
    # More specific hidden imports
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinterdnd2',
    ],
    # Exclude unnecessary modules
    excludes=[
        '_gtkagg',
        '_tkagg', 
        'bsddb',
        'curses',
        'matplotlib',
        'numpy',
        'pandas',
        'pywin.debugger',
        'pywin.debugger.dbgcon',
        'pywin.dialogs',
        'scipy',
        'tcl',
        'Tkconstants',
        'tensorflow',
        'torch',
        'wx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    # Collect only specific submodules
    collect_submodules=['tkinter', 'PIL.Image', 'PIL.ImageTk'],
)

# Enable better compression
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
    compress=True
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols from binary (reduces size)
    upx=True,    # Enable UPX compression
    upx_exclude=[
        'vcruntime140.dll',  # Exclude problematic files from UPX compression
        'python*.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)