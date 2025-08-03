"""
자동화 모니터링 위젯
Use Case 문서의 자동화 프로세스를 실시간으로 모니터링하고 제어하는 위젯
"""

import time
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QPushButton, QProgressBar, QTextEdit,
                           QFrame, QScrollArea, QGroupBox, QListWidget,
                           QListWidgetItem, QSplitter, QMessageBox, 
                           QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, QMutex
from PyQt5.QtGui import QFont, QMovie, QPixmap, QColor

from .styles import COLORS
from ..utils.font_loader import font_loader
from ..automation.web_ceph_automation import WebCephAutomation
from ..config import config

class AutomationWorker(QThread):
    """자동화 작업을 실행하는 워커 스레드"""
    
    # 시그널 정의
    step_started = pyqtSignal(str, str)  # step_name, description
    step_completed = pyqtSignal(str, bool, str)  # step_name, success, message
    progress_updated = pyqtSignal(int)  # percentage
    log_message = pyqtSignal(str, str)  # message, level (info, warning, error)
    automation_finished = pyqtSignal(bool, str)  # success, final_message
    
    def __init__(self, patient_data, images):
        super().__init__()
        self.patient_data = patient_data
        self.images = images
        self.automation = WebCephAutomation()
        self.is_paused = False
        self.should_stop = False
        self.mutex = QMutex()
    
    def run(self):
        """자동화 프로세스 실행"""
        try:
            self.log_message.emit("자동화 프로세스를 시작합니다...", "info")
            
            steps = [
                ("browser_launch", "브라우저 실행", self.launch_browser),
                ("login", "Web Ceph 로그인", self.login_webceph),
                ("patient_register", "환자 등록", self.register_patient),
                ("image_upload", "이미지 업로드", self.upload_images),
                ("analysis_start", "분석 시작", self.start_analysis),
                ("analysis_wait", "분석 대기", self.wait_analysis),
                ("pdf_download", "PDF 다운로드", self.download_pdf),
                ("airtable_sync", "Airtable 동기화", self.sync_airtable)
            ]
            
            total_steps = len(steps)
            
            for i, (step_id, step_name, step_func) in enumerate(steps):
                if self.should_stop:
                    break
                
                # 일시정지 체크
                while self.is_paused and not self.should_stop:
                    self.msleep(100)
                
                if self.should_stop:
                    break
                
                # 단계 시작
                self.step_started.emit(step_id, step_name)
                
                try:
                    # 단계 실행
                    success, message = step_func()
                    
                    # 결과 처리
                    self.step_completed.emit(step_id, success, message)
                    
                    if not success:
                        self.automation_finished.emit(False, f"{step_name} 실패: {message}")
                        return
                    
                    # 진행률 업데이트
                    progress = int(((i + 1) / total_steps) * 100)
                    self.progress_updated.emit(progress)
                    
                except Exception as e:
                    error_msg = f"{step_name} 중 오류 발생: {str(e)}"
                    self.step_completed.emit(step_id, False, error_msg)
                    self.automation_finished.emit(False, error_msg)
                    return
            
            if not self.should_stop:
                self.automation_finished.emit(True, "모든 작업이 성공적으로 완료되었습니다!")
                
        except Exception as e:
            self.automation_finished.emit(False, f"예상치 못한 오류가 발생했습니다: {str(e)}")
    
    def launch_browser(self):
        """브라우저 실행"""
        self.log_message.emit("Chrome 브라우저를 실행합니다...", "info")
        self.msleep(2000)  # 시뮬레이션
        return True, "브라우저가 성공적으로 실행되었습니다"
    
    def login_webceph(self):
        """Web Ceph 로그인"""
        self.log_message.emit("Web Ceph에 로그인합니다...", "info")
        self.msleep(3000)  # 시뮬레이션
        return True, "로그인이 완료되었습니다"
    
    def register_patient(self):
        """환자 등록"""
        patient = self.patient_data
        self.log_message.emit(f"환자 '{patient['name']}'을(를) 등록합니다...", "info")
        self.msleep(2500)  # 시뮬레이션
        return True, f"환자 {patient['name']}이(가) 성공적으로 등록되었습니다"
    
    def upload_images(self):
        """이미지 업로드"""
        self.log_message.emit("X-ray 이미지를 업로드합니다...", "info")
        self.msleep(4000)  # 시뮬레이션
        
        self.log_message.emit("얼굴 사진을 업로드합니다...", "info")
        self.msleep(3000)  # 시뮬레이션
        
        return True, "모든 이미지가 성공적으로 업로드되었습니다"
    
    def start_analysis(self):
        """분석 시작"""
        self.log_message.emit("분석을 시작합니다...", "info")
        self.msleep(1500)  # 시뮬레이션
        return True, "분석이 시작되었습니다"
    
    def wait_analysis(self):
        """분석 대기"""
        self.log_message.emit("분석이 진행 중입니다. 완료까지 대기합니다...", "info")
        
        # 분석 대기 시뮬레이션 (30초)
        for i in range(30):
            if self.should_stop:
                return False, "작업이 중단되었습니다"
            
            while self.is_paused and not self.should_stop:
                self.msleep(100)
            
            self.msleep(1000)
            
            if i % 5 == 0:
                self.log_message.emit(f"분석 진행 중... ({i+1}/30초)", "info")
        
        return True, "분석이 완료되었습니다"
    
    def download_pdf(self):
        """PDF 다운로드"""
        self.log_message.emit("분석 결과 PDF를 다운로드합니다...", "info")
        self.msleep(3000)  # 시뮬레이션
        
        # 파일명 생성
        patient_name = self.patient_data['name']
        reg_num = self.patient_data['registration_number']
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{patient_name}_{reg_num}_{date_str}.pdf"
        
        return True, f"PDF 파일이 다운로드되었습니다: {filename}"
    
    def sync_airtable(self):
        """Airtable 동기화"""
        self.log_message.emit("Airtable에 결과를 동기화합니다...", "info")
        self.msleep(2000)  # 시뮬레이션
        return True, "Airtable 동기화가 완료되었습니다"
    
    def pause(self):
        """작업 일시정지"""
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()
    
    def resume(self):
        """작업 재개"""
        self.mutex.lock()
        self.is_paused = False
        self.mutex.unlock()
    
    def stop(self):
        """작업 중단"""
        self.mutex.lock()
        self.should_stop = True
        self.is_paused = False
        self.mutex.unlock()

