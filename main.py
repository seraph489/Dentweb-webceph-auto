#!/usr/bin/env python3
"""
Web Ceph Auto Processor
치과 영상 분석 자동화 프로그램 메인 실행 파일

덴트웹과 WebCeph 플랫폼을 연동하여 환자 분석 프로세스를 완전 자동화하는
데스크톱 애플리케이션입니다.

주요 기능:
- Dentweb OCR 기반 환자 정보 자동 추출
- WebCeph 자동 로그인 및 분석 실행
- PDF 결과 자동 다운로드 및 전송
- 실시간 진행 상황 모니터링

Version: 1.0.0
Author: Web Ceph Auto Team
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QPainter, QBrush, QColor
from typing import Optional, Dict
import re

# 프로젝트 루트 디렉터리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.ui.main_window import MainWindow
from src.ui.login_window import LoginWindow
from src.utils.font_loader import font_loader
# from src.utils.system_checker import SystemChecker  # 제거

import pygetwindow as gw
import win32gui

def setup_logging():
    """로깅 설정"""
    try:
        # 로그 디렉터리 생성
        log_dir = Path.home() / "AppData" / "Local" / "WebCephAuto" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 로그 파일 경로 (날짜별로 분리)
        today = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"app_{today}.log"
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Windows에서 콘솔 인코딩 설정
        if sys.platform.startswith('win'):
            try:
                import io
                if hasattr(sys.stdout, 'buffer'):
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                if hasattr(sys.stderr, 'buffer'):
                    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            except Exception as e:
                print(f"콘솔 인코딩 설정 실패: {e}")
        
        # 애플리케이션 시작 로그
        logger = logging.getLogger(__name__)
        logger.info("=" * 50)
        logger.info("Web Ceph Auto Processor 시작")
        logger.info(f"버전: 1.0.0")
        logger.info(f"Python: {sys.version}")
        logger.info(f"작업 디렉터리: {os.getcwd()}")
        logger.info("=" * 50)
        
    except Exception as e:
        print(f"로깅 설정 실패: {e}")

def check_system_requirements():
    """시스템 요구사항 확인"""
    try:
        # Python 버전 확인
        if sys.version_info < (3, 7):
            QMessageBox.critical(
                None,
                "시스템 요구사항 오류",
                "Python 3.7 이상이 필요합니다.\n"
                f"현재 버전: {sys.version}"
            )
            return False
            
        # 필수 디렉터리 생성
        required_dirs = [
            Path.home() / "Documents" / "WebCephAuto" / "Images",
            Path.home() / "Documents" / "WebCephAuto" / "Results", 
            Path.home() / "Documents" / "WebCephAuto" / "Backup",
            Path.home() / "AppData" / "Local" / "WebCephAuto" / "screenshots",
            Path.home() / "AppData" / "Local" / "WebCephAuto" / "logs",
        ]
        
        for dir_path in required_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # 설정 파일 초기화
        config._load_config()
        
        return True
        
    except Exception as e:
        logging.error(f"시스템 요구사항 확인 실패: {e}")
        QMessageBox.critical(
            None,
            "초기화 오류",
            f"시스템 초기화 중 오류가 발생했습니다:\n{str(e)}"
        )
        return False

def create_splash_screen(app):
    """개선된 스플래시 스크린 생성"""
    try:
        # 스플래시 이미지 경로
        splash_path = project_root / "assets" / "splash.png"
        
        if splash_path.exists():
            pixmap = QPixmap(str(splash_path))
        else:
            # 기본 스플래시 화면 생성 (IA 디자인 반영)
            pixmap = QPixmap(500, 350)
            pixmap.fill(QColor("#F9FAFB"))
            
            # 그라데이션 배경 추가
            painter = QPainter(pixmap)
            gradient = painter.fillRect(0, 0, 500, 100, QColor("#3B82F6"))
            painter.end()
            
        splash = QSplashScreen(pixmap)
        splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen | Qt.FramelessWindowHint)
        
        # 스플래시 메시지 스타일 (IA 디자인 반영)
        splash.setStyleSheet("""
            QSplashScreen {
                background-color: #F9FAFB;
                border: 2px solid #E5E7EB;
                border-radius: 12px;
            }
        """)
        
        return splash
        
    except Exception as e:
        logging.warning(f"스플래시 스크린 생성 실패: {e}")
        return None

def show_startup_message(splash):
    """시작 메시지 표시 (IA 기반 단계별 메시지)"""
    if splash:
        messages = [
            ("시스템 초기화 중...", 10),
            ("폰트 로딩 중...", 20),
            ("UI 컴포넌트 로딩 중...", 40),
            ("자동화 엔진 초기화 중...", 60),
            ("설정 로딩 중...", 80),
            ("준비 완료!", 100)
        ]
        
        for message, progress in messages:
            splash.showMessage(
                f"\n\nWeb Ceph Auto v1.0\n\n{message}",
                Qt.AlignCenter,
                Qt.black
            )
            QApplication.processEvents()
            QTimer.singleShot(300, lambda: None)  # 0.3초 대기

class AutoCephApplication(QApplication):
    """메인 애플리케이션 클래스 (IA v3.0 반영)"""
    
    # 시그널 정의
    settings_required = pyqtSignal()  # 설정이 필요할 때
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # 애플리케이션 정보 설정
        self.setApplicationName("Web Ceph Auto")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Web Ceph Auto Team")
        self.setOrganizationDomain("webcephauto.com")
        
        # 한국어 글꼴 로드
        font_loader.load_korean_fonts()
        
        # 기본 폰트 설정 (IA 권장 폰트)
        try:
            default_font = QFont("Pretendard", 10)
            if not default_font.exactMatch():
                default_font = QFont("Noto Sans KR", 10)
            if not default_font.exactMatch():
                default_font = QFont("맑은 고딕", 10)
                
            self.setFont(default_font)
        except Exception as e:
            logging.warning(f"기본 폰트 설정 실패: {e}")
        
        # 메인 윈도우 및 로그인 윈도우
        self.main_window = None
        self.login_window = None
        
        # 초기 설정 상태
        self.is_first_run = self._check_first_run()
        
    def _check_first_run(self):
        """첫 실행 여부 확인"""
        try:
            # 설정 파일이 없거나 필수 설정이 비어있으면 첫 실행
            webceph_id = config.get('webceph', 'username', '')
            api_key = config.get('upstage', 'api_key', '')
            if not webceph_id or not api_key:
                return True
            return False
        except:
            return True
        
    def initialize(self):
        """애플리케이션 초기화 (IA v3.0: 대시보드 먼저 표시)"""
        try:
            # 메인 윈도우를 바로 표시 (IA 설계 원칙: Dashboard-First)
            self.show_main_window()
            
            return True
            
        except Exception as e:
            logging.error(f"애플리케이션 초기화 실패: {e}")
            QMessageBox.critical(
                None,
                "초기화 오류",
                f"애플리케이션 초기화 중 오류가 발생했습니다:\n{str(e)}"
            )
            return False
    
    def show_main_window(self, user_info=None):
        """메인 윈도우 표시 (IA v3.0: Dashboard-First)"""
        try:
            # 메인 윈도우 생성 및 표시
            self.main_window = MainWindow()
            
            # 대시보드 탭으로 시작 (IA 설계 원칙)
            self.main_window.tab_widget.setCurrentIndex(0)  # 첫 번째 탭 = 대시보드
            
            # 윈도우 표시
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            # 첫 실행이거나 설정이 없는 경우 알림 표시
            if self.is_first_run:
                self.show_settings_required_message()
            
            # 시작 로그
            logging.info("메인 윈도우가 성공적으로 표시되었습니다 (대시보드 우선)")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logging.error(f"메인 윈도우 표시 실패: {e}")
            logging.error(f"상세 오류:\n{error_details}")
            QMessageBox.critical(
                None,
                "윈도우 오류",
                f"메인 윈도우 표시 중 오류가 발생했습니다:\n{str(e)}\n\n상세 정보:\n{error_details}"
            )
    
    def show_settings_required_message(self):
        """설정 필요 알림 표시"""
        try:
            QTimer.singleShot(1000, lambda: QMessageBox.information(
                self.main_window,
                "초기 설정 필요",
                "Web Ceph Auto를 처음 사용하시는군요!\n\n"
                "원활한 사용을 위해 다음 설정을 완료해주세요:\n"
                "• WebCeph 계정 정보\n"
                "• Upstage OCR API 키\n"
                "• 폴더 경로 설정\n\n"
                "설정 탭에서 정보를 입력해주세요."
            ))
        except Exception as e:
            logging.warning(f"설정 알림 표시 실패: {e}")            


def main():
    """메인 함수"""
    try:
        # 로깅 설정
        setup_logging()
        
        # QApplication 생성
        app = AutoCephApplication(sys.argv)
        
        # 스플래시 스크린 표시
        splash = create_splash_screen(app)
        if splash:
            splash.show()
            show_startup_message(splash)
        
        # 시스템 요구사항 확인
        if not check_system_requirements():
            return 1
            
        # 애플리케이션 초기화
        if not app.initialize():
            return 1
            
        # 스플래시 스크린 숨기기
        if splash:
            splash.finish(app.main_window if app.main_window else None)
            
        # 예외 처리 핸들러 설정
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
                
            logging.critical(
                "처리되지 않은 예외 발생",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # 상세한 오류 정보 제공
            error_detail = f"{exc_type.__name__}: {exc_value}"
            
            QMessageBox.critical(
                None,
                "애플리케이션 오류",
                f"예상치 못한 오류가 발생했습니다:\n\n"
                f"{error_detail}\n\n"
                f"로그 파일을 확인해주세요:\n"
                f"{Path.home() / 'AppData' / 'Local' / 'WebCephAuto' / 'logs'}"
            )
        
        sys.excepthook = handle_exception
        
        # 이벤트 루프 실행
        exit_code = app.exec_()
        
        # 정리 작업
        logging.info("애플리케이션 종료")
        logging.info("=" * 50)
        
        return exit_code
        
    except Exception as e:
        # 최종 예외 처리
        error_msg = f"애플리케이션 시작 중 치명적 오류: {e}"
        print(error_msg)
        
        try:
            logging.critical(error_msg)
        except:
            pass  # 로깅도 실패한 경우
            
        # GUI가 가능하면 메시지 박스 표시
        try:
            if 'app' in locals():
                QMessageBox.critical(None, "치명적 오류", error_msg)
            else:
                # QApplication이 생성되지 않은 경우
                temp_app = QApplication(sys.argv)
                QMessageBox.critical(None, "치명적 오류", error_msg)
        except:
            pass  # GUI 표시도 실패한 경우
            
        return 1

if __name__ == "__main__":
    # Windows에서 High DPI 지원
    if sys.platform.startswith('win'):
        try:
            from PyQt5.QtCore import Qt
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except:
            pass
    
    # 메인 함수 실행
    sys.exit(main())