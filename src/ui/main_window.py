"""
메인 윈도우 모듈
애플리케이션의 중앙 창으로, 모든 주요 기능을 통합 관리
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QTabWidget, QMenuBar, QStatusBar, QAction, 
                           QMessageBox, QSystemTrayIcon, QMenu, QSplitter,
                           QFrame, QLabel, QPushButton, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont, QPixmap, QKeySequence

from .styles import COLORS
from .dashboard import DashboardWidget
from .patient_form import PatientFormWidget
from .automation_monitor import AutomationMonitorWidget
from .automation_flow import AutomationFlowWidget  # 새로 추가
from .settings_window import SettingsWidget
from ..utils.font_loader import font_loader
from ..config import config

class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    # 시그널 정의
    window_closing = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.settings_window = None
        self.init_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.setup_system_tray()
        self.load_window_state()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Web Ceph Auto - 치과 영상 분석 자동화")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 탭 위젯 생성
        self.create_tab_widget(main_layout)
        
        # 스타일 적용
        self.apply_styles()
        
    def create_tab_widget(self, parent_layout):
        """탭 위젯 생성"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")
        
        # 탭 생성 및 추가
        self.create_tabs()
        
        parent_layout.addWidget(self.tab_widget)
        
    def create_tabs(self):
        """각 탭 생성"""
        
        # 1. 대시보드 탭 (기본 화면)
        self.dashboard_widget = DashboardWidget()
        self.tab_widget.addTab(self.dashboard_widget, "📊 대시보드")
        
        # 2. 덴트웹-웹셉 자동화 탭
        self.automation_flow_widget = AutomationFlowWidget()
        self.tab_widget.addTab(self.automation_flow_widget, "🚀 덴트웹-웹셉 자동화")
        
        # 3. 환자 관리 탭
        self.patient_form_widget = PatientFormWidget()
        self.tab_widget.addTab(self.patient_form_widget, "👤 환자 관리")
        
        # 4. 설정 탭
        self.settings_widget = SettingsWidget()
        self.tab_widget.addTab(self.settings_widget, "⚙️ 설정")
        
        # 기본 탭을 대시보드로 설정
        self.tab_widget.setCurrentIndex(0)
        
        # 시그널 연결
        self.connect_signals()
        
    def connect_signals(self):
        """시그널 연결"""
        # 자동화 플로우 시그널
        self.automation_flow_widget.automation_started.connect(self.on_automation_started)
        self.automation_flow_widget.automation_completed.connect(self.on_automation_completed)
        self.automation_flow_widget.automation_failed.connect(self.on_automation_failed)
        self.automation_flow_widget.status_updated.connect(self.on_status_updated)
        
        # 환자 폼 시그널 (시그널이 있는 경우에만 연결)
        if hasattr(self.patient_form_widget, 'patient_saved'):
            self.patient_form_widget.patient_saved.connect(self.on_patient_saved)
        if hasattr(self.patient_form_widget, 'automation_requested'):
            self.patient_form_widget.automation_requested.connect(self.on_automation_requested)
        
        # 대시보드 빠른 액션 시그널 연결
        self.dashboard_widget.quick_action_widget.action_clicked.connect(self.handle_quick_action)
    
    def navigate_to_page(self, page_name):
        """페이지 전환 메서드"""
        try:
            if page_name == "dashboard":
                self.tab_widget.setCurrentWidget(self.dashboard_widget)
            elif page_name == "patient_form":
                self.tab_widget.setCurrentWidget(self.patient_form_widget)
            elif page_name == "automation":
                self.tab_widget.setCurrentWidget(self.automation_flow_widget)
            elif page_name == "settings":
                self.tab_widget.setCurrentWidget(self.settings_widget)
            else:
                print(f"알 수 없는 페이지: {page_name}")
        except Exception as e:
            print(f"페이지 전환 오류: {e}")
    
    def handle_quick_action(self, action_type):
        """대시보드 빠른 액션 처리"""
        if action_type == "new_patient":
            # 신규 환자 처리 시 바로 자동화 탭으로 이동하여 OCR 실행
            self.navigate_to_page("automation")
            # OCR 실행 및 복사 단계 바로 실행
            self.automation_flow_widget.execute_step('ocr_extraction')
        elif action_type == "batch_process":
            self.navigate_to_page("patient_form")
        elif action_type == "monitor":
            self.navigate_to_page("automation")
        
    def setup_menu(self):
        """메뉴바 설정"""
        menubar = self.menuBar()
        menubar.setObjectName("menuBar")
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일(&F)')
        
        # 새 환자
        new_patient_action = QAction('새 환자(&N)', self)
        new_patient_action.setShortcut(QKeySequence.New)
        new_patient_action.triggered.connect(self.new_patient)
        file_menu.addAction(new_patient_action)
        
        file_menu.addSeparator()
        
        # 종료
        exit_action = QAction('종료(&X)', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 자동화 메뉴
        automation_menu = menubar.addMenu('자동화(&A)')
        
        # 덴트웹-웹셉 자동화 시작
        start_automation_action = QAction('덴트웹-웹셉 자동화 시작(&S)', self)
        start_automation_action.setShortcut('Ctrl+R')
        start_automation_action.triggered.connect(self.start_dentweb_webceph_automation)
        automation_menu.addAction(start_automation_action)
        
        automation_menu.addSeparator()
        
        # OCR만 실행
        ocr_only_action = QAction('OCR만 실행(&O)', self)
        ocr_only_action.setShortcut('Ctrl+O')
        ocr_only_action.triggered.connect(self.execute_ocr_only)
        automation_menu.addAction(ocr_only_action)
        
        # 설정 메뉴
        settings_menu = menubar.addMenu('설정(&S)')
        
        # 일반 설정
        general_settings_action = QAction('일반 설정(&G)', self)
        general_settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(general_settings_action)
        
        settings_menu.addSeparator()
        
        # API 설정
        api_settings_action = QAction('API 설정(&A)', self)
        api_settings_action.triggered.connect(self.open_api_settings)
        settings_menu.addAction(api_settings_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말(&H)')
        
        # 사용법
        usage_action = QAction('사용법(&U)', self)
        usage_action.triggered.connect(self.show_usage)
        help_menu.addAction(usage_action)
        
        help_menu.addSeparator()
        
        # 정보
        about_action = QAction('정보(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        """상태바 설정"""
        self.status_bar = self.statusBar()
        self.status_bar.setObjectName("statusBar")
        
        # 상태 메시지
        self.status_label = QLabel("준비")
        self.status_bar.addWidget(self.status_label)
        
        # 연결 상태
        self.connection_label = QLabel("연결 확인 중...")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # 초기 상태 확인
        QTimer.singleShot(2000, self.check_connection_status)
        
    def setup_system_tray(self):
        """시스템 트레이 설정"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # 트레이 아이콘 설정
            try:
                icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.ico"
                if icon_path.exists():
                    self.tray_icon.setIcon(QIcon(str(icon_path)))
                else:
                    # 기본 아이콘 사용
                    self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
            except:
                self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
            
            # 트레이 메뉴
            tray_menu = QMenu()
            
            show_action = QAction("창 보이기", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("종료", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            
            # 트레이 아이콘 표시
            self.tray_icon.show()
            
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['gray_50']};
                font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
            }}
            
            #mainTabWidget {{
                background-color: white;
                border: none;
            }}
            
            #mainTabWidget::pane {{
                border: 1px solid {COLORS['gray_200']};
                background-color: white;
            }}
            
            #mainTabWidget::tab-bar {{
                left: 8px;
            }}
            
            QTabBar::tab {{
                background-color: {COLORS['gray_100']};
                color: {COLORS['gray_600']};
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                min-width: 120px;
            }}
            
            QTabBar::tab:selected {{
                background-color: white;
                color: {COLORS['primary_500']};
                font-weight: 600;
                border-bottom: 2px solid {COLORS['primary_500']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['gray_200']};
                color: {COLORS['gray_700']};
            }}
            
            #menuBar {{
                background-color: white;
                border-bottom: 1px solid {COLORS['gray_200']};
                font-size: 14px;
                padding: 4px 0;
            }}
            
            QMenuBar::item {{
                padding: 8px 16px;
                background-color: transparent;
                color: {COLORS['gray_700']};
            }}
            
            QMenuBar::item:selected {{
                background-color: {COLORS['primary_50']};
                color: {COLORS['primary_500']};
            }}
            
            QMenu {{
                background-color: white;
                border: 1px solid {COLORS['gray_200']};
                border-radius: 6px;
                padding: 8px 0;
                font-size: 14px;
            }}
            
            QMenu::item {{
                padding: 8px 16px;
                color: {COLORS['gray_700']};
            }}
            
            QMenu::item:selected {{
                background-color: {COLORS['primary_50']};
                color: {COLORS['primary_500']};
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: {COLORS['gray_200']};
                margin: 4px 8px;
            }}
            
            #statusBar {{
                background-color: white;
                border-top: 1px solid {COLORS['gray_200']};
                font-size: 13px;
                color: {COLORS['gray_600']};
            }}
        """)
        
    # 슬롯 메서드들
    def on_automation_started(self):
        """자동화 시작 시 처리"""
        self.status_label.setText("자동화 실행 중...")
        self.tab_widget.setCurrentWidget(self.automation_flow_widget)
        
    def on_automation_completed(self, result_data):
        """자동화 완료 시 처리"""
        self.status_label.setText("자동화 완료")
        
        # 대시보드 업데이트
        self.dashboard_widget.update_daily_stats()
        
        # 완료 알림
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "Web Ceph Auto",
                "자동화 프로세스가 완료되었습니다.",
                QSystemTrayIcon.Information,
                3000
            )
            
    def on_automation_failed(self, error_message):
        """자동화 실패 시 처리"""
        self.status_label.setText("자동화 실패")
        
        QMessageBox.critical(
            self,
            "자동화 실패",
            f"자동화 프로세스 중 오류가 발생했습니다:\n\n{error_message}"
        )
        
    def on_status_updated(self, message, level):
        """상태 업데이트 처리"""
        self.status_label.setText(message)
        
    def on_patient_saved(self, patient_data):
        """환자 저장 시 처리"""
        self.status_label.setText(f"환자 '{patient_data['name']}' 저장됨")
        
    def on_automation_requested(self, patient_data):
        """자동화 요청 처리"""
        # 자동화 플로우 탭으로 이동
        self.tab_widget.setCurrentWidget(self.automation_flow_widget)
        
    def on_tray_activated(self, reason):
        """트레이 아이콘 활성화 처리"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
                
    # 메뉴 액션 메서드들
    def new_patient(self):
        """새 환자 생성"""
        self.tab_widget.setCurrentWidget(self.patient_form_widget)
        self.patient_form_widget.clear_form()
        
    def start_dentweb_webceph_automation(self):
        """덴트웹-웹셉 자동화 시작"""
        self.tab_widget.setCurrentWidget(self.automation_flow_widget)
        
    def execute_ocr_only(self):
        """OCR만 실행"""
        self.tab_widget.setCurrentWidget(self.automation_flow_widget)
        self.automation_flow_widget.execute_step('ocr_extraction')
        
    def open_settings(self):
        """설정 창 열기"""
        if not self.settings_window:
            self.settings_window = SettingsWidget()
        
        self.settings_window.show()
        self.settings_window.raise_()
        
    def open_api_settings(self):
        """API 설정 열기"""
        self.open_settings()
        # 설정 창에서 API 탭으로 이동하는 로직 추가 필요
        
    def show_usage(self):
        """사용법 표시"""
        usage_text = """
        <h3>🦷 Web Ceph Auto 사용법</h3>
        
        <h4>1. 초기 설정</h4>
        <ul>
            <li>설정 > API 설정에서 Upstage OCR API 키 입력</li>
            <li>WebCeph 로그인 정보 입력</li>
            <li>Make.com Webhook URL 설정 (선택)</li>
        </ul>
        
        <h4>2. 자동화 실행</h4>
        <ul>
            <li>덴트웹 프로그램에서 환자 정보 화면 준비</li>
            <li>'덴트웹-웹셉 자동화' 탭에서 단계별 실행</li>
            <li>OCR → WebCeph 분석 → PDF 다운로드 순서로 진행</li>
        </ul>
        
        <h4>3. 결과 확인</h4>
        <ul>
            <li>대시보드에서 처리 현황 확인</li>
            <li>로그에서 상세 실행 내역 확인</li>
            <li>PDF 파일은 설정된 폴더에 자동 저장</li>
        </ul>
        """
        
        QMessageBox.information(self, "사용법", usage_text)
        
    def show_about(self):
        """정보 표시"""
        about_text = """
        <h3>🦷 Web Ceph Auto v1.0</h3>
        <p><b>치과 영상 분석 자동화 프로그램</b></p>
        
        <p>덴트웹과 WebCeph 플랫폼을 연동하여<br>
        환자 분석 프로세스를 자동화하는 솔루션입니다.</p>
        
        <p><b>주요 기능:</b></p>
        <ul>
            <li>OCR 기반 환자 정보 자동 추출</li>
            <li>WebCeph 자동 로그인 및 분석</li>
            <li>PDF 결과 자동 다운로드</li>
            <li>실시간 진행 상황 모니터링</li>
        </ul>
        
        <p><small>Copyright © 2024 Web Ceph Auto Team</small></p>
        """
        
        QMessageBox.about(self, "정보", about_text)
        
    def check_connection_status(self):
        """연결 상태 확인"""
        # 실제로는 API 연결 상태를 확인하는 로직 구현
        try:
            # Upstage API 연결 테스트
            api_key = config.get('upstage', 'api_key', '')
            if api_key:
                self.connection_label.setText("🟢 API 연결됨")
            else:
                self.connection_label.setText("🟡 API 키 필요")
        except:
            self.connection_label.setText("🔴 연결 실패")
            
    def load_window_state(self):
        """창 상태 로드"""
        try:
            # config에서 창 크기와 위치 로드
            width = config.get_int('window', 'width', 1400)
            height = config.get_int('window', 'height', 900)
            x = config.get_int('window', 'x', 100)
            y = config.get_int('window', 'y', 100)
            
            self.resize(width, height)
            self.move(x, y)
            
            # 마지막 활성 탭 로드
            last_tab = config.get_int('window', 'last_tab', 0)
            if 0 <= last_tab < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(last_tab)
                
        except:
            pass  # 설정 로드 실패 시 기본값 사용
            
    def save_window_state(self):
        """창 상태 저장"""
        try:
            # 창 크기와 위치 저장
            config.set('window', 'width', str(self.width()))
            config.set('window', 'height', str(self.height()))
            config.set('window', 'x', str(self.x()))
            config.set('window', 'y', str(self.y()))
            
            # 현재 활성 탭 저장
            config.set('window', 'last_tab', str(self.tab_widget.currentIndex()))
            
            config.save()
        except:
            pass
            
    def closeEvent(self, event):
        """창 닫기 이벤트 처리"""
        # 자동화가 실행 중인지 확인
        if (hasattr(self, 'automation_flow_widget') and 
            self.automation_flow_widget.automation_worker and 
            self.automation_flow_widget.automation_worker.isRunning()):
            
            reply = QMessageBox.question(
                self,
                "자동화 실행 중",
                "자동화가 실행 중입니다. 정말 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        # 창 상태 저장
        self.save_window_state()
        
        # 시그널 발생
        self.window_closing.emit()
        
        # 트레이 아이콘 숨기기
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                self.tray_icon.hide()
        except RuntimeError:
            # C/C++ 객체가 이미 삭제된 경우 무시
            pass
            
        event.accept()
        
    def __del__(self):
        """소멸자"""
        # 트레이 아이콘 정리 (이미 삭제된 경우 오류 방지)
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                self.tray_icon.hide()
        except RuntimeError:
            # C/C++ 객체가 이미 삭제된 경우 무시
            pass 