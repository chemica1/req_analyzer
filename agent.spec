# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all_submodules, collect_data_files, copy_metadata
import sys
import os

block_cipher = None

# Collect all necessary bits
datas = []
binaries = []
hiddenimports = [
    'streamlit',
    'langchain_ollama',
    'langchain_community',
    'langchain_core',
    'pdf2image',
    'PIL',
    'chromadb',
    'chromadb.telemetry.product.posthog',
    'posthog',
    'backoff',
    'monotonic',
    'click',
    'regex',
    'tqdm',
    'requests',
    'yaml',
]

# Collect data for streamlit
datas += collect_data_files('streamlit')
datas += collect_data_files('langchain_community')
datas += collect_data_files('chromadb')
datas += copy_metadata('streamlit')
datas += copy_metadata('chromadb')
datas += copy_metadata('tqdm')
datas += copy_metadata('regex')
datas += copy_metadata('requests')
datas += copy_metadata('packaging')
datas += copy_metadata('filelock')
datas += copy_metadata('numpy')
datas += copy_metadata('tokenizers')

# Add local source files
datas += [('src', 'src'), ('config.yaml', '.')]

# Collect submodules
hiddenimports += collect_all_submodules('streamlit')
hiddenimports += collect_all_submodules('langchain_community')
hiddenimports += collect_all_submodules('chromadb')
hiddenimports += collect_all_submodules('pdf2image')
hiddenimports += collect_all_submodules('PIL')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements=None,
)
