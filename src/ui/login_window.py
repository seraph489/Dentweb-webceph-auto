"""
로그인 윈도우 클래스
Design Guide의 로그인 페이지 디자인을 구현
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QCheckBox, QFrame,
                           QMessageBox, QProgressBar, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont

from .styles import COLORS
from ..utils.font_loader import font_loader
from ..config import config

class LoginWorker(QThread):
    """로그인 작업을 백그라운드에서 처리하는 워커 스레드"""
    
    login_result = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
    
    def run(self):
        """로그인 검증 로직"""
        try:
            # 실제 구현에서는 Web Ceph 로그인 API 호출
            # 현재는 데모를 위한 간단한 검증
            self.msleep(1500)  # 로그인 시뮬레이션
            
            if self.username and self.password:
                # 간단한 검증 (실제로는 Web Ceph API 연동)
                if len(self.username) >= 3 and len(self.password) >= 4:
                    self.login_result.emit(True, "로그인 성공")
                else:
                    self.login_result.emit(False, "사용자명은 3자 이상, 비밀번호는 4자 이상이어야 합니다")
            else:
                self.login_result.emit(False, "사용자명과 비밀번호를 입력해주세요")
                
        except Exception as e:
            self.login_result.emit(False, f"로그인 중 오류가 발생했습니다: {str(e)}")

class LoginWindow(QDialog):
    """로그인 윈도우"""
    
    login_successful = pyqtSignal(str)  # username
    
    def __init__(self):
        super().__init__()
        self.login_worker = None
        
        # 폰트 로드
        font_loader.load_korean_fonts()
        
        # UI 초기화
        self.init_ui()
        self.setup_styles()
        self.load_saved_credentials()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Web Ceph Auto - 로그인")
        self.setFixedSize(QSize(480, 600))
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 배경 컨테이너
        self.container = QFrame()
        self.container.setObjectName("login_container")
        main_layout.addWidget(self.container)
        
        # 컨테이너 레이아웃
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setAlignment(Qt.AlignCenter)
        
        # 로그인 카드
        self.create_login_card(container_layout)
    
    def create_login_card(self, layout):
        """로그인 카드 생성"""
        # 카드 프레임
        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedSize(QSize(400, 500))
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(24)
        
        # 헤더 섹션
        self.create_header_section(card_layout)
        
        # 로그인 폼
        self.create_login_form(card_layout)
        
        # 버튼 섹션
        self.create_button_section(card_layout)
        
        # 추가 옵션
        self.create_options_section(card_layout)
        
        layout.addWidget(card)
    
    def create_header_section(self, layout):
        """헤더 섹션 생성"""
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(8)
        
        # 로고/아이콘 (텍스트로 대체)
        logo_label = QLabel("🦷")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFont(QFont("Segoe UI Emoji", 48))
        logo_label.setStyleSheet(f"color: {COLORS['primary_500']};")
        
        # 제품명
        title_label = QLabel("Web Ceph Auto")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(font_loader.get_font('Bold', 28))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        # 부제목
        subtitle_label = QLabel("치과 영상 분석 자동화")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(font_loader.get_font('Regular', 14))
        subtitle_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
    
    def create_login_form(self, layout):
        """로그인 폼 생성"""
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)
        
        # 사용자명 입력
        username_layout = QVBoxLayout()
        username_layout.setSpacing(6)
        
        username_label = QLabel("사용자명")
        username_label.setFont(font_loader.get_font('Medium', 12))
        username_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Web Ceph 사용자명을 입력하세요")
        self.username_input.setFont(font_loader.get_font('Regular', 14))
        self.username_input.setMinimumHeight(44)
        self.username_input.returnPressed.connect(self.on_login_clicked)
        
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        
        # 비밀번호 입력
        password_layout = QVBoxLayout()
        password_layout.setSpacing(6)
        
        password_label = QLabel("비밀번호")
        password_label.setFont(font_loader.get_font('Medium', 12))
        password_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("비밀번호를 입력하세요")
        self.password_input.setFont(font_loader.get_font('Regular', 14))
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(44)
        self.password_input.returnPressed.connect(self.on_login_clicked)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        
        form_layout.addLayout(username_layout)
        form_layout.addLayout(password_layout)
        
        layout.addLayout(form_layout)
    
    def create_button_section(self, layout):
        """버튼 섹션 생성"""
        button_layout = QVBoxLayout()
        button_layout.setSpacing(12)
        
        # 로그인 버튼
        self.login_btn = QPushButton("로그인")
        self.login_btn.setFont(font_loader.get_font('SemiBold', 16))
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setProperty("class", "primary")
        self.login_btn.clicked.connect(self.on_login_clicked)
        
        # 진행률 표시 (초기에는 숨김)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 무한 진행률
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(4)
        
        # 상태 메시지
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(font_loader.get_font('Regular', 12))
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.progress_bar)
        button_layout.addWidget(self.status_label)
        
        layout.addLayout(button_layout)
    
    def create_options_section(self, layout):
        """추가 옵션 섹션 생성"""
        options_layout = QVBoxLayout()
        options_layout.setSpacing(16)
        
        # 자동 로그인 체크박스
        self.auto_login_checkbox = QCheckBox("자동 로그인")
        self.auto_login_checkbox.setFont(font_loader.get_font('Regular', 12))
        self.auto_login_checkbox.setStyleSheet(f"color: {COLORS['gray_600']};")
        
        # 도움말 링크들
        help_layout = QHBoxLayout()
        help_layout.setAlignment(Qt.AlignCenter)
        
        settings_btn = QPushButton("설정")
        settings_btn.setFont(font_loader.get_font('Regular', 12))
        settings_btn.setProperty("class", "ghost")
        settings_btn.clicked.connect(self.show_settings)
        
        help_btn = QPushButton("도움말")
        help_btn.setFont(font_loader.get_font('Regular', 12))
        help_btn.setProperty("class", "ghost")
        help_btn.clicked.connect(self.show_help)
        
        help_layout.addWidget(settings_btn)
        help_layout.addWidget(QLabel("|"))
        help_layout.addWidget(help_btn)
        
        options_layout.addWidget(self.auto_login_checkbox)
        options_layout.addLayout(help_layout)
        
        layout.addLayout(options_layout)
    
    def setup_styles(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['gray_50']};
            }}
            
            #login_container {{
                background-color: {COLORS['gray_50']};
            }}
            
            #login_card {{
                background-color: {COLORS['white']};
                border: 1px solid {COLORS['gray_200']};
                border-radius: 12px;
            }}
            
            QLineEdit {{
                background-color: {COLORS['white']};
                border: 1px solid {COLORS['gray_300']};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                color: {COLORS['gray_700']};
            }}
            
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary_500']};
                outline: none;
            }}
            
            QLineEdit::placeholder {{
                color: {COLORS['gray_400']};
            }}
            
            QPushButton.primary {{
                background-color: {COLORS['primary_500']};
                color: {COLORS['white']};
                border: none;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 16px;
                font-weight: 600;
            }}
            
            QPushButton.primary:hover {{
                background-color: {COLORS['primary_600']};
            }}
            
            QPushButton.primary:pressed {{
                background-color: {COLORS['primary_700']};
            }}
            
            QPushButton.primary:disabled {{
                background-color: {COLORS['gray_300']};
                color: {COLORS['gray_500']};
            }}
            
            QPushButton.ghost {{
                background-color: transparent;
                color: {COLORS['gray_500']};
                border: none;
                padding: 4px 8px;
                font-size: 12px;
            }}
            
            QPushButton.ghost:hover {{
                color: {COLORS['primary_500']};
            }}
            
            QCheckBox {{
                color: {COLORS['gray_600']};
                font-size: 12px;
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {COLORS['gray_300']};
                border-radius: 4px;
                background-color: {COLORS['white']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary_500']};
                border-color: {COLORS['primary_500']};
            }}
            
            QProgressBar {{
                background-color: {COLORS['gray_200']};
                border: none;
                border-radius: 2px;
                height: 4px;
            }}
            
            QProgressBar::chunk {{
                background-color: {COLORS['primary_500']};
                border-radius: 2px;
            }}
        """)
    
    def load_saved_credentials(self):
        """저장된 로그인 정보 로드"""
        if config.get_bool('general', 'auto_login'):
            username, password = config.get_credentials()
            if username and password:
                self.username_input.setText(username)
                self.password_input.setText(password)
                self.auto_login_checkbox.setChecked(True)
                
                # 자동 로그인 실행
                QTimer.singleShot(1000, self.on_login_clicked)
    
    def on_login_clicked(self):
        """로그인 버튼 클릭 처리"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            self.show_status_message("사용자명과 비밀번호를 입력해주세요", "error")
            return
        
        # UI 상태 변경
        self.set_loading_state(True)
        
        # 백그라운드에서 로그인 처리
        self.login_worker = LoginWorker(username, password)
        self.login_worker.login_result.connect(self.on_login_result)
        self.login_worker.start()
    
    def on_login_result(self, success, message):
        """로그인 결과 처리"""
        self.set_loading_state(False)
        
        if success:
            # 자동 로그인 설정 저장
            if self.auto_login_checkbox.isChecked():
                config.save_credentials(
                    self.username_input.text().strip(),
                    self.password_input.text().strip()
                )
                config.set('general', 'auto_login', 'true')
            else:
                config.set('general', 'auto_login', 'false')
            
            # 성공 시그널 발송
            self.login_successful.emit(self.username_input.text().strip())
        else:
            self.show_status_message(message, "error")
    
    def set_loading_state(self, loading):
        """로딩 상태 설정"""
        self.login_btn.setEnabled(not loading)
        self.username_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
        
        if loading:
            self.login_btn.setText("로그인 중...")
            self.progress_bar.setVisible(True)
            self.status_label.setVisible(False)
        else:
            self.login_btn.setText("로그인")
            self.progress_bar.setVisible(False)
    
    def show_status_message(self, message, status_type="info"):
        """상태 메시지 표시"""
        self.status_label.setText(message)
        self.status_label.setVisible(True)
        
        if status_type == "error":
            self.status_label.setStyleSheet(f"color: {COLORS['error_500']};")
        elif status_type == "success":
            self.status_label.setStyleSheet(f"color: {COLORS['success_500']};")
        else:
            self.status_label.setStyleSheet(f"color: {COLORS['gray_600']};")
        
        # 3초 후 메시지 숨김
        QTimer.singleShot(3000, lambda: self.status_label.setVisible(False))
    
    def show_settings(self):
        """설정 화면 표시"""
        QMessageBox.information(self, "설정", "설정 기능은 메인 프로그램에서 이용하실 수 있습니다.")
    
    def show_help(self):
        """도움말 표시"""
        help_text = """
Web Ceph Auto Processor 로그인 도움말

• Web Ceph 계정 정보를 입력하세요
• 자동 로그인을 체크하면 다음번에 자동으로 로그인됩니다
• 문제가 있을 경우 설정에서 연결 정보를 확인하세요

문의사항이 있으시면 관리자에게 연락하세요.
        """
        QMessageBox.information(self, "도움말", help_text.strip())
    
    def keyPressEvent(self, event):
        """키보드 이벤트 처리"""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.terminate()
            self.login_worker.wait()
        event.accept() 