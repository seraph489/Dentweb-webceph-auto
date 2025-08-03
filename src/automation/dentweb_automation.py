"""
Dentweb 자동화 모듈
스크린샷 촬영 및 Upstage OCR을 사용한 환자 정보 추출
"""

import os
import io
import base64
import requests
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image, ImageGrab
import mss
import win32gui
from PyQt5.QtCore import QThread, pyqtSignal

from ..config import config

class DentwebOCRExtractor:
    """Dentweb 스크린샷 및 OCR 추출 클래스"""
    
    def __init__(self):
        self.api_key = config.get_upstage_api_key()
        self.api_url = config.get('upstage', 'api_url', 'https://api.upstage.ai/v1/document-ai/ocr')
    
    def find_dentweb_window(self) -> Optional[Dict]:
        """Dentweb 프로그램 창 찾기 (최소화 창 포함 강화 버전)"""
        try:
            dentweb_windows = []
            
            print("모든 창을 스캔하여 덴트웹 프로그램을 찾습니다...")
            
            def enum_windows_callback(hwnd, windows):
                try:
                    # 모든 창을 검사 (최소화 상태 무관)
                    window_title = win32gui.GetWindowText(hwnd)
                    if not window_title:
                        return True  # 제목이 없는 창은 건너뛰기
                    
                    # 창 클래스 이름도 확인 (더 정확한 식별)
                    try:
                        class_name = win32gui.GetClassName(hwnd)
                    except:
                        class_name = ""
                    
                    print(f"창 스캔: '{window_title}' (클래스: {class_name})")
                    
                    # 1. 매우 강력한 패턴: Chart No.와 이름이 포함된 덴트웹 창
                    super_strong_patterns = [
                        ('▶ 덴트웹', 'Chart No.', '이름'),
                        ('덴트웹 ::', 'Chart No.', '이름'),
                    ]
                    is_super_strong = False
                    for prefix, keyword1, keyword2 in super_strong_patterns:
                        if (window_title.startswith(prefix) and 
                            keyword1 in window_title and keyword2 in window_title):
                            is_super_strong = True
                            break
                    
                    # 2. 강력한 패턴: "▶ 덴트웹" 또는 "덴트웹 ::"로 시작
                    strong_patterns = ['▶ 덴트웹', '덴트웹 ::']
                    is_strong_match = any(window_title.startswith(pattern) for pattern in strong_patterns)
                    
                    # 3. 일반 패턴
                    dentweb_patterns = [
                        'dentweb', 'dentWeb', 'DentWeb', 'DENTWEB',
                        '덴트웹', '덴트 웹', '치과관리', '치과 관리',
                        'dental', 'Dental', 'DENTAL'
                    ]
                    is_general_match = any(pattern.lower() in window_title.lower() for pattern in dentweb_patterns)
                    
                    if is_super_strong or is_strong_match or is_general_match:
                        try:
                            # 창 위치와 크기 가져오기
                            rect = win32gui.GetWindowRect(hwnd)
                            
                            # 창 상태 확인 (더 정확한 최소화 감지)
                            is_minimized = (rect[0] < -30000 or rect[1] < -30000 or 
                                          (rect[2] - rect[0] <= 0) or (rect[3] - rect[1] <= 0))
                            is_foreground = win32gui.GetForegroundWindow() == hwnd
                            is_visible_area = (rect[2] - rect[0] > 100) and (rect[3] - rect[1] > 100)
                            
                            # 추가로 Windows API로 최소화 상태 확인
                            try:
                                import win32con
                                placement = win32gui.GetWindowPlacement(hwnd)
                                is_actually_minimized = (placement[1] == win32con.SW_SHOWMINIMIZED)
                                if is_actually_minimized:
                                    is_minimized = True
                                    print(f"Windows API로 최소화 확인: {window_title}")
                            except:
                                pass
                            
                            # 창이 숨겨져 있거나 보이지 않는 상태인지 확인
                            is_window_visible = win32gui.IsWindowVisible(hwnd)
                            is_window_enabled = win32gui.IsWindowEnabled(hwnd)
                            
                            print(f"창 상태 상세: 최소화={is_minimized}, 보임={is_window_visible}, 활성={is_window_enabled}")
                            
                            # 최소화되었거나 보이지 않는 창 복원 시도 (더욱 강화된 버전)
                            if is_minimized or not is_window_visible or (rect[2] - rect[0] <= 0):
                                print(f"숨겨진/최소화된 창 발견 (강력한 복원 시도): {window_title}")
                                try:
                                    import time
                                    
                                    # 1단계: 기본 복원 시퀀스
                                    print("1단계: 기본 복원...")
                                    win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                                    time.sleep(0.3)
                                    
                                    # 2단계: 강제 표시
                                    print("2단계: 강제 표시...")
                                    win32gui.ShowWindow(hwnd, 5)  # SW_SHOW
                                    time.sleep(0.2)
                                    
                                    # 3단계: 일반 창으로 표시
                                    print("3단계: 일반 창으로 표시...")
                                    win32gui.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL
                                    time.sleep(0.3)
                                    
                                    # 4단계: 최전면으로 이동
                                    print("4단계: 최전면으로 이동...")
                                    try:
                                        win32gui.SetForegroundWindow(hwnd)
                                        win32gui.BringWindowToTop(hwnd)
                                        # 추가: 활성 창으로 설정
                                        win32gui.SetActiveWindow(hwnd)
                                    except Exception as fg_error:
                                        print(f"최전면 이동 실패: {fg_error}")
                                    
                                    time.sleep(0.5)
                                    
                                    # 5단계: 복원 결과 확인
                                    rect_after = win32gui.GetWindowRect(hwnd)
                                    print(f"복원 후 위치: {rect_after}")
                                    
                                    # 여전히 복원되지 않은 경우 최대화 시도
                                    if rect_after[0] < -30000 or rect_after[1] < -30000 or (rect_after[2] - rect_after[0] <= 0):
                                        print("5단계: 최대화로 강제 복원...")
                                        win32gui.ShowWindow(hwnd, 3)  # SW_SHOWMAXIMIZED
                                        time.sleep(0.5)
                                        rect_after = win32gui.GetWindowRect(hwnd)
                                        print(f"최대화 후 위치: {rect_after}")
                                    
                                    rect = rect_after
                                    is_minimized = False
                                    print(f"창 복원 완료: {rect}")
                                        
                                except Exception as e:
                                    print(f"창 복원 중 오류: {e}")
                                    # 복원 실패해도 창 정보는 저장 (나중에 재시도 가능)
                                    pass
                            
                            # 창 정보 저장
                            window_info = {
                                'hwnd': hwnd,
                                'title': window_title,
                                'rect': rect,
                                'width': rect[2] - rect[0],
                                'height': rect[3] - rect[1],
                                'is_super_strong': is_super_strong,
                                'is_strong_match': is_strong_match,
                                'is_foreground': is_foreground,
                                'is_minimized': is_minimized,
                                'is_visible_area': is_visible_area,
                                'area': (rect[2] - rect[0]) * (rect[3] - rect[1])
                            }
                            windows.append(window_info)
                            print(f"Dentweb 창 발견: {window_title}")
                            print(f"  위치: {rect}, 활성: {is_foreground}, 최소화: {is_minimized}")
                                
                        except Exception as e:
                            print(f"창 정보 가져오기 실패: {e}")
                except Exception as callback_error:
                    print(f"창 콜백 처리 중 오류: {callback_error}")
                return True
            
            win32gui.EnumWindows(enum_windows_callback, dentweb_windows)
            
            if dentweb_windows:
                print(f"총 {len(dentweb_windows)}개의 덴트웹 관련 창 발견")
                
                # 우선순위 기반 선택
                # 1순위: 매우 강력한 패턴 (Chart No. + 이름 포함)
                super_strong_matches = [w for w in dentweb_windows if w.get('is_super_strong', False)]
                if super_strong_matches:
                    # 활성 창 우선, 없으면 가장 큰 창
                    foreground_matches = [w for w in super_strong_matches if w.get('is_foreground', False)]
                    if foreground_matches:
                        selected_window = max(foreground_matches, key=lambda w: w['area'])
                    else:
                        selected_window = max(super_strong_matches, key=lambda w: w['area'])
                    print(f"매우 강력한 패턴으로 선택: {selected_window['title']}")
                    
                    # 선택된 창 최종 복원 확인
                    self._ensure_window_restored(selected_window)
                    return selected_window
                
                # 2순위: 강력한 패턴
                strong_matches = [w for w in dentweb_windows if w.get('is_strong_match', False)]
                if strong_matches:
                    # 활성 창 우선, 없으면 가장 큰 창
                    foreground_matches = [w for w in strong_matches if w.get('is_foreground', False)]
                    if foreground_matches:
                        selected_window = max(foreground_matches, key=lambda w: w['area'])
                    else:
                        selected_window = max(strong_matches, key=lambda w: w['area'])
                    print(f"강력한 패턴으로 선택: {selected_window['title']}")
                    
                    # 선택된 창 최종 복원 확인
                    self._ensure_window_restored(selected_window)
                    return selected_window
                
                # 3순위: 가장 큰 창
                visible_windows = [w for w in dentweb_windows if w.get('is_visible_area', True)]
                if visible_windows:
                    selected_window = max(visible_windows, key=lambda w: w['area'])
                    print(f"가장 큰 창으로 선택: {selected_window['title']}")
                    
                    # 선택된 창 최종 복원 확인
                    self._ensure_window_restored(selected_window)
                    return selected_window
                
                # 마지막: 아무거나
                selected_window = dentweb_windows[0]
                print(f"첫 번째 창으로 선택: {selected_window['title']}")
                
                # 선택된 창 최종 복원 확인
                self._ensure_window_restored(selected_window)
                return selected_window
                
            else:
                print("Dentweb 창을 찾을 수 없습니다")
                return None
                
        except Exception as e:
            print(f"Dentweb 창 찾기 오류: {e}")
            return None
    
    def _ensure_window_restored(self, window_info: Dict):
        """선택된 창이 확실히 복원되었는지 최종 확인 및 복원"""
        try:
            hwnd = window_info['hwnd']
            window_title = window_info['title']
            
            print(f"최종 창 복원 확인: {window_title}")
            
            # 현재 창 상태 확인
            current_rect = win32gui.GetWindowRect(hwnd)
            is_visible = win32gui.IsWindowVisible(hwnd)
            
            print(f"최종 확인 - 위치: {current_rect}, 보임: {is_visible}")
            
            # 여전히 최소화되어 있거나 보이지 않는 경우
            if (current_rect[0] < -30000 or current_rect[1] < -30000 or 
                current_rect[2] - current_rect[0] <= 0 or not is_visible):
                
                print("창이 여전히 숨겨져 있음 - 최종 복원 시도...")
                
                import time
                
                # 최종 복원 시퀀스 (가장 강력한 방법)
                try:
                    # 1. 강제 활성화
                    win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                    time.sleep(0.2)
                    
                    # 2. 표시 강제
                    win32gui.ShowWindow(hwnd, 5)  # SW_SHOW
                    time.sleep(0.2)
                    
                    # 3. 일반 창으로
                    win32gui.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL
                    time.sleep(0.3)
                    
                    # 4. 최대화 (확실한 복원을 위해)
                    win32gui.ShowWindow(hwnd, 3)  # SW_SHOWMAXIMIZED
                    time.sleep(0.3)
                    
                    # 5. 최전면 이동
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.BringWindowToTop(hwnd)
                    
                    # 6. 최종 확인
                    final_rect = win32gui.GetWindowRect(hwnd)
                    final_visible = win32gui.IsWindowVisible(hwnd)
                    
                    print(f"최종 복원 결과 - 위치: {final_rect}, 보임: {final_visible}")
                    
                    # 창 정보 업데이트
                    window_info['rect'] = final_rect
                    window_info['is_minimized'] = False
                    
                except Exception as restore_error:
                    print(f"최종 복원 실패: {restore_error}")
            else:
                print("창이 이미 올바르게 복원되어 있습니다")
                
        except Exception as e:
            print(f"최종 창 복원 확인 중 오류: {e}")
    
    def capture_dentweb_screenshot(self, x: int = None, y: int = None, 
                                 width: int = None, height: int = None) -> Optional[Image.Image]:
        """
        Dentweb 화면의 지정된 영역을 스크린샷으로 촬영
        먼저 Dentweb 창을 자동으로 찾고, 실패 시 설정된 좌표 사용
        """
        try:
            # 1. 먼저 Dentweb 창 자동 인식 시도
            dentweb_window = self.find_dentweb_window()
            
            if dentweb_window:
                # Dentweb 창이 발견된 경우, 창 기준 좌측 상단에서 적절한 크기 캡처
                rect = dentweb_window['rect']
                
                # 창 상태 최적화 및 활성화
                try:
                    import time
                    hwnd = dentweb_window['hwnd']
                    
                    print(f"창 상태 최적화 시작 - 현재 크기: {rect}")
                    
                    # 1단계: 최소화 해제
                    win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                    time.sleep(0.3)
                    
                    # 2단계: 창 크기 확인 및 조정
                    current_rect = win32gui.GetWindowRect(hwnd)
                    current_width = current_rect[2] - current_rect[0]
                    current_height = current_rect[3] - current_rect[1]
                    
                    print(f"복원 후 크기: {current_width}x{current_height}")
                    
                    # 창이 너무 작거나 위치가 이상하면 최대화 시도
                    if (current_width < 1000 or current_height < 700 or 
                        current_rect[0] < -100 or current_rect[1] < -100):
                        print("창 크기가 부적절함 - 최대화 시도")
                        win32gui.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                        time.sleep(0.5)
                    else:
                        # 적절한 크기라면 화면에 보이도록 조정
                        print("창 크기 적절함 - 표시 상태로 전환")
                        win32gui.ShowWindow(hwnd, 5)  # SW_SHOW
                        time.sleep(0.3)
                    
                    # 3단계: 최전면으로 이동
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.3)
                    
                    # 4단계: 최종 위치 확인
                    final_rect = win32gui.GetWindowRect(hwnd)
                    final_width = final_rect[2] - final_rect[0]
                    final_height = final_rect[3] - final_rect[1]
                    
                    print(f"최종 창 상태: {final_width}x{final_height}, 위치: {final_rect}")
                    
                    # 여전히 문제가 있으면 강력한 복원 시도
                    if (final_width < 800 or final_height < 600 or 
                        final_rect[0] < -30000 or final_rect[1] < -30000):
                        print("강력한 창 복원 시도")
                        
                        # 1. 강제 일반 상태로 복원
                        win32gui.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL
                        time.sleep(0.3)
                        
                        # 2. 창 위치 강제 조정 (화면 중앙으로)
                        try:
                            import win32api
                            screen_width = win32api.GetSystemMetrics(0)
                            screen_height = win32api.GetSystemMetrics(1)
                            
                            # 화면 중앙에 적당한 크기로 배치
                            new_width = min(1200, int(screen_width * 0.8))
                            new_height = min(800, int(screen_height * 0.8))
                            new_x = (screen_width - new_width) // 2
                            new_y = (screen_height - new_height) // 2
                            
                            # 창 위치와 크기 강제 설정
                            win32gui.SetWindowPos(hwnd, 0, new_x, new_y, new_width, new_height, 0x0040)
                            time.sleep(0.5)
                            
                            print(f"창 위치 강제 조정: ({new_x}, {new_y}) - {new_width}x{new_height}")
                            
                        except Exception as pos_error:
                            print(f"창 위치 조정 실패: {pos_error}")
                            # 마지막 수단으로 최대화
                            win32gui.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                            time.sleep(0.5)
                        
                        # 최종 확인
                        final_rect = win32gui.GetWindowRect(hwnd)
                        print(f"강력한 복원 후: {final_rect}")
                    
                    rect = final_rect
                    
                except Exception as e:
                    print(f"창 최적화 실패: {e}")
                    print("기본 설정으로 진행합니다")
                
                # 캡처 영역 설정 (최대화시 (0,0)에서 670*470 영역만 캡처)
                window_width = rect[2] - rect[0]
                window_height = rect[3] - rect[1]
                
                print(f"창 전체 크기: {window_width}x{window_height}")
                print(f"창 위치: ({rect[0]}, {rect[1]}) - ({rect[2]}, {rect[3]})")
                
                # 화면 크기 가져오기
                import win32api
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                print(f"화면 크기: {screen_width}x{screen_height}")
                
                # 창이 최대화된 상태인지 확인 (더 정확한 판별)
                is_maximized = (
                    window_width >= screen_width * 0.95 and 
                    window_height >= screen_height * 0.95 and
                    rect[0] <= 10 and rect[1] <= 10  # 창이 화면 좌상단 근처에 있는지 확인
                )
                
                print(f"최대화 상태 판별: {is_maximized}")
                
                if is_maximized:
                    # 최대화된 경우: 절대 화면 좌표 (0,0) 기준으로 670*470 영역만 캡처
                    x = 0
                    y = 0
                    width = 670
                    height = 470
                    print(f"최대화 감지: 절대 화면 좌표 (0,0) 기준으로 670×470 영역 캡처")
                else:
                    # 최대화되지 않은 경우: 창 기준 상대 좌표로 캡처
                    if window_width >= 800 and window_height >= 600:
                        # 중간 크기 창: 대부분 영역 캡처
                        width = window_width - 50
                        height = window_height - 100
                        x = rect[0] + 25
                        y = rect[1] + 50
                    else:
                        # 작은 창: 전체 캡처 (타이틀바만 제외)
                        width = window_width
                        height = max(window_height - 40, window_height)
                        x = rect[0]
                        y = rect[1] + 30 if window_height > 100 else rect[1]
                    
                    # 최소 크기 보장
                    width = max(width, 400)
                    height = max(height, 300)
                    
                    # 화면 경계 초과 방지
                    if x + width > screen_width:
                        width = screen_width - x
                    if y + height > screen_height:
                        height = screen_height - y
                    
                    print(f"일반 창 모드: 창 기준 상대 좌표로 캡처")
                
                print(f"최종 캡처 영역: ({x}, {y}) - {width}×{height}")
                if is_maximized:
                    print(f"캡처 모드: 절대 화면 좌표 (0,0) 기준")
                else:
                    print(f"캡처 영역 비율: {width/window_width:.1%} x {height/window_height:.1%}")
                    print(f"캡처 모드: 창 기준 상대 좌표")
            else:
                # 2. Dentweb 창을 찾지 못한 경우 (0,0,800,600) 기본값 사용
                if x is None:
                    x = 0
                if y is None:
                    y = 0
                if width is None:
                    width = 800
                if height is None:
                    height = 600
                print(f"설정값으로 캡처: ({x}, {y}) - {width}×{height}")
            # MSS를 사용한 스크린샷 촬영
            with mss.mss() as sct:
                monitor = {
                    "top": y,
                    "left": x,
                    "width": width,
                    "height": height
                }
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                screenshots_dir = Path.home() / "AppData" / "Local" / "WebCephAuto" / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = screenshots_dir / f"dentweb_screenshot_{timestamp}.png"
                img.save(screenshot_path)
                print(f"스크린샷 저장됨: {screenshot_path}")
                return img
        except Exception as e:
            print(f"스크린샷 촬영 오류: {e}")
            return None
    
    def extract_text_with_upstage_ocr(self, image: Image.Image) -> Optional[str]:
        """
        Upstage OCR API를 사용하여 이미지에서 텍스트 추출
        공식 문서: https://api.upstage.ai/v1/document-digitization
        
        Args:
            image: PIL Image 객체
            
        Returns:
            추출된 텍스트 또는 None
        """
        try:
            if not self.api_key:
                raise Exception("Upstage API 키가 설정되지 않았습니다")
            
            print(f"OCR API 호출 시작 - URL: {self.api_url}")
            
            # 이미지 전처리 (OCR 정확도 향상)
            processed_image = self._preprocess_image_for_ocr(image)
            
            # 임시 파일로 이미지 저장
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                processed_image.save(temp_file.name, format='PNG', dpi=(300, 300))
                temp_filename = temp_file.name
            
            try:
                # API 요청 헤더 (공식 문서에 따른 Bearer 토큰 방식)
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                # multipart/form-data로 파일 전송 (공식 문서 방식)
                with open(temp_filename, "rb") as f:
                    files = {"document": f}
                    data = {"model": "ocr"}
                    
                    print("Upstage OCR API 요청 전송 중...")
                    
                    # API 호출
                    response = requests.post(
                        self.api_url,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=30
                    )
                
                print(f"API 응답 상태 코드: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"OCR API 성공 응답: {result}")
                    
                    # 응답에서 텍스트 추출 (공식 응답 구조에 맞춤)
                    extracted_text = self._extract_text_from_response(result)
                    if extracted_text:
                        print(f"추출된 텍스트 길이: {len(extracted_text)} 문자")
                        return extracted_text
                    else:
                        print("응답에서 텍스트를 찾을 수 없습니다")
                        return None
                        
                elif response.status_code == 401:
                    raise Exception("API 키가 올바르지 않습니다. 설정을 확인해주세요.")
                elif response.status_code == 429:
                    raise Exception("API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
                else:
                    error_msg = f"OCR API 오류 (코드: {response.status_code})"
                    try:
                        error_detail = response.json()
                        error_msg += f" - {error_detail}"
                    except:
                        error_msg += f" - {response.text}"
                    print(error_msg)
                    raise Exception(error_msg)
                    
            finally:
                # 임시 파일 정리
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                
        except Exception as e:
            print(f"OCR 처리 오류: {e}")
            return None
    
    def _extract_text_from_response(self, response_data: dict) -> Optional[str]:
        """
        Upstage API 응답에서 텍스트 추출 (개선된 버전)
        
        Args:
            response_data: API 응답 JSON 데이터
            
        Returns:
            추출된 텍스트 또는 None
        """
        try:
            # 다양한 응답 구조에 대응
            extracted_texts = []
            
            # 1. 직접 'text' 필드가 있는 경우
            if 'text' in response_data:
                extracted_texts.append(response_data['text'])
            
            # 2. 'pages' 구조인 경우
            if 'pages' in response_data:
                for page in response_data['pages']:
                    if 'text' in page:
                        extracted_texts.append(page['text'])
                    # elements가 있는 경우
                    if 'elements' in page:
                        for element in page['elements']:
                            if 'text' in element:
                                extracted_texts.append(element['text'])
            
            # 3. 직접 'elements' 구조인 경우  
            if 'elements' in response_data:
                for element in response_data['elements']:
                    if 'text' in element:
                        extracted_texts.append(element['text'])
            
            # 4. 'content' 구조인 경우 (일부 API 버전)
            if 'content' in response_data:
                content = response_data['content']
                if isinstance(content, str):
                    extracted_texts.append(content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, str):
                            extracted_texts.append(item)
                        elif isinstance(item, dict) and 'text' in item:
                            extracted_texts.append(item['text'])
            
            # 텍스트 조합
            if extracted_texts:
                combined_text = '\n'.join(extracted_texts).strip()
                return combined_text if combined_text else None
            
            return None
            
        except Exception as e:
            print(f"응답 텍스트 추출 오류: {e}")
            return None
    
    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        OCR 정확도 향상을 위한 이미지 전처리
        
        Args:
            image: 원본 PIL Image
            
        Returns:
            전처리된 PIL Image
        """
        try:
            # RGB 모드로 변환
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 이미지 크기가 너무 작으면 확대 (최소 800x600)
            width, height = image.size
            if width < 800 or height < 600:
                scale_factor = max(800/width, 600/height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"이미지 크기 조정: {width}x{height} -> {new_width}x{new_height}")
            
            # 대비 및 선명도 향상
            from PIL import ImageEnhance
            
            # 대비 향상
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # 선명도 향상
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            return image
            
        except Exception as e:
            print(f"이미지 전처리 오류: {e}")
            return image  # 오류 시 원본 반환
    
    def parse_patient_info(self, ocr_text: str) -> Dict[str, str]:
        """
        OCR로 추출된 텍스트에서 환자 정보를 파싱
        Args:
            ocr_text: OCR로 추출된 텍스트
        Returns:
            환자 정보 딕셔너리
        """
        patient_info = {
            'chart_no': '',
            'last_name': '',
            'first_name': '',
            'birth_date': '',
            'phone': '',
            'address': '',
            'gender': '',
            'capture_date': datetime.now().strftime('%Y-%m-%d')
        }
        try:
            print(f"OCR 텍스트 파싱 시작:\n{ocr_text}")
            lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
            full_text = ' '.join(lines)
            
            # 맨 윗줄(첫 번째 줄) 우선 파싱 - 환자 이름, 나이, 생년월일
            first_line = lines[0] if lines else ""
            print(f"맨 윗줄 우선 파싱: {first_line}")
            
            # 1. 첫 번째 줄에서 환자 이름 우선 추출
            top_line_name_patterns = [
                r'([가-힣]{2,4})\s*\(.*?\)',  # 홍길동(남 25Y 0M) 형태
                r'([가-힣]{2,4})\s*님',       # 홍길동님 형태
                r'([가-힣]{2,4})\s*환자',     # 홍길동환자 형태
                r'^([가-힣]{2,4})\s',         # 맨 앞에 나오는 한국어 이름
                r'([가-힣]{2,4})\s*\d+Y',     # 홍길동 25Y 형태
            ]
            
            for pattern in top_line_name_patterns:
                m = re.search(pattern, first_line)
                if m:
                    full_name = m.group(1)
                    if len(full_name) >= 2:
                        patient_info['last_name'] = full_name[0]
                        patient_info['first_name'] = full_name[1:]
                        print(f"첫 줄에서 이름 발견: 성={full_name[0]}, 이름={full_name[1:]}")
                        break
            
            # 2. 첫 번째 줄에서 생년월일 우선 추출 (나이와 함께 있는 경우 많음)
            top_line_birth_patterns = [
                r'([0-9]{4}[-./][0-9]{1,2}[-./][0-9]{1,2})',  # 1990-01-01 형태
                r'([0-9]{4}년\s*[0-9]{1,2}월\s*[0-9]{1,2}일)',  # 1990년 1월 1일 형태
            ]
            
            for pattern in top_line_birth_patterns:
                m = re.search(pattern, first_line)
                if m:
                    birth_date = re.sub(r'[./년월일\s]', '-', m.group(1))
                    birth_date = re.sub(r'-+', '-', birth_date).strip('-')
                    patient_info['birth_date'] = birth_date
                    print(f"첫 줄에서 생년월일 발견: {birth_date}")
                    break
            
            # 3. Chart No. (차트번호) - 첫 줄 우선, 없으면 전체에서 검색
            chart_patterns = [
                r'Chart No[.\s:]*([0-9]+)',
                r'차트번호[:\s]*([0-9]+)',
                r'No[.\s:]*([0-9]+)'
            ]
            
            # 첫 줄에서 차트번호 우선 검색
            for pattern in chart_patterns:
                m = re.search(pattern, first_line)
                if m:
                    patient_info['chart_no'] = m.group(1)
                    print(f"첫 줄에서 차트번호 발견: {m.group(1)}")
                    break
            
            # 첫 줄에서 찾지 못한 경우 전체에서 검색
            if not patient_info['chart_no']:
                for line in lines:
                    for pattern in chart_patterns:
                        m = re.search(pattern, line)
                        if m:
                            patient_info['chart_no'] = m.group(1)
                            print(f"차트번호 발견: {m.group(1)}")
                            break
                    if patient_info['chart_no']:
                        break
            
            # 4. 첫 줄에서 찾지 못한 이름을 전체에서 재검색
            if not patient_info['first_name']:
                name_patterns = [
                    r'이름[:\s]*([가-힣]{2,4})',
                    r'성명[:\s]*([가-힣]{2,4})',
                    r'([가-힣]{2,4})\s*\(',
                    r'([가-힣]{2,4})\s*님',
                    r'([가-힣]{2,4})\s*환자',
                    r'^([가-힣]{2,4})$'
                ]
                for line in lines:
                    for pattern in name_patterns:
                        m = re.search(pattern, line)
                        if m:
                            full_name = m.group(1)
                            if len(full_name) >= 2:
                                patient_info['last_name'] = full_name[0]
                                patient_info['first_name'] = full_name[1:]
                                print(f"이름 발견: 성={full_name[0]}, 이름={full_name[1:]}")
                                break
                    if patient_info['first_name']:
                        break
            
            # 5. 첫 줄에서 찾지 못한 생년월일을 전체에서 재검색
            if not patient_info['birth_date']:
                birth_patterns = [
                    r'생년월일[:\s]*([0-9]{4}[-./][0-9]{1,2}[-./][0-9]{1,2})',
                    r'출생[:\s]*([0-9]{4}[-./][0-9]{1,2}[-./][0-9]{1,2})',
                    r'생일[:\s]*([0-9]{4}[-./][0-9]{1,2}[-./][0-9]{1,2})',
                    r'DOB[:\s]*([0-9]{4}[-./][0-9]{1,2}[-./][0-9]{1,2})',
                    r'([0-9]{4}[-./][0-9]{1,2}[-./][0-9]{1,2})'
                ]
                for line in lines:
                    for pattern in birth_patterns:
                        m = re.search(pattern, line)
                        if m:
                            birth_date = re.sub(r'[./]', '-', m.group(1))
                            patient_info['birth_date'] = birth_date
                            print(f"생년월일 발견: {birth_date}")
                            break
                    if patient_info['birth_date']:
                        break
            # 휴대전화
            phone_patterns = [
                r'(01[016789]-\d{3,4}-\d{4})',
                r'(01[016789]\d{7,8})'
            ]
            for line in lines:
                for pattern in phone_patterns:
                    m = re.search(pattern, line)
                    if m and not patient_info['phone']:
                        patient_info['phone'] = m.group(1)
                        print(f"휴대전화 발견: {m.group(1)}")
                        break
            # 주소 (여러 줄 지원)
            address_lines = []
            capture = False
            for line in lines:
                if capture:
                    # 주소가 끝나는 조건: 다음 항목(예: '이름:', '생년월일:' 등) 또는 빈 줄
                    if re.match(r'^[가-힣]+[:：]', line) or line == '':
                        break
                    address_lines.append(line)
                if '주소' in line or 'Address' in line:
                    addr = line.split(':', 1)[-1].strip() if ':' in line else line
                    address_lines.append(addr)
                    capture = True
            if address_lines:
                patient_info['address'] = ' '.join(address_lines)
                print(f"주소 발견: {patient_info['address']}")
            # 성별 (1) 상단 (남 xxY xxM), (여 xxY xxM) 패턴
            gender_from_text = ''
            gender_text_patterns = [
                r'\((남)\s*\d+Y',
                r'\((여)\s*\d+Y'
            ]
            for line in lines:
                for pattern in gender_text_patterns:
                    m = re.search(pattern, line)
                    if m:
                        gender_from_text = m.group(1)
                        print(f"성별(텍스트) 발견: {gender_from_text}")
                        break
                if gender_from_text:
                    break
            # 성별 (2) 주민번호 뒷자리로 판별
            gender_from_jumin = ''
            jumin_pattern = r'(\d{6})[- ]?(\d)\d{6}'
            for line in lines:
                m = re.search(jumin_pattern, line)
                if m:
                    code = m.group(2)
                    if code in ['1', '3']:
                        gender_from_jumin = '남'
                    elif code in ['2', '4']:
                        gender_from_jumin = '여'
                    print(f"성별(주민번호) 발견: {gender_from_jumin}")
                    break
            # 최종 gender 결정
            gender = ''
            if gender_from_text:
                gender = 'M' if gender_from_text == '남' else 'F'
            elif gender_from_jumin:
                gender = 'M' if gender_from_jumin == '남' else 'F'
            patient_info['gender'] = gender
            if gender:
                print(f"최종 성별: {gender}")
            print("파싱된 환자 정보:")
            for key, value in patient_info.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"환자 정보 파싱 오류: {e}")
        return patient_info
    
    def extract_patient_info_from_dentweb(self, x: int = None, y: int = None,
                                        width: int = None, height: int = None) -> Dict[str, str]:
        """
        Dentweb에서 환자 정보를 추출하는 전체 프로세스
        
        Args:
            x, y, width, height: 스크린샷 영역 (기본값은 config에서 가져옴)
            
        Returns:
            환자 정보 딕셔너리
        """
        dentweb_window = None
        original_window_state = None
        
        try:
            print("Dentweb 창 찾기 및 최대화 중...")
            
            # 1. Dentweb 창 찾기 및 최대화
            dentweb_window = self.find_dentweb_window()
            if dentweb_window:
                hwnd = dentweb_window['hwnd']
                
                # 현재 창 상태 확인 및 복원
                current_rect = win32gui.GetWindowRect(hwnd)
                print(f"현재 창 상태: {current_rect}")
                
                # 최소화되어 있는지 다시 한번 확인
                if (current_rect[0] < -30000 or current_rect[1] < -30000 or 
                    current_rect[2] - current_rect[0] <= 0):
                    print("창이 여전히 최소화되어 있음 - 강제 복원 시도...")
                    try:
                        # 강력한 복원 시퀀스
                        win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                        import time
                        time.sleep(0.3)
                        win32gui.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL  
                        time.sleep(0.3)
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.BringWindowToTop(hwnd)
                        time.sleep(0.3)
                        
                        # 복원 결과 확인
                        restored_rect = win32gui.GetWindowRect(hwnd)
                        print(f"복원 후 창 상태: {restored_rect}")
                    except Exception as restore_error:
                        print(f"창 복원 중 오류: {restore_error}")
                
                # 현재 창 상태 저장 (복원을 위해)
                original_window_state = win32gui.GetWindowRect(hwnd)
                
                # 창 최대화
                print("Dentweb 창을 최대화합니다...")
                win32gui.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                win32gui.SetForegroundWindow(hwnd)  # 최전면으로 이동
                
                import time
                time.sleep(0.5)  # 최대화 완료 대기
                print("Dentweb 창이 최대화되었습니다")
            else:
                print("Dentweb 창을 찾을 수 없어 기본 설정으로 진행합니다")
            
            print("Dentweb 스크린샷 촬영 중...")
            
            # 2. 스크린샷 촬영
            screenshot = self.capture_dentweb_screenshot(x, y, width, height)
            if not screenshot:
                raise Exception("스크린샷 촬영에 실패했습니다")
            
            print("OCR 텍스트 추출 중...")
            
            # 3. OCR 텍스트 추출
            ocr_text = self.extract_text_with_upstage_ocr(screenshot)
            if not ocr_text:
                raise Exception("OCR 텍스트 추출에 실패했습니다")
            
            print(f"추출된 텍스트:\n{ocr_text}")
            
            # 4. 환자 정보 파싱
            patient_info = self.parse_patient_info(ocr_text)
            
            return patient_info
            
        except Exception as e:
            print(f"환자 정보 추출 오류: {e}")
            return {
                'name': '',
                'birth_date': '',
                'registration_number': '',
                'capture_date': datetime.now().strftime('%Y-%m-%d'),
                'error': str(e)
            }
        finally:
            # 5. OCR 완료 후 Dentweb 창 최소화
            if dentweb_window:
                try:
                    hwnd = dentweb_window['hwnd']
                    print("OCR 완료 - Dentweb 창을 최소화합니다...")
                    win32gui.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                    print("Dentweb 창이 최소화되었습니다")
                except Exception as minimize_error:
                    print(f"창 최소화 실패: {minimize_error}")
            else:
                print("최소화할 Dentweb 창이 없습니다")

    def test_ocr_with_current_screen(self, x: int = 0, y: int = 0, 
                                   width: int = 400, height: int = 400) -> Dict[str, str]:
        """
        현재 화면의 지정된 영역으로 OCR 테스트
        
        Args:
            x, y, width, height: 캡처할 영역 좌표
            
        Returns:
            테스트 결과 딕셔너리
        """
        result = {
            'success': False,
            'text': '',
            'error': '',
            'screenshot_path': ''
        }
        
        try:
            print(f"테스트 OCR 시작 - 영역: ({x}, {y}, {width}, {height})")
            
            # 1. 스크린샷 촬영
            screenshot = self.capture_dentweb_screenshot(x, y, width, height)
            if not screenshot:
                result['error'] = "스크린샷 촬영에 실패했습니다"
                return result
            
            # 스크린샷 경로 저장
            screenshots_dir = Path.home() / "AppData" / "Local" / "WebCephAuto" / "screenshots"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = screenshots_dir / f"test_ocr_{timestamp}.png"
            screenshot.save(screenshot_path)
            result['screenshot_path'] = str(screenshot_path)
            
            print(f"테스트 스크린샷 저장: {screenshot_path}")
            
            # 2. OCR 텍스트 추출
            extracted_text = self.extract_text_with_upstage_ocr(screenshot)
            if extracted_text:
                result['success'] = True
                result['text'] = extracted_text
                print(f"OCR 테스트 성공! 추출된 텍스트:\n{extracted_text}")
            else:
                result['error'] = "OCR 텍스트 추출에 실패했습니다"
                
        except Exception as e:
            result['error'] = f"OCR 테스트 오류: {str(e)}"
            print(f"OCR 테스트 실패: {e}")
        
        return result


class DentwebAutomationWorker(QThread):
    """Dentweb 자동화 워커 스레드"""
    
    # 시그널 정의
    patient_info_extracted = pyqtSignal(dict)  # 환자 정보 추출 완료
    screenshot_captured = pyqtSignal(str)      # 스크린샷 촬영 완료
    error_occurred = pyqtSignal(str)           # 오류 발생
    status_updated = pyqtSignal(str)           # 상태 업데이트
    
    def __init__(self):
        super().__init__()
        self.extractor = DentwebOCRExtractor()
        self.screenshot_coords = None
    
    def set_screenshot_coordinates(self, x: int, y: int, width: int, height: int):
        """스크린샷 좌표 설정"""
        self.screenshot_coords = (x, y, width, height)
    
    def run(self):
        """워커 스레드 실행"""
        try:
            self.status_updated.emit("Dentweb 화면에서 환자 정보를 추출하는 중...")
            
            # 좌표 설정 확인
            if self.screenshot_coords:
                x, y, width, height = self.screenshot_coords
                patient_info = self.extractor.extract_patient_info_from_dentweb(x, y, width, height)
            else:
                patient_info = self.extractor.extract_patient_info_from_dentweb()
            
            if 'error' in patient_info:
                self.error_occurred.emit(patient_info['error'])
            else:
                self.patient_info_extracted.emit(patient_info)
                self.status_updated.emit("환자 정보 추출이 완료되었습니다")
                
        except Exception as e:
            self.error_occurred.emit(f"자동화 프로세스 오류: {str(e)}") 