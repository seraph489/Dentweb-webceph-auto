#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Ceph Auto Processor 빌드 스크립트
PyInstaller를 사용하여 EXE 파일 생성
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_requirements():
    """필수 요구사항 확인"""
    print("🔍 필수 요구사항을 확인합니다...")
    
    # Python 버전 확인
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 이상이 필요합니다")
        return False
    
    # PyInstaller 확인
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} 발견")
    except ImportError:
        print("❌ PyInstaller가 설치되지 않았습니다")
        print("   pip install pyinstaller 명령으로 설치해주세요")
        return False
    
    # 필수 패키지 확인
    required_packages = {
        'PyQt5': 'PyQt5',
        'selenium': 'selenium', 
        'requests': 'requests', 
        'cryptography': 'cryptography',
        'opencv-python': 'cv2', 
        'pillow': 'PIL', 
        'webdriver-manager': 'webdriver_manager'
    }
    
    missing_packages = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} 확인")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} 누락")
    
    if missing_packages:
        print(f"\n다음 패키지를 설치해주세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def clean_build_dirs():
    """빌드 디렉토리 정리"""
    print("\n🧹 이전 빌드 파일을 정리합니다...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   제거됨: {dir_name}/")
    
    # .spec 파일도 제거
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"   제거됨: {spec_file}")

def create_pyinstaller_spec():
    """PyInstaller spec 파일 생성"""
    print("\n📝 PyInstaller 설정 파일을 생성합니다...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

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
    console=False,  # 콘솔 창 숨김
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)
'''
    
    with open('webcephauto.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("   ✅ webcephauto.spec 파일이 생성되었습니다")

def create_version_info():
    """버전 정보 파일 생성"""
    print("\n📋 버전 정보 파일을 생성합니다...")
    
    version_info = '''# UTF-8
#
# 버전 정보 (Windows 실행 파일용)
#

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Web Ceph Auto Team'),
        StringStruct(u'FileDescription', u'치과 영상 분석 자동화 프로그램'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'WebCephAuto'),
        StringStruct(u'LegalCopyright', u'Copyright © 2024 Web Ceph Auto Team'),
        StringStruct(u'OriginalFilename', u'WebCephAuto.exe'),
        StringStruct(u'ProductName', u'Web Ceph Auto Processor'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print("   ✅ version_info.txt 파일이 생성되었습니다")

def create_icon():
    """기본 아이콘 생성 (선택사항)"""
    print("\n🎨 아이콘 파일을 확인합니다...")
    
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    icon_path = assets_dir / 'icon.ico'
    if not icon_path.exists():
        print("   ⚠️  아이콘 파일이 없습니다. 기본 아이콘을 사용합니다.")
        print("   💡 assets/icon.ico 파일을 추가하면 사용자 정의 아이콘을 사용할 수 있습니다.")
    else:
        print("   ✅ 사용자 정의 아이콘을 발견했습니다")

def build_executable():
    """실행 파일 빌드"""
    print("\n🔨 실행 파일을 빌드합니다...")
    print("   이 과정은 몇 분이 소요될 수 있습니다...")
    
    try:
        # PyInstaller 실행
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'webcephauto.spec'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("   ✅ 빌드가 성공적으로 완료되었습니다!")
            
            # 결과 확인
            exe_path = Path('dist/WebCephAuto.exe')
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"   📦 생성된 파일: {exe_path} ({size_mb:.1f} MB)")
                return True
            else:
                print("   ❌ 실행 파일이 생성되지 않았습니다")
                return False
        else:
            print("   ❌ 빌드 중 오류가 발생했습니다:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"   ❌ 빌드 실패: {str(e)}")
        return False

def create_installer_script():
    """설치 스크립트 생성 (Inno Setup용)"""
    print("\n📦 설치 스크립트를 생성합니다...")
    
    installer_script = '''[Setup]
AppName=Web Ceph Auto Processor
AppVersion=1.0.0
AppPublisher=Web Ceph Auto Team
AppPublisherURL=https://github.com/webcephauto
DefaultDirName={autopf}\\WebCephAuto
DefaultGroupName=Web Ceph Auto
UninstallDisplayIcon={app}\\WebCephAuto.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=WebCephAuto_Setup_v1.0.0

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 아이콘 만들기"; GroupDescription: "추가 아이콘:"; Flags: unchecked

[Files]
Source: "dist\\WebCephAuto.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\Web Ceph Auto"; Filename: "{app}\\WebCephAuto.exe"
Name: "{group}\\제거"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\Web Ceph Auto"; Filename: "{app}\\WebCephAuto.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\\WebCephAuto.exe"; Description: "프로그램 실행"; Flags: nowait postinstall skipifsilent
'''
    
    with open('installer_setup.iss', 'w', encoding='utf-8') as f:
        f.write(installer_script)
    
    print("   ✅ installer_setup.iss 파일이 생성되었습니다")
    print("   💡 Inno Setup을 사용하여 설치 프로그램을 만들 수 있습니다")

def main():
    """메인 빌드 프로세스"""
    print("🚀 Web Ceph Auto Processor 빌드를 시작합니다\n")
    
    # 1. 요구사항 확인
    if not check_requirements():
        print("\n❌ 빌드를 중단합니다")
        return 1
    
    # 2. 이전 빌드 정리
    clean_build_dirs()
    
    # 3. 빌드 파일들 생성
    create_version_info()
    create_icon()
    create_pyinstaller_spec()
    
    # 4. 실행 파일 빌드
    if not build_executable():
        print("\n❌ 빌드가 실패했습니다")
        return 1
    
    # 5. 설치 스크립트 생성
    create_installer_script()
    
    print("\n🎉 빌드가 완료되었습니다!")
    print("\n📁 결과 파일:")
    print("   - dist/WebCephAuto.exe (실행 파일)")
    print("   - installer_setup.iss (설치 프로그램 스크립트)")
    
    print("\n📝 다음 단계:")
    print("   1. dist/WebCephAuto.exe를 테스트해보세요")
    print("   2. Inno Setup으로 installer_setup.iss를 컴파일하여 설치 프로그램을 만드세요")
    print("   3. 배포 전에 다양한 환경에서 테스트하세요")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        print("\n✨ 빌드 성공!")
    else:
        print("\n💥 빌드 실패!")
    
    # Windows에서 일시 정지
    if sys.platform == "win32":
        input("\nPress Enter to exit...")
    
    sys.exit(exit_code) 