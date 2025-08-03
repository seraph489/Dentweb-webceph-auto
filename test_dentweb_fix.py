#!/usr/bin/env python3
"""
Dentweb 창 상태 강제 복원 테스트
"""

import sys
from pathlib import Path
import win32gui
import time

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def force_restore_dentweb():
    """Dentweb 창 강제 복원 및 활성화"""
    try:
        from src.automation.dentweb_automation import DentwebOCRExtractor
        
        extractor = DentwebOCRExtractor()
        window = extractor.find_dentweb_window()
        
        if not window:
            print("Dentweb 창을 찾을 수 없습니다")
            return False
            
        hwnd = window['hwnd']
        print(f"찾은 창: {window['title']}")
        print(f"현재 위치: {window['rect']}")
        
        # 1. 다양한 복원 방법 시도
        restore_methods = [
            (9, "SW_RESTORE"),      # 복원
            (1, "SW_SHOWNORMAL"),   # 일반 표시
            (5, "SW_SHOW"),         # 표시
            (4, "SW_SHOWNOACTIVATE"), # 비활성 표시
            (3, "SW_SHOWMAXIMIZED") # 최대화
        ]
        
        for method_code, method_name in restore_methods:
            print(f"\n{method_name} 시도...")
            try:
                win32gui.ShowWindow(hwnd, method_code)
                time.sleep(0.5)
                
                # 결과 확인
                new_rect = win32gui.GetWindowRect(hwnd)
                new_width = new_rect[2] - new_rect[0]
                new_height = new_rect[3] - new_rect[1]
                
                print(f"결과: {new_width}x{new_height}, 위치: {new_rect}")
                
                # 성공적으로 복원되었는지 확인
                if new_rect[0] > -30000 and new_rect[1] > -30000 and new_width > 500:
                    print(f"✓ {method_name}으로 성공적으로 복원됨!")
                    
                    # 최전면으로 이동
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.3)
                    return True
                    
            except Exception as e:
                print(f"❌ {method_name} 실패: {e}")
        
        print("❌ 모든 복원 방법 실패")
        return False
        
    except Exception as e:
        print(f"오류: {e}")
        return False

def main():
    print("=== Dentweb 창 강제 복원 테스트 ===")
    
    success = force_restore_dentweb()
    
    if success:
        print("\n🎉 Dentweb 창이 성공적으로 복원되었습니다!")
        print("이제 자동화가 정상적으로 작동할 것입니다.")
    else:
        print("\n⚠ Dentweb 창 복원에 실패했습니다.")
        print("Dentweb 프로그램을 수동으로 열고 최대화해주세요.")
    
    input("\nEnter 키를 눌러서 종료하세요...")

if __name__ == "__main__":
    main()