class StepIndicatorWidget(QFrame):
    """단계 표시 위젯"""
    
    def __init__(self, step_id, step_name, description=""):
        super().__init__()
        self.step_id = step_id
        self.step_name = step_name
        self.description = description
        self.status = "pending"  # pending, active, completed, failed
        
        self.setup_ui()
        self.update_appearance()
    
    def setup_ui(self):
        """UI 설정"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # 상태 아이콘
        self.status_icon = QLabel("⏳")
        self.status_icon.setFont(font_loader.get_font('Regular', 20))
        self.status_icon.setFixedSize(32, 32)
        self.status_icon.setAlignment(Qt.AlignCenter)
        
        # 텍스트 영역
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self.title_label = QLabel(self.step_name)
        self.title_label.setFont(font_loader.get_font('SemiBold', 14))
        
        self.desc_label = QLabel(self.description)
        self.desc_label.setFont(font_loader.get_font('Regular', 12))
        self.desc_label.setWordWrap(True)
        
        text_layout.addWidget(self.title_label)
        if self.description:
            text_layout.addWidget(self.desc_label)
        
        layout.addWidget(self.status_icon)
        layout.addLayout(text_layout)
        layout.addStretch()
    
    def set_status(self, status, message=""):
        """상태 설정"""
        self.status = status
        if message:
            self.desc_label.setText(message)
        self.update_appearance()
    
    def update_appearance(self):
        """상태에 따른 외관 업데이트"""
        if self.status == "pending":
            self.status_icon.setText("⏳")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['gray_50']};
                    border: 1px solid {COLORS['gray_200']};
                    border-radius: 8px;
                }}
            """)
            self.title_label.setStyleSheet(f"color: {COLORS['gray_600']};")
            self.desc_label.setStyleSheet(f"color: {COLORS['gray_500']};")
            
        elif self.status == "active":
            self.status_icon.setText("🔄")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['primary_50']};
                    border: 2px solid {COLORS['primary_300']};
                    border-radius: 8px;
                }}
            """)
            self.title_label.setStyleSheet(f"color: {COLORS['primary_700']};")
            self.desc_label.setStyleSheet(f"color: {COLORS['primary_600']};")
            
        elif self.status == "completed":
            self.status_icon.setText("✅")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['white']};
                    border: 1px solid {COLORS['success_500']};
                    border-radius: 8px;
                }}
            """)
            self.title_label.setStyleSheet(f"color: {COLORS['success_500']};")
            self.desc_label.setStyleSheet(f"color: {COLORS['success_500']};")
            
        elif self.status == "failed":
            self.status_icon.setText("❌")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['white']};
                    border: 1px solid {COLORS['error_500']};
                    border-radius: 8px;
                }}
            """)
            self.title_label.setStyleSheet(f"color: {COLORS['error_500']};")
            self.desc_label.setStyleSheet(f"color: {COLORS['error_500']};")

class LogWidget(QFrame):
    """로그 위젯"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정"""
        self.setProperty("class", "card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 헤더
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("실행 로그")
        title_label.setFont(font_loader.get_font('SemiBold', 14))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        clear_btn = QPushButton("지우기")
        clear_btn.setFont(font_loader.get_font('Regular', 12))
        clear_btn.setProperty("class", "ghost")
        clear_btn.clicked.connect(self.clear_log)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        
        # 로그 텍스트
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(font_loader.get_font('Regular', 11))
        self.log_text.setMaximumHeight(200)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.log_text)
    
    def add_log(self, message, level="info"):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "error":
            color = COLORS['error_500']
            prefix = "❌"
        elif level == "warning":
            color = COLORS['warning_500']
            prefix = "⚠️"
        elif level == "success":
            color = COLORS['success_500']
            prefix = "✅"
        else:
            color = COLORS['gray_700']
            prefix = "ℹ️"
        
        formatted_message = f'<span style="color: {COLORS["gray_500"]}">[{timestamp}]</span> <span style="color: {color}">{prefix} {message}</span>'
        
        self.log_text.append(formatted_message)
        
        # 자동 스크롤
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()

