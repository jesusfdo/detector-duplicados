# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para Detector de Duplicados."""

a = Analysis(
    ['src/detector_duplicados/cli.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'detector_duplicados',
        'detector_duplicados.cli',
        'detector_duplicados.config',
        'detector_duplicados.db',
        'detector_duplicados.duper',
        'detector_duplicados.html_report',
        'detector_duplicados.scanner',
        'detector_duplicados.ui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DetectorDeDuplicados',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
