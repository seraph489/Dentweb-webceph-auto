# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 현재 디렉토리
current_dir = Path('.').resolve()

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=[
        # 폰트 파일들 포함
        ('public/Pretendard-1.3.9/public/static/*.otf', 'public/Pretendard-1.3.9/public/static/'),
        ('public/Noto_Sans_KR/static/*.ttf', 'public/Noto_Sans_KR/static/'),
    ],
    hiddenimports=[
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.service',
        'webdriver_manager.chrome',
        'cryptography.fernet',
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'requests.adapters',
        'urllib3.util.retry',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'tkinter',
        'test',
        'unittest',
        'doctest',
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
    name='WebCephAuto',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 디버깅을 위해 콘솔 창 표시
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)