class AutomationMonitorWidget(QWidget):
    """자동화 모니터링 메인 위젯"""
    
    def __init__(self):
        super().__init__()
        self.automation_worker = None
        self.step_widgets = {}
        self.is_running = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # 페이지 제목
        self.create_page_header(main_layout)
        
        # 메인 콘텐츠 영역
        self.create_main_content(main_layout)
        
        # 제어 버튼들
        self.create_control_buttons(main_layout)
    
    def create_page_header(self, layout):
        """페이지 헤더 생성"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("자동화 진행 상황")
        title_label.setFont(font_loader.get_font('Bold', 24))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        self.status_label = QLabel("대기 중...")
        self.status_label.setFont(font_loader.get_font('Regular', 14))
        self.status_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
    
    def create_main_content(self, layout):
        """메인 콘텐츠 영역 생성"""
        # 스플리터로 영역 분할
        splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 진행 단계
        self.create_progress_section(splitter)
        
        # 오른쪽: 로그
        self.create_log_section(splitter)
        
        # 비율 설정 (2:1)
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
    
    def create_progress_section(self, parent):
        """진행 상황 섹션 생성"""
        progress_widget = QFrame()
        progress_widget.setProperty("class", "card")
        
        layout = QVBoxLayout(progress_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 전체 진행률
        progress_header = QVBoxLayout()
        progress_header.setSpacing(8)
        
        progress_title = QLabel("전체 진행률")
        progress_title.setFont(font_loader.get_font('SemiBold', 16))
        progress_title.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimumHeight(8)
        self.overall_progress.setValue(0)
        
        self.progress_label = QLabel("0/8 단계 완료")
        self.progress_label.setFont(font_loader.get_font('Regular', 12))
        self.progress_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        
        progress_header.addWidget(progress_title)
        progress_header.addWidget(self.overall_progress)
        progress_header.addWidget(self.progress_label)
        
        # 단계별 진행 상황
        steps_title = QLabel("단계별 진행 상황")
        steps_title.setFont(font_loader.get_font('SemiBold', 14))
        steps_title.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        steps_container = QWidget()
        self.steps_layout = QVBoxLayout(steps_container)
        self.steps_layout.setSpacing(8)
        
        # 단계 위젯들 생성
        self.create_step_widgets()
        
        scroll_area.setWidget(steps_container)
        
        layout.addLayout(progress_header)
        layout.addWidget(steps_title)
        layout.addWidget(scroll_area)
        
        parent.addWidget(progress_widget)
    
    def create_step_widgets(self):
        """단계 위젯들 생성"""
        steps = [
            ("browser_launch", "브라우저 실행", "Chrome 브라우저를 실행합니다"),
            ("login", "Web Ceph 로그인", "Web Ceph 웹사이트에 로그인합니다"),
            ("patient_register", "환자 등록", "새 환자 정보를 등록합니다"),
            ("image_upload", "이미지 업로드", "X-ray와 얼굴 사진을 업로드합니다"),
            ("analysis_start", "분석 시작", "자동 분석을 시작합니다"),
            ("analysis_wait", "분석 대기", "분석 완료까지 대기합니다"),
            ("pdf_download", "PDF 다운로드", "분석 결과를 다운로드합니다"),
            ("airtable_sync", "Airtable 동기화", "결과를 Airtable에 저장합니다")
        ]
        
        for step_id, step_name, description in steps:
            step_widget = StepIndicatorWidget(step_id, step_name, description)
            self.step_widgets[step_id] = step_widget
            self.steps_layout.addWidget(step_widget)
        
        self.steps_layout.addStretch()
    
    def create_log_section(self, parent):
        """로그 섹션 생성"""
        self.log_widget = LogWidget()
        parent.addWidget(self.log_widget)
    
    def create_control_buttons(self, layout):
        """제어 버튼들 생성"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # 일시정지 버튼
        self.pause_btn = QPushButton("⏸️ 일시정지")
        self.pause_btn.setFont(font_loader.get_font('Medium', 14))
        self.pause_btn.setMinimumHeight(44)
        self.pause_btn.setProperty("class", "secondary")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_automation)
        
        # 중단 버튼
        self.stop_btn = QPushButton("⏹️ 중단")
        self.stop_btn.setFont(font_loader.get_font('Medium', 14))
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setProperty("class", "secondary")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_automation)
        
        # 재시작 버튼
        self.restart_btn = QPushButton("🔄 재시작")
        self.restart_btn.setFont(font_loader.get_font('Medium', 14))
        self.restart_btn.setMinimumHeight(44)
        self.restart_btn.setProperty("class", "ghost")
        self.restart_btn.setEnabled(False)
        self.restart_btn.clicked.connect(self.restart_automation)
        
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.restart_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def start_patient_process(self, patient_data, images):
        """환자 처리 프로세스 시작"""
        if self.is_running:
            QMessageBox.warning(self, "경고", "이미 실행 중인 작업이 있습니다.")
            return
        
        # 초기화
        self.reset_progress()
        
        # 워커 스레드 생성
        self.automation_worker = AutomationWorker(patient_data, images)
        
        # 시그널 연결
        self.automation_worker.step_started.connect(self.on_step_started)
        self.automation_worker.step_completed.connect(self.on_step_completed)
        self.automation_worker.progress_updated.connect(self.on_progress_updated)
        self.automation_worker.log_message.connect(self.on_log_message)
        self.automation_worker.automation_finished.connect(self.on_automation_finished)
        
        # 시작
        self.automation_worker.start()
        self.is_running = True
        
        # UI 상태 업데이트
        self.status_label.setText(f"환자 '{patient_data['name']}' 처리 중...")
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(False)
        
        self.log_widget.add_log(f"환자 '{patient_data['name']}' 자동화 프로세스를 시작합니다", "info")
    
    def reset_progress(self):
        """진행 상황 초기화"""
        self.overall_progress.setValue(0)
        self.progress_label.setText("0/8 단계 완료")
        
        for step_widget in self.step_widgets.values():
            step_widget.set_status("pending")
    
    def on_step_started(self, step_id, step_name):
        """단계 시작 처리"""
        if step_id in self.step_widgets:
            self.step_widgets[step_id].set_status("active", "진행 중...")
        
        self.log_widget.add_log(f"{step_name} 시작", "info")
    
    def on_step_completed(self, step_id, success, message):
        """단계 완료 처리"""
        if step_id in self.step_widgets:
            status = "completed" if success else "failed"
            self.step_widgets[step_id].set_status(status, message)
        
        level = "success" if success else "error"
        self.log_widget.add_log(message, level)
    
    def on_progress_updated(self, percentage):
        """진행률 업데이트"""
        self.overall_progress.setValue(percentage)
        completed_steps = int((percentage / 100) * 8)
        self.progress_label.setText(f"{completed_steps}/8 단계 완료 ({percentage}%)")
    
    def on_log_message(self, message, level):
        """로그 메시지 처리"""
        self.log_widget.add_log(message, level)
    
    def on_automation_finished(self, success, message):
        """자동화 완료 처리"""
        self.is_running = False
        
        # UI 상태 업데이트
        status_text = "완료" if success else "실패"
        self.status_label.setText(f"자동화 {status_text}")
        
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(True)
        
        # 최종 로그
        level = "success" if success else "error"
        self.log_widget.add_log(message, level)
        
        # 메시지 박스 표시
        if success:
            QMessageBox.information(self, "완료", message)
        else:
            QMessageBox.warning(self, "실패", message)
    
    def pause_automation(self):
        """자동화 일시정지"""
        if self.automation_worker and self.is_running:
            if self.pause_btn.text() == "⏸️ 일시정지":
                self.automation_worker.pause()
                self.pause_btn.setText("▶️ 재개")
                self.status_label.setText("일시정지됨")
                self.log_widget.add_log("자동화가 일시정지되었습니다", "warning")
            else:
                self.automation_worker.resume()
                self.pause_btn.setText("⏸️ 일시정지")
                self.status_label.setText("진행 중...")
                self.log_widget.add_log("자동화가 재개되었습니다", "info")
    
    def stop_automation(self):
        """자동화 중단"""
        if self.automation_worker and self.is_running:
            reply = QMessageBox.question(
                self,
                "중단 확인",
                "정말로 자동화 작업을 중단하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.automation_worker.stop()
                self.automation_worker.wait(3000)  # 3초 대기
                
                self.is_running = False
                self.status_label.setText("중단됨")
                self.pause_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self.restart_btn.setEnabled(True)
                
                self.log_widget.add_log("사용자에 의해 자동화가 중단되었습니다", "warning")
    
    def restart_automation(self):
        """자동화 재시작"""
        reply = QMessageBox.question(
            self,
            "재시작 확인",
            "처음부터 다시 시작하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 이전 데이터가 있다면 재사용, 없다면 새로 입력 요청
            main_window = self.window()
            main_window.navigate_to_page("patient_form")
    
    def check_status(self):
        """상태 체크 (외부에서 호출)"""
        return self.is_running
    
    def is_running(self):
        """실행 중인지 확인"""
        return self.is_running 