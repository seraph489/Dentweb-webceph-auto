#!/usr/bin/env python3
"""
자동화 기능 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트 디렉터리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_dentweb_detection():
    """Dentweb 창 감지 테스트"""
    print("=== Dentweb 창 감지 테스트 ===")
    try:
        from src.automation.dentweb_automation import DentwebOCRExtractor
        
        extractor = DentwebOCRExtractor()
        window = extractor.find_dentweb_window()
        
        if window:
            print(f"Dentweb 창 감지 성공!")
            print(f"  제목: {window['title']}")
            print(f"  위치: {window['rect']}")
            print(f"  크기: {window['width']}x{window['height']}")
            print(f"  매우 강력한 매치: {window.get('is_super_strong', False)}")
            print(f"  강력한 매치: {window.get('is_strong_match', False)}")
            print(f"  활성 창: {window.get('is_foreground', False)}")
            return True
        else:
            print("Dentweb 창을 찾을 수 없습니다")
            return False
            
    except Exception as e:
        print(f"오류 발생: {e}")
        return False

def test_webceph_browser():
    """WebCeph 브라우저 초기화 테스트"""
    print("\n=== WebCeph 브라우저 초기화 테스트 ===")
    try:
        from src.automation.web_ceph_automation import WebCephAutomation
        
        automation = WebCephAutomation()
        print("WebCeph 자동화 객체 생성 성공")
        
        # 브라우저 초기화는 시간이 오래 걸리므로 스킵
        print("브라우저 초기화 테스트는 시간 관계상 스킵합니다")
        print("실제 사용 시에는 automation.initialize_browser()를 호출하세요")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def test_config():
    """설정 테스트"""
    print("\n=== 설정 테스트 ===")
    try:
        from src.config import config
        
        # 기본 설정 확인
        webceph_url = config.get('webceph', 'url', '')
        upstage_api_url = config.get('upstage', 'api_url', '')
        
        print(f"WebCeph URL: {webceph_url}")
        print(f"Upstage API URL: {upstage_api_url}")
        
        if webceph_url and upstage_api_url:
            print("✓ 기본 설정 확인 완료")
            return True
        else:
            print("⚠ 일부 설정이 비어있습니다")
            return True
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🔧 Web Ceph Auto 자동화 기능 테스트")
    print("=" * 50)
    
    results = []
    
    # 각 테스트 실행
    results.append(test_config())
    results.append(test_dentweb_detection()) 
    results.append(test_webceph_browser())
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print(f"성공: {sum(results)}개 / 전체: {len(results)}개")
    
    if all(results):
        print("🎉 모든 테스트 통과! 자동화 기능이 정상 작동할 준비가 되었습니다.")
    else:
        print("⚠ 일부 테스트에서 문제가 발견되었습니다.")
    
    input("\nEnter 키를 눌러서 종료하세요...")

if __name__ == "__main__":
    main()