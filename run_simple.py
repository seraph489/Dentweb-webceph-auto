#!/usr/bin/env python3
"""
간단한 실행 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉터리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== Web Ceph Auto 간단 실행 테스트 ===")
print(f"Python 버전: {sys.version}")
print(f"작업 디렉터리: {os.getcwd()}")

try:
    from PyQt5.QtWidgets import QApplication
    print("PyQt5 import 성공")
    
    from src.config import config
    print("Config import 성공")
    
    from src.ui.main_window import MainWindow
    print("MainWindow import 성공")
    
    # QApplication 생성
    app = QApplication(sys.argv)
    print("QApplication 생성 성공")
    
    # 메인 윈도우 생성
    print("메인 윈도우 생성 중...")
    main_window = MainWindow()
    print("MainWindow 생성 성공")
    
    # 윈도우 표시
    main_window.show()
    main_window.raise_()
    main_window.activateWindow()
    print("윈도우 표시 완료")
    
    print("\n>>> GUI 창이 열렸습니다. 창을 닫으면 프로그램이 종료됩니다. <<<")
    
    # 이벤트 루프 실행
    sys.exit(app.exec_())
    
except Exception as e:
    import traceback
    print(f"\n오류 발생: {e}")
    print("상세 오류:")
    traceback.print_exc()
    input("Enter 키를 눌러서 종료하세요...")