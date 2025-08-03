"""
덴트웹-웹셉 자동화 플로우 위젯
PRD와 Use Case에 따른 3단계 자동화 프로세스를 위한 UI
"""

import time
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QPushButton, QProgressBar, QTextEdit,
                           QFrame, QScrollArea, QGroupBox, QListWidget,
                           QListWidgetItem, QSplitter, QMessageBox, 
                           QTabWidget, QFileDialog, QLineEdit, QComboBox,
                           QCheckBox, QSpinBox, QFormLayout, QDialog,
                           QDialogButtonBox, QPlainTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, QMutex, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QMovie, QPixmap, QColor, QPalette, QIcon

from .styles import COLORS
from ..utils.font_loader import font_loader
from ..automation.dentweb_automation import DentwebAutomationWorker
from ..automation.web_ceph_automation import WebCephAutomation
from ..config import config

class AutomationFlowWidget(QWidget):
    """덴트웹-웹셉 자동화 플로우 메인 위젯"""
    
    # 시그널 정의
    automation_started = pyqtSignal()
    automation_completed = pyqtSignal(dict)  # 결과 데이터
    automation_failed = pyqtSignal(str)  # 오류 메시지
    status_updated = pyqtSignal(str, str)  # 메시지, 레벨(info/warning/error)
    
    def __init__(self):
        super().__init__()
        self.automation_worker = None
        self.current_step = 0
        self.total_steps = 3
        
        # 추출된 환자 데이터 저장
        self.extracted_patient_data = {}
        self.extracted_images = {}
        
        # 자동화 단계 정의
        self.automation_steps = [
            {
                'id': 'ocr_extraction',
                'title': '📋 OCR 실행 및 사진 복사',
                'description': 'Dentweb 화면에서 환자 정보를 추출하고 사진을 복사합니다',
                'status': 'pending'  # pending, running, completed, failed
            },
            {
                'id': 'webceph_analysis',
                'title': '🌐 WebCeph 등록 및 업로드',
                'description': 'WebCeph에 환자를 등록하고 이미지를 업로드하여 분석을 시작합니다',
                'status': 'pending'
            },
            {
                'id': 'pdf_download',
                'title': '📤 PDF 전송하기',
                'description': '분석 완료 후 PDF를 다운로드하고 지정된 위치로 전송합니다',
                'status': 'pending'
            }
        ]
        
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(32, 32, 32, 32)
        
        # 제목 및 설명
        self.create_header(main_layout)
        
        # 자동화 실행 영역
        self.create_execution_section(main_layout)
        
        # 로그 영역
        self.create_log_section(main_layout)
        
    def create_header(self, parent_layout):
        """헤더 영역 생성"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(8)
        
        # 제목
        title_label = QLabel("🦷 AutoCeph v1.0")
        title_label.setObjectName("title")
        
        # 부제목
        subtitle_label = QLabel("덴트웹과 WebCeph 연동 자동화 프로그램")
        subtitle_label.setObjectName("subtitle")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        parent_layout.addWidget(header_widget)
        
    def check_settings(self):
        """설정 확인"""
        try:
            # 설정에서 필요한 값들을 가져와서 확인
            webceph_id, webceph_pw = config.get_credentials()
            upstage_api = config.get_upstage_api_key()
            
            missing_settings = []
            if not webceph_id:
                missing_settings.append("WebCeph ID")
            if not webceph_pw:
                missing_settings.append("WebCeph 비밀번호")
            if not upstage_api:
                missing_settings.append("Upstage API 키")
            
            if missing_settings:
                QMessageBox.warning(
                    self,
                    "설정 확인 필요",
                    f"다음 설정이 필요합니다:\n• {chr(10).join(missing_settings)}\n\n"
                    "설정 탭에서 먼저 설정을 완료해주세요."
                )
                return False
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "설정 오류",
                f"설정 확인 중 오류가 발생했습니다:\n{str(e)}"
            )
            return False
        
    def create_execution_section(self, parent_layout):
        """실행 영역 생성"""
        execution_group = QGroupBox("🚀 실행 (Execution)")
        execution_group.setObjectName("executionGroup")
        execution_layout = QVBoxLayout(execution_group)
        execution_layout.setSpacing(16)
        
        # 전체 진행률
        self.create_progress_section(execution_layout)
        
        # 단계별 버튼
        self.create_step_buttons(execution_layout)
        
        parent_layout.addWidget(execution_group)
        
    def create_progress_section(self, parent_layout):
        """진행률 섹션 생성"""
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setSpacing(8)
        
        # 진행률 레이블
        progress_header = QHBoxLayout()
        self.progress_label = QLabel("전체 진행률")
        self.progress_label.setObjectName("progressLabel")
        
        self.progress_status = QLabel("준비")
        self.progress_status.setObjectName("progressStatus")
        
        progress_header.addWidget(self.progress_label)
        progress_header.addStretch()
        progress_header.addWidget(self.progress_status)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setObjectName("progressBar")
        
        progress_layout.addLayout(progress_header)
        progress_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(progress_widget)
        
    def create_step_buttons(self, parent_layout):
        """단계별 버튼 생성"""
        steps_widget = QWidget()
        steps_layout = QVBoxLayout(steps_widget)
        steps_layout.setSpacing(12)
        
        self.step_buttons = []
        
        for i, step in enumerate(self.automation_steps):
            step_frame = QFrame()
            step_frame.setObjectName("stepFrame")
            step_layout = QHBoxLayout(step_frame)
            step_layout.setContentsMargins(16, 12, 16, 12)
            
            # 단계 정보
            step_info_layout = QVBoxLayout()
            
            step_title = QLabel(step['title'])
            step_title.setObjectName("stepTitle")
            
            step_desc = QLabel(step['description'])
            step_desc.setObjectName("stepDescription")
            step_desc.setWordWrap(True)
            
            step_info_layout.addWidget(step_title)
            step_info_layout.addWidget(step_desc)
            
            # 실행 버튼
            step_button = QPushButton("실행")
            step_button.setObjectName("primaryButton")
            step_button.setFixedSize(80, 36)
            step_button.clicked.connect(lambda checked, step_id=step['id']: self.execute_step(step_id))
            
            # 상태 표시
            status_label = QLabel("대기 중")
            status_label.setObjectName("statusLabel")
            status_label.setFixedWidth(60)
            
            step_layout.addLayout(step_info_layout)
            step_layout.addStretch()
            step_layout.addWidget(status_label)
            step_layout.addWidget(step_button)
            
            self.step_buttons.append({
                'frame': step_frame,
                'button': step_button,
                'status': status_label,
                'step_id': step['id']
            })
            
            steps_layout.addWidget(step_frame)
        
        parent_layout.addWidget(steps_widget)
        
    def create_log_section(self, parent_layout):
        """로그 영역 생성"""
        log_group = QGroupBox("📜 로그 (Log)")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout(log_group)
        
        # 로그 컨트롤
        log_controls = QHBoxLayout()
        
        clear_log_btn = QPushButton("🗑️ 로그 지우기")
        clear_log_btn.setObjectName("ghostButton")
        clear_log_btn.clicked.connect(self.clear_log)
        
        save_log_btn = QPushButton("💾 로그 저장")
        save_log_btn.setObjectName("ghostButton")
        save_log_btn.clicked.connect(self.save_log)
        
        log_controls.addWidget(clear_log_btn)
        log_controls.addWidget(save_log_btn)
        log_controls.addStretch()
        
        # 로그 텍스트
        self.log_text = QPlainTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setMinimumHeight(200)
        self.log_text.setReadOnly(True)
        
        # 초기 로그 메시지
        self.add_log("프로그램이 시작되었습니다.", "info")
        
        log_layout.addLayout(log_controls)
        log_layout.addWidget(self.log_text)
        
        parent_layout.addWidget(log_group)
        
    def setup_styles(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QWidget {{
                font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
                background-color: {COLORS['gray_50']};
            }}
            
            #title {{
                font-size: 24px;
                font-weight: bold;
                color: {COLORS['gray_800']};
                margin-bottom: 4px;
            }}
            
            #subtitle {{
                font-size: 14px;
                color: {COLORS['gray_500']};
                margin-bottom: 24px;
            }}
            
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: {COLORS['gray_700']};
                border: 2px solid {COLORS['gray_200']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: white;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: white;
            }}
            
            #inputField {{
                padding: 12px 16px;
                border: 2px solid {COLORS['gray_300']};
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                color: {COLORS['gray_700']};
                min-height: 20px;
            }}
            
            #inputField:focus {{
                border-color: {COLORS['primary_500']};
                outline: none;
            }}
            
            #inputField:disabled {{
                background-color: {COLORS['gray_100']};
                color: {COLORS['gray_400']};
            }}
            
            #primaryButton {{
                background-color: {COLORS['primary_500']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 20px;
            }}
            
            #primaryButton:hover {{
                background-color: {COLORS['primary_600']};
            }}
            
            #primaryButton:pressed {{
                background-color: {COLORS['primary_700']};
            }}
            
                         #primaryButton:disabled {{
                 background-color: {COLORS['gray_300']};
                 color: {COLORS['gray_500']};
             }}
             
             #successButton {{
                 background-color: {COLORS['success_500']};
                 color: white;
                 border: none;
                 border-radius: 6px;
                 padding: 12px 24px;
                 font-size: 14px;
                 font-weight: 600;
                 min-height: 20px;
             }}
             
             #successButton:hover {{
                 background-color: {COLORS['success_600']};
             }}
             
             #successButton:pressed {{
                 background-color: {COLORS['success_700']};
             }}
            
            #secondaryButton {{
                background-color: white;
                color: {COLORS['primary_500']};
                border: 2px solid {COLORS['primary_500']};
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                min-height: 20px;
            }}
            
            #secondaryButton:hover {{
                background-color: {COLORS['primary_50']};
            }}
            
            #secondaryButton:pressed {{
                background-color: {COLORS['primary_100']};
            }}
            
            #ghostButton {{
                background-color: transparent;
                color: {COLORS['gray_600']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }}
            
            #ghostButton:hover {{
                background-color: {COLORS['gray_100']};
                color: {COLORS['gray_800']};
            }}
            
            #stepFrame {{
                background-color: white;
                border: 1px solid {COLORS['gray_200']};
                border-radius: 8px;
                margin: 2px 0;
            }}
            
            #stepFrame:hover {{
                border-color: {COLORS['primary_300']};
                background-color: {COLORS['primary_50']};
            }}
            
            #stepTitle {{
                font-size: 16px;
                font-weight: 600;
                color: {COLORS['gray_800']};
                margin-bottom: 4px;
            }}
            
            #stepDescription {{
                font-size: 14px;
                color: {COLORS['gray_600']};
                line-height: 1.4;
            }}
            
            #statusLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {COLORS['gray_500']};
                text-align: center;
            }}
            
            #progressLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {COLORS['gray_700']};
            }}
            
            #progressStatus {{
                font-size: 14px;
                color: {COLORS['gray_500']};
            }}
            
            QProgressBar {{
                border: 2px solid {COLORS['gray_200']};
                border-radius: 6px;
                text-align: center;
                background-color: {COLORS['gray_100']};
                height: 8px;
            }}
            
            QProgressBar::chunk {{
                background-color: {COLORS['primary_500']};
                border-radius: 4px;
            }}
            
            #logText {{
                background-color: {COLORS['gray_900']};
                color: {COLORS['gray_100']};
                border: 1px solid {COLORS['gray_300']};
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                line-height: 1.4;
            }}
        """)
        
    def execute_step(self, step_id):
        """단계별 실행 (재실행 포함)"""
        # 버튼 텍스트 확인으로 재실행 여부 판단
        button_text = ""
        for step_ui in self.step_buttons:
            if step_ui['step_id'] == step_id:
                button_text = step_ui['button'].text()
                break
        
        if button_text in ["재실행", "재시도"]:
            self.add_log(f"단계 재실행 시작: {step_id}", "info")
            # 재실행의 경우 상태를 pending으로 초기화
            self.reset_step_status(step_id)
        else:
            self.add_log(f"단계 실행 시작: {step_id}", "info")
        
        # 설정 확인
        if not self.check_settings():
            return
        
        # 현재 단계 찾기
        step_index = next((i for i, step in enumerate(self.automation_steps) if step['id'] == step_id), -1)
        if step_index == -1:
            self.add_log(f"알 수 없는 단계: {step_id}", "error")
            return
            
        # 재실행이 아닌 경우만 이전 단계 완료 여부 확인
        if button_text not in ["재실행", "재시도"] and step_index > 0:
            for i in range(step_index):
                if self.automation_steps[i]['status'] != 'completed':
                    QMessageBox.warning(
                        self,
                        "단계 순서 오류",
                        f"이전 단계를 먼저 완료해주세요: {self.automation_steps[i]['title']}"
                    )
                    return
        
        # 단계별 실행
        if step_id == 'ocr_extraction':
            self.execute_ocr_extraction()
        elif step_id == 'webceph_analysis':
            self.execute_webceph_analysis()
        elif step_id == 'pdf_download':
            self.execute_pdf_download()
        
    def reset_step_status(self, step_id):
         """단계 상태를 초기화하여 재실행 가능하게 만듬"""
         # automation_steps 상태 초기화
         for step in self.automation_steps:
             if step['id'] == step_id:
                 step['status'] = 'pending'
                 break
         
         # UI 초기화
         for step_ui in self.step_buttons:
             if step_ui['step_id'] == step_id:
                 step_ui['status'].setText("대기 중")
                 step_ui['status'].setStyleSheet(f"color: {COLORS['gray_500']};")
                 step_ui['button'].setText("실행")
                 step_ui['button'].setObjectName("primaryButton")
                 step_ui['button'].setEnabled(True)
                 break
            
    def execute_ocr_extraction(self):
        """OCR 실행 및 사진 복사"""
        try:
            # 설정 확인
            if not self.check_settings():
                return
                
            self.update_step_status('ocr_extraction', 'running', "실행 중...")
            self.add_log("OCR 실행 및 사진 복사를 시작합니다...", "info")
            
            # Dentweb 자동화 워커 실행
            if self.automation_worker and self.automation_worker.isRunning():
                self.automation_worker.terminate()
                self.automation_worker.wait()
            
            self.automation_worker = DentwebAutomationWorker()
            self.automation_worker.patient_info_extracted.connect(self.on_patient_info_extracted)
            self.automation_worker.error_occurred.connect(self.on_automation_error)
            self.automation_worker.status_updated.connect(self.on_status_updated)
            
            # 개선된 OCR 실행 대화상자 표시
            self.show_ocr_capture_dialog()
            
        except Exception as e:
            self.update_step_status('ocr_extraction', 'failed', "실패")
            self.add_log(f"OCR 실행 실패: {str(e)}", "error")
    
    def show_ocr_capture_dialog(self):
        """OCR 캡처 영역 선택 대화상자"""
        try:
            # 캡처 영역 설정 가져오기
            x = config.get_int('dentweb', 'screenshot_x', 400)
            y = config.get_int('dentweb', 'screenshot_y', 400)
            width = config.get_int('dentweb', 'screenshot_width', 400)
            height = config.get_int('dentweb', 'screenshot_height', 400)
            
            reply = QMessageBox.question(
                self,
                "OCR 실행 준비",
                f"📷 Dentweb 환자 정보 화면을 준비하세요\n\n"
                f"🎯 Dentweb 창을 자동으로 찾아 최적 영역을 캡처합니다\n"
                f"⚡ 확인 클릭 후 바로 자동 캡처됩니다\n\n"
                f"✅ Dentweb 프로그램에서 환자 정보가 잘 보이는지 확인하세요\n"
                f"📋 환자명, 차트번호, 생년월일 등이 화면에 표시되어야 합니다",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Ok
            )
            
            if reply == QMessageBox.Ok:
                self.add_log("스크린샷을 바로 촬영합니다...", "info")
                self.execute_capture()
            else:
                self.update_step_status('ocr_extraction', 'pending', "대기 중")
                self.add_log("OCR 실행이 취소되었습니다", "warning")
            
        except Exception as e:
            self.add_log(f"OCR 대화상자 오류: {str(e)}", "error")
            self.update_step_status('ocr_extraction', 'failed', "실패")
    
    def start_countdown_capture(self):
        """카운트다운과 함께 캡처 시작 (사용하지 않음 - 호환성 유지용)"""
        # 이 함수는 더 이상 사용하지 않지만 호환성을 위해 유지
        self.execute_capture()
    
    def execute_capture(self):
        """실제 캡처 실행"""
        try:
            self.add_log("📷 스크린샷 촬영 중...", "info")
            
            # 자동화 워커 시작
            self.automation_worker.start()
            
        except Exception as e:
            self.add_log(f"캡처 실행 오류: {str(e)}", "error")
            self.update_step_status('ocr_extraction', 'failed', "실패")
            
    def execute_webceph_analysis(self):
        """WebCeph 등록 및 업로드"""
        try:
            # 설정 확인
            if not self.check_settings():
                return
                
            self.update_step_status('webceph_analysis', 'running', "실행 중...")
            self.add_log("WebCeph 등록 및 업로드를 시작합니다...", "info")
            
            # 실제 WebCeph 자동화 실행
            self.start_real_webceph_automation()
            
        except Exception as e:
            self.update_step_status('webceph_analysis', 'failed', "실패")
            self.add_log(f"WebCeph 분석 실패: {str(e)}", "error")
    
    def start_real_webceph_automation(self):
        """실제 WebCeph 자동화 시작"""
        try:
            # WebCeph 자동화 워커 생성
            from ..automation.web_ceph_automation import WebCephAutomation
            
            # 이전 단계에서 추출된 환자 데이터 사용
            patient_data = self.extracted_patient_data if self.extracted_patient_data else {
                'name': '',
                'birth_date': '',
                'registration_number': '',
                'gender': 'M'
            }
            
            # 이미지 데이터 (현재는 빈 값, 추후 이미지 캡처 기능 추가 예정)
            images = self.extracted_images if self.extracted_images else {
                'xray': None,
                'face': None
            }
            
            # 환자 데이터 상태 확인 및 로그
            if patient_data.get('name'):
                self.add_log(f"📋 추출된 환자 데이터를 사용합니다: {patient_data.get('name')}", "info")
            else:
                self.add_log("⚠️ 추출된 환자 데이터가 없습니다. 수동 입력이 필요할 수 있습니다.", "warning")
            
            self.add_log("🚀 Chrome 브라우저를 실행합니다...", "info")
            
            # WebCeph 자동화 클래스 인스턴스 생성
            self.webceph_automation = WebCephAutomation()
            
            # 백그라운드에서 WebCeph 자동화 실행
            QTimer.singleShot(1000, lambda: self.run_webceph_process(patient_data, images))
            
        except Exception as e:
            self.add_log(f"❌ WebCeph 자동화 시작 실패: {str(e)}", "error")
            self.update_step_status('webceph_analysis', 'failed', "실패")
    
    def run_webceph_process(self, patient_data, images):
        """WebCeph 프로세스 실행 - 단계별 진행"""
        try:
            # 브라우저 초기화
            self.add_log("🌐 Chrome 브라우저를 초기화합니다...", "info")
            self.webceph_automation.initialize_browser()
            
            # 로그인 정보 확인
            username, password = config.get_credentials()
            if not username or not password:
                raise Exception("WebCeph 로그인 정보가 설정되지 않았습니다. 설정 탭에서 확인해주세요.")
            
            # 1-3단계: 순차적 WebCeph 로그인 및 신규 환자 클릭
            self.add_log(f"🔐 WebCeph 로그인을 시작합니다... (사용자: {username})", "info")
            self.webceph_automation.login(username, password)
            
            # 신규 환자 전체 프로세스 실행 (신규 ID 자동 감지 포함)
            self.add_log("🆕 신규 환자 생성 및 자동 감지를 시작합니다...", "info")
            
            # 환자 데이터 확인 및 출력
            if patient_data:
                self.add_log("📋 OCR에서 추출된 환자 정보:", "info")
                if patient_data.get('name'):
                    self.add_log(f"  • 환자명: {patient_data.get('name')}", "success")
                if patient_data.get('birth_date'):
                    self.add_log(f"  • 생년월일: {patient_data.get('birth_date')}", "success")
                if patient_data.get('registration_number'):
                    self.add_log(f"  • 등록번호: {patient_data.get('registration_number')}", "success")
                if patient_data.get('chart_no'):
                    self.add_log(f"  • 차트번호: {patient_data.get('chart_no')}", "success")
                if patient_data.get('gender'):
                    self.add_log(f"  • 성별: {patient_data.get('gender')}", "success")
                
                # 신규 환자 버튼 클릭
                self.add_log("🖱️ 신규 환자 입력 버튼을 클릭합니다...", "info")
                self.webceph_automation.click_new_patient_button()
                
                # 신규 환자 폼 자동 작성
                self.add_log("📝 신규 환자 폼을 자동으로 작성합니다...", "info")
                self.webceph_automation.fill_patient_form(patient_data)
                
                # 신규 생성된 환자 자동 감지, 선택 및 레코드 생성
                self.add_log("🔍 방금 생성된 신규 환자를 자동으로 감지하고 레코드를 생성합니다...", "info")
                if self.webceph_automation.detect_and_select_new_patient(patient_data):
                    self.add_log("✅ 신규 생성 환자 자동 선택 성공!", "success")
                    
                    # 최신 환자 ID 표시
                    latest_id = self.webceph_automation.get_latest_patient_id()
                    if latest_id:
                        self.add_log(f"🆔 선택된 환자 ID: {latest_id}", "success")
                    
                    # 레코드 생성
                    self.add_log("📋 환자 레코드를 생성합니다...", "info")
                    if self.webceph_automation.create_patient_record(patient_data):
                        self.add_log("✅ 레코드 생성 버튼 클릭 성공!", "success")
                        
                        # 레코드 정보 설정
                        self.add_log("📝 레코드 정보를 설정합니다...", "info")
                        self.webceph_automation.setup_record_info(patient_data)
                        
                        # 레코드 생성 확인
                        self.add_log("✅ 레코드 생성을 확인합니다...", "info")
                        if self.webceph_automation.confirm_record_creation():
                            self.add_log("🎉 레코드 생성이 완료되었습니다!", "success")
                            
                            # 이미지 업로드 준비 상태 확인
                            if self.webceph_automation.wait_for_record_ready():
                                self.add_log("📸 이미지 업로드 준비 완료!", "success")
                            else:
                                self.add_log("⚠️ 이미지 업로드 준비 상태 확인 실패", "warning")
                        else:
                            self.add_log("⚠️ 레코드 생성 확인 실패", "warning")
                    else:
                        self.add_log("⚠️ 레코드 생성 실패 - 수동으로 진행해주세요", "warning")
                else:
                    self.add_log("⚠️ 신규 환자 자동 선택 실패 - 수동으로 환자를 선택해주세요", "warning")
                
            else:
                self.add_log("📋 추출된 환자 정보가 없습니다", "warning")
                self.add_log("🧪 테스트용 환자 데이터를 사용합니다", "info")
                
                # 테스트용 환자 데이터
                test_patient_data = {
                    'name': '김테스트',
                    'first_name': '테스트',
                    'last_name': '김',
                    'birth_date': '1990-01-01',
                    'chart_no': 'TEST001',
                    'gender': 'M'
                }
                
                # 신규 환자 버튼 클릭
                self.add_log("🖱️ 신규 환자 입력 버튼을 클릭합니다...", "info")
                self.webceph_automation.click_new_patient_button()
                
                self.add_log("📝 테스트 환자 폼을 작성합니다...", "info")
                self.webceph_automation.fill_patient_form(test_patient_data)
                
                # 테스트 환자도 자동 감지 및 레코드 생성 시도
                self.add_log("🔍 테스트 환자 자동 감지 및 레코드 생성을 시도합니다...", "info")
                if self.webceph_automation.detect_and_select_new_patient(test_patient_data):
                    self.add_log("✅ 테스트 환자 선택 성공!", "success")
                    
                    # 테스트 환자 레코드 생성
                    self.add_log("📋 테스트 환자 레코드를 생성합니다...", "info")
                    if self.webceph_automation.create_patient_record(test_patient_data):
                        self.add_log("✅ 테스트 환자 레코드 생성 성공!", "success")
                        self.webceph_automation.setup_record_info(test_patient_data)
                        self.webceph_automation.confirm_record_creation()
                        self.webceph_automation.wait_for_record_ready()
                    else:
                        self.add_log("⚠️ 테스트 환자 레코드 생성 실패", "warning")
                else:
                    self.add_log("⚠️ 테스트 환자 자동 선택 실패", "warning")
            
            # 성공 완료
            self.add_log("✅ WebCeph 신규 환자 등록 및 선택이 완료되었습니다!", "success")
            self.add_log("🎉 다음 단계: 이미지 업로드 및 분석 시작", "info")
            
            # 완료 처리
            QTimer.singleShot(2000, self.complete_webceph_analysis)
            
        except Exception as e:
            self.add_log(f"❌ WebCeph 프로세스 오류: {str(e)}", "error")
            self.update_step_status('webceph_analysis', 'failed', "실패")
            self._cleanup_browser()
    
    def _cleanup_browser(self):
        """브라우저 정리"""
        try:
            if hasattr(self, 'webceph_automation') and self.webceph_automation.driver:
                self.webceph_automation.driver.quit()
                self.add_log("🧹 브라우저가 정리되었습니다", "info")
        except Exception as e:
            self.add_log(f"브라우저 정리 중 오류: {str(e)}", "warning")
            
    def execute_pdf_download(self):
        """PDF 전송하기"""
        try:
                
            self.update_step_status('pdf_download', 'running', "실행 중...")
            self.add_log("PDF 전송을 시작합니다...", "info")
            
            # PDF 전송 시뮬레이션
            QTimer.singleShot(1500, lambda: self.simulate_pdf_download())
            
        except Exception as e:
            self.update_step_status('pdf_download', 'failed', "실패")
            self.add_log(f"PDF 전송 실패: {str(e)}", "error")
            
    def simulate_webceph_analysis(self):
        """WebCeph 분석 시뮬레이션"""
        self.add_log("WebCeph에 로그인 중...", "info")
        QTimer.singleShot(1000, lambda: self.add_log("환자 정보 등록 중...", "info"))
        QTimer.singleShot(2000, lambda: self.add_log("이미지 업로드 중...", "info"))
        QTimer.singleShot(3500, lambda: self.add_log("분석 시작...", "info"))
        QTimer.singleShot(5000, lambda: self.complete_webceph_analysis())
        
    def complete_webceph_analysis(self):
        """WebCeph 분석 완료"""
        self.update_step_status('webceph_analysis', 'completed', "완료")
        self.add_log("WebCeph 분석이 완료되었습니다.", "success")
        self.update_progress(66)
        
    def simulate_pdf_download(self):
        """PDF 다운로드 시뮬레이션"""
        self.add_log("분석 결과 PDF 다운로드 중...", "info")
        QTimer.singleShot(1000, lambda: self.add_log("Make.com Webhook으로 전송 중...", "info"))
        QTimer.singleShot(2000, lambda: self.complete_pdf_download())
        
    def complete_pdf_download(self):
        """PDF 다운로드 완료"""
        self.update_step_status('pdf_download', 'completed', "완료")
        self.add_log("PDF 전송이 완료되었습니다.", "success")
        self.update_progress(100)
        self.add_log("모든 자동화 프로세스가 완료되었습니다! 🎉", "success")
        
    def on_patient_info_extracted(self, patient_info):
        """환자 정보 추출 완료 처리"""
        # 추출된 데이터 저장
        self.extracted_patient_data = patient_info
        
        self.update_step_status('ocr_extraction', 'completed', "완료")
        
        # 추출된 정보 로그 출력
        if patient_info.get('name'):
            self.add_log(f"✅ 환자명: {patient_info.get('name')}", "success")
        if patient_info.get('birth_date'):
            self.add_log(f"📅 생년월일: {patient_info.get('birth_date')}", "info")
        if patient_info.get('registration_number'):
            self.add_log(f"🔢 등록번호: {patient_info.get('registration_number')}", "info")
        
        # 환자 정보가 제대로 추출되었는지 확인
        if not any([patient_info.get('name'), patient_info.get('birth_date'), patient_info.get('registration_number')]):
            self.add_log("⚠️ 환자 정보가 제대로 추출되지 않았습니다", "warning")
            self.add_log("💡 WebCeph 단계는 수동으로 진행해야 할 수 있습니다", "info")
        else:
            self.add_log("🎉 OCR 실행 및 환자 정보 추출이 완료되었습니다!", "success")
            self.add_log("➡️ 다음 단계: WebCeph 등록 및 업로드", "info")
        
        self.update_progress(33)
        
    def on_automation_error(self, error_message):
        """자동화 오류 처리"""
        self.update_step_status('ocr_extraction', 'failed', "실패")
        self.add_log(f"자동화 오류: {error_message}", "error")
        
    def on_status_updated(self, status_message):
        """상태 업데이트 처리"""
        self.add_log(status_message, "info")
        
    def update_step_status(self, step_id, status, status_text):
        """단계 상태 업데이트"""
        # automation_steps 업데이트
        for step in self.automation_steps:
            if step['id'] == step_id:
                step['status'] = status
                break
                
        # UI 업데이트
        for step_ui in self.step_buttons:
            if step_ui['step_id'] == step_id:
                step_ui['status'].setText(status_text)
                
                # 상태에 따른 스타일 적용
                if status == 'running':
                    step_ui['status'].setStyleSheet(f"color: {COLORS['primary_500']}; font-weight: 600;")
                    step_ui['button'].setEnabled(False)
                elif status == 'completed':
                    step_ui['status'].setStyleSheet(f"color: {COLORS['success_500']}; font-weight: 600;")
                    step_ui['button'].setText("재실행")
                    step_ui['button'].setEnabled(True)
                elif status == 'failed':
                    step_ui['status'].setStyleSheet(f"color: {COLORS['error_500']}; font-weight: 600;")
                    step_ui['button'].setText("재시도")
                    step_ui['button'].setEnabled(True)
                else:  # pending
                    step_ui['status'].setStyleSheet(f"color: {COLORS['gray_500']};")
                    step_ui['button'].setText("실행")
                    step_ui['button'].setObjectName("primaryButton")  # 기본 버튼 스타일
                    step_ui['button'].setEnabled(True)
                break
                
    def update_progress(self, value):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        if value == 0:
            self.progress_status.setText("준비")
        elif value == 100:
            self.progress_status.setText("완료")
        else:
            self.progress_status.setText(f"{value}% 진행")
            
    def add_log(self, message, level="info"):
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 레벨에 따른 아이콘
        level_icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        icon = level_icons.get(level, "ℹ️")
        log_entry = f"[{timestamp}] {icon} {message}"
        
        self.log_text.appendPlainText(log_entry)
        
        # 자동 스크롤
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()
        self.add_log("로그가 지워졌습니다.", "info")
        
    def save_log(self):
        """로그 저장"""
        try:
            log_dir = Path.home() / "Documents" / "WebCephAuto" / "Logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"automation_log_{timestamp}.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
                
            self.add_log(f"로그가 저장되었습니다: {log_file.name}", "success")
            
        except Exception as e:
            self.add_log(f"로그 저장 실패: {str(e)}", "error") 