#!/usr/bin/env python3
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_dentweb():
    print("=== Dentweb 창 감지 테스트 ===")
    try:
        from src.automation.dentweb_automation import DentwebOCRExtractor
        
        extractor = DentwebOCRExtractor()
        window = extractor.find_dentweb_window()
        
        if window:
            print("Dentweb 창 감지 성공!")
            print(f"제목: {window['title']}")
            print(f"크기: {window['width']}x{window['height']}")
            print(f"강력한 매치: {window.get('is_super_strong', False)}")
            return True
        else:
            print("Dentweb 창을 찾을 수 없습니다")
            return False
            
    except Exception as e:
        print(f"오류: {e}")
        return False

if __name__ == "__main__":
    test_dentweb()
    input("Enter 키를 눌러서 종료하세요...")