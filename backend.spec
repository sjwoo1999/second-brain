# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Second Brain Backend."""

import os
from pathlib import Path

block_cipher = None
base_dir = Path(SPECPATH)

a = Analysis(
    ['backend_main.py'],
    pathex=[str(base_dir)],
    binaries=[],
    datas=[
        # 설정 파일들
        ('config', 'config'),
        ('interfaces', 'interfaces'),
        ('core', 'core'),
        ('tools', 'tools'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'httptools',
        'websockets',
        'pydantic',
        'fastapi',
        'starlette',
        'anyio',
        'sniffio',
        'httpx',
        'anthropic',
        'dotenv',
    ],
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
    name='python-backend-x86_64-pc-windows-msvc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 콘솔 출력 보이게
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
