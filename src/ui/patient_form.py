"""
환자 정보 입력 폼 위젯
Use Case 문서의 환자 등록 프로세스를 구현하며 단계별 진행과 실시간 검증을 제공
"""

import os
import re
from datetime import datetime, date
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QLineEdit, QPushButton, QComboBox, 
                           QDateEdit, QTextEdit, QFileDialog, QTabWidget,
                           QFrame, QScrollArea, QGroupBox, QCheckBox,
                           QProgressBar, QListWidget, QListWidgetItem,
                           QSplitter, QMessageBox, QDialog, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer, QThread
from PyQt5.QtGui import QPixmap, QFont, QMovie

from .styles import COLORS
from ..utils.font_loader import font_loader
from ..config import config
from ..automation.dentweb_automation import DentwebAutomationWorker

class ValidationMixin:
    """입력 검증 믹스인 클래스"""
    
    @staticmethod
    def validate_name(name):
        """이름 검증"""
        if not name or len(name.strip()) < 2:
            return False, "이름은 2자 이상 입력해주세요"
        if len(name.strip()) > 50:
            return False, "이름은 50자 이하로 입력해주세요"
        # 한글, 영문, 공백만 허용
        if not re.match(r'^[가-힣a-zA-Z\s]+$', name.strip()):
            return False, "이름은 한글 또는 영문만 입력 가능합니다"
        return True, ""
    
    @staticmethod
    def validate_registration_number(reg_num):
        """등록번호 검증"""
        if not reg_num or len(reg_num.strip()) < 6:
            return False, "등록번호는 6자 이상 입력해주세요"
        if len(reg_num.strip()) > 20:
            return False, "등록번호는 20자 이하로 입력해주세요"
        # 숫자와 문자만 허용
        if not re.match(r'^[a-zA-Z0-9]+$', reg_num.strip()):
            return False, "등록번호는 영문과 숫자만 입력 가능합니다"
        return True, ""
    
    @staticmethod
    def validate_phone(phone):
        """전화번호 검증 (선택사항)"""
        if not phone:
            return True, ""  # 선택사항이므로 빈 값 허용
        # 하이픈 제거 후 검증
        clean_phone = phone.replace("-", "").replace(" ", "")
        if not re.match(r'^01[0-9]{8,9}$', clean_phone):
            return False, "올바른 휴대폰 번호를 입력해주세요 (예: 010-1234-5678)"
        return True, ""
    
    @staticmethod
    def validate_birth_date(birth_date):
        """생년월일 검증"""
        try:
            # QDate를 Python date로 변환
            if hasattr(birth_date, 'toPyDate'):
                birth_py_date = birth_date.toPyDate()
            else:
                birth_py_date = birth_date
            
            today = date.today()
            if birth_py_date > today:
                return False, "생년월일은 오늘 이전 날짜여야 합니다"
            
            # 150세 이상은 불가
            age = today.year - birth_py_date.year
            if age > 150:
                return False, "생년월일을 다시 확인해주세요"
            
            return True, ""
        except Exception:
            return False, "올바른 날짜를 입력해주세요"

class PatientInfoWidget(QFrame, ValidationMixin):
    """환자 정보 입력 위젯"""
    
    form_validated = pyqtSignal(bool, dict)  # is_valid, patient_data
    
    def __init__(self):
        super().__init__()
        self.patient_data = {}
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_form)
        
        self.setup_ui()
        self.setup_validation()
    
    def setup_ui(self):
        """UI 설정"""
        self.setProperty("class", "card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 제목
        title_label = QLabel("환자 정보 입력")
        title_label.setFont(font_loader.get_font('SemiBold', 18))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        # 폼 그리드
        form_layout = QGridLayout()
        form_layout.setSpacing(16)
        form_layout.setColumnStretch(1, 1)
        
        # 이름 (필수)
        self.create_form_field(form_layout, 0, "이름 *", "name_input", "환자 이름을 입력하세요")
        
        # 생년월일 (필수)
        birth_label = QLabel("생년월일 *")
        birth_label.setFont(font_loader.get_font('Medium', 12))
        birth_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setDate(QDate.currentDate().addYears(-30))
        self.birth_date_input.setMaximumDate(QDate.currentDate())
        self.birth_date_input.setMinimumDate(QDate(1900, 1, 1))
        self.birth_date_input.setDisplayFormat("yyyy-MM-dd")
        self.birth_date_input.setFont(font_loader.get_font('Regular', 14))
        self.birth_date_input.setMinimumHeight(44)
        
        form_layout.addWidget(birth_label, 1, 0)
        form_layout.addWidget(self.birth_date_input, 1, 1)
        
        # 등록번호 (필수)
        self.create_form_field(form_layout, 2, "등록번호 *", "reg_num_input", "환자 등록번호를 입력하세요")
        
        # 성별 (필수)
        gender_label = QLabel("성별 *")
        gender_label.setFont(font_loader.get_font('Medium', 12))
        gender_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        
        self.gender_input = QComboBox()
        self.gender_input.addItems(["선택하세요", "남성", "여성"])
        self.gender_input.setFont(font_loader.get_font('Regular', 14))
        self.gender_input.setMinimumHeight(44)
        
        form_layout.addWidget(gender_label, 3, 0)
        form_layout.addWidget(self.gender_input, 3, 1)
        
        # 연락처 (선택)
        self.create_form_field(form_layout, 4, "연락처", "phone_input", "010-1234-5678")
        
        # 이메일 (선택)
        self.create_form_field(form_layout, 5, "이메일", "email_input", "patient@example.com")
        
        # 특이사항 (선택)
        notes_label = QLabel("특이사항")
        notes_label.setFont(font_loader.get_font('Medium', 12))
        notes_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("환자의 특이사항이나 참고사항을 입력하세요")
        self.notes_input.setFont(font_loader.get_font('Regular', 14))
        self.notes_input.setMaximumHeight(80)
        
        form_layout.addWidget(notes_label, 6, 0, Qt.AlignTop)
        form_layout.addWidget(self.notes_input, 6, 1)
        
        # 개인정보 이용 동의 체크박스 (필수)
        consent_layout = QHBoxLayout()
        self.consent_checkbox = QCheckBox()
        self.consent_checkbox.setFont(font_loader.get_font('Regular', 12))
        
        consent_text = QLabel("의사회원의 웹엠 서비스 이용을 위한 안내문\n\n"
                             "회원이 웹엠 서비스 이용을 위해 회원이 운영하는 병원, 의원 등 개인정보취급 자(이하 \"관자\")의 개인정보를 이용하는 경우, 의원은 개인정보 처리방침에 따라 다음과 같이 개인정보를 처리, 위탁하고자 합니다.\n\n"
                             "중요한 내용이오니, 반드시 숙지하시기 바랍니다.\n\n"
                             "1. 개인정보 수집, 이용 등의 목적 의무\n\n"
                             "회원이 환자정보를 환자로부터 수집하는 경우, 관련규정에 대해 리 절차를 생각 하거나, 엔지 시 인정보 처리방침에 따라 다음과 같은 개인정보를 처리 조건이 됩니다.")
        consent_text.setFont(font_loader.get_font('Regular', 10))
        consent_text.setStyleSheet(f"color: {COLORS['gray_600']}; background-color: {COLORS['gray_50']}; padding: 12px; border: 1px solid {COLORS['gray_200']}; border-radius: 4px;")
        consent_text.setWordWrap(True)
        consent_text.setMaximumHeight(120)
        
        consent_label = QLabel("의사회원의 웹엠 서비스 이용을 위한 안내문을 읽고 숙지하였으므로, 환자로부터 유효한 동의를 받았음을 확인합니다.")
        consent_label.setFont(font_loader.get_font('Medium', 12))
        consent_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        consent_label.setWordWrap(True)
        
        consent_layout.addWidget(self.consent_checkbox)
        consent_layout.addWidget(consent_label)
        consent_layout.addStretch()
        
        form_layout.addWidget(QLabel(""), 7, 0)  # 빈 공간
        form_layout.addWidget(consent_text, 8, 0, 1, 2)
        form_layout.addLayout(consent_layout, 9, 0, 1, 2)
        
        # 검증 메시지 영역
        self.validation_label = QLabel("")
        self.validation_label.setFont(font_loader.get_font('Regular', 12))
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)
        
        layout.addWidget(title_label)
        layout.addLayout(form_layout)
        layout.addWidget(self.validation_label)
        layout.addStretch()
    
    def create_form_field(self, layout, row, label_text, attr_name, placeholder):
        """폼 필드 생성 헬퍼"""
        label = QLabel(label_text)
        label.setFont(font_loader.get_font('Medium', 12))
        label.setStyleSheet(f"color: {COLORS['gray_700']};")
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFont(font_loader.get_font('Regular', 14))
        input_field.setMinimumHeight(44)
        
        setattr(self, attr_name, input_field)
        
        layout.addWidget(label, row, 0)
        layout.addWidget(input_field, row, 1)
    
    def setup_validation(self):
        """검증 설정"""
        # 입력 필드 변경 시 검증 트리거
        self.name_input.textChanged.connect(self.trigger_validation)
        self.birth_date_input.dateChanged.connect(self.trigger_validation)
        self.reg_num_input.textChanged.connect(self.trigger_validation)
        self.gender_input.currentTextChanged.connect(self.trigger_validation)
        self.phone_input.textChanged.connect(self.trigger_validation)
        self.email_input.textChanged.connect(self.trigger_validation)
        self.consent_checkbox.stateChanged.connect(self.trigger_validation)
    
    def trigger_validation(self):
        """검증 트리거 (500ms 지연)"""
        self.validation_timer.stop()
        self.validation_timer.start(500)
    
    def validate_form(self):
        """폼 전체 검증"""
        errors = []
        
        # 이름 검증
        name_valid, name_msg = self.validate_name(self.name_input.text())
        if not name_valid:
            errors.append(name_msg)
            self.set_field_error(self.name_input, name_msg)
        else:
            self.clear_field_error(self.name_input)
        
        # 생년월일 검증
        birth_valid, birth_msg = self.validate_birth_date(self.birth_date_input.date())
        if not birth_valid:
            errors.append(birth_msg)
        
        # 등록번호 검증
        reg_valid, reg_msg = self.validate_registration_number(self.reg_num_input.text())
        if not reg_valid:
            errors.append(reg_msg)
            self.set_field_error(self.reg_num_input, reg_msg)
        else:
            self.clear_field_error(self.reg_num_input)
        
        # 성별 검증
        if self.gender_input.currentText() == "선택하세요":
            errors.append("성별을 선택해주세요")
        
        # 동의 체크박스 검증
        if not self.consent_checkbox.isChecked():
            errors.append("개인정보 이용 동의를 체크해주세요")
        
        # 연락처 검증 (선택사항)
        phone_valid, phone_msg = self.validate_phone(self.phone_input.text())
        if not phone_valid:
            errors.append(phone_msg)
            self.set_field_error(self.phone_input, phone_msg)
        else:
            self.clear_field_error(self.phone_input)
        
        # 이메일 검증 (선택사항)
        email = self.email_input.text().strip()
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append("올바른 이메일 형식을 입력해주세요")
            self.set_field_error(self.email_input, "올바른 이메일 형식을 입력해주세요")
        else:
            self.clear_field_error(self.email_input)
        
        # 결과 처리
        is_valid = len(errors) == 0
        
        if is_valid:
            self.patient_data = self.get_form_data()
            self.show_validation_message("✅ 모든 정보가 올바르게 입력되었습니다", "success")
        else:
            self.show_validation_message(f"❌ {len(errors)}개 오류: {', '.join(errors[:2])}", "error")
        
        self.form_validated.emit(is_valid, self.patient_data if is_valid else {})
    
    def get_form_data(self):
        """폼 데이터 반환"""
        return {
            'name': self.name_input.text().strip(),
            'birth_date': self.birth_date_input.date().toPyDate(),
            'registration_number': self.reg_num_input.text().strip(),
            'gender': 'M' if self.gender_input.currentText() == '남성' else 'F',
            'phone': self.phone_input.text().strip() or None,
            'email': self.email_input.text().strip() or None,
            'notes': self.notes_input.toPlainText().strip() or None,
            'consent_agreed': self.consent_checkbox.isChecked()
        }
    
    def set_field_error(self, field, message):
        """필드 오류 스타일 설정"""
        field.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['error_500']};
                background-color: {COLORS['white']};
            }}
        """)
        field.setToolTip(message)
    
    def clear_field_error(self, field):
        """필드 오류 스타일 제거"""
        field.setStyleSheet("")
        field.setToolTip("")
    
    def show_validation_message(self, message, type="info"):
        """검증 메시지 표시"""
        self.validation_label.setText(message)
        self.validation_label.setVisible(True)
        
        if type == "error":
            self.validation_label.setStyleSheet(f"color: {COLORS['error_500']};")
        elif type == "success":
            self.validation_label.setStyleSheet(f"color: {COLORS['success_500']};")
        else:
            self.validation_label.setStyleSheet(f"color: {COLORS['gray_600']};")
    
    def clear_form(self):
        """폼 초기화"""
        self.name_input.clear()
        self.birth_date_input.setDate(QDate.currentDate().addYears(-30))
        self.reg_num_input.clear()
        self.gender_input.setCurrentIndex(0)
        self.phone_input.clear()
        self.email_input.clear()
        self.notes_input.clear()
        self.consent_checkbox.setChecked(False)
        
        # 오류 스타일 제거
        for field in [self.name_input, self.reg_num_input, self.phone_input, self.email_input]:
            self.clear_field_error(field)
        
        self.validation_label.setVisible(False)
        self.patient_data = {}

class ImageSelectionWidget(QFrame):
    """이미지 선택 위젯"""
    
    images_selected = pyqtSignal(dict)  # {'xray': path, 'face': path}
    
    def __init__(self):
        super().__init__()
        self.selected_images = {'xray': None, 'face': None}
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정"""
        self.setProperty("class", "card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 제목
        title_label = QLabel("이미지 선택")
        title_label.setFont(font_loader.get_font('SemiBold', 18))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        # 이미지 선택 영역
        images_layout = QHBoxLayout()
        images_layout.setSpacing(20)
        
        # X-ray 이미지
        self.xray_widget = self.create_image_widget("X-ray 이미지", "xray")
        images_layout.addWidget(self.xray_widget)
        
        # 얼굴 사진
        self.face_widget = self.create_image_widget("얼굴 사진", "face")
        images_layout.addWidget(self.face_widget)
        
        layout.addWidget(title_label)
        layout.addLayout(images_layout)
        layout.addStretch()
    
    def create_image_widget(self, title, image_type):
        """이미지 위젯 생성"""
        widget = QFrame()
        widget.setMinimumHeight(300)
        widget.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {COLORS['gray_300']};
                border-radius: 8px;
                background-color: {COLORS['gray_50']};
            }}
            QFrame:hover {{
                border-color: {COLORS['primary_300']};
                background-color: {COLORS['primary_50']};
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        
        # 제목
        title_label = QLabel(title)
        title_label.setFont(font_loader.get_font('SemiBold', 14))
        title_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        title_label.setAlignment(Qt.AlignCenter)
        
        # 미리보기 라벨
        preview_label = QLabel("📷")
        preview_label.setFont(QFont("Segoe UI Emoji", 48))
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet(f"color: {COLORS['gray_400']};")
        setattr(self, f"{image_type}_preview", preview_label)
        
        # 파일 경로 라벨
        path_label = QLabel("파일을 선택하세요")
        path_label.setFont(font_loader.get_font('Regular', 12))
        path_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        path_label.setAlignment(Qt.AlignCenter)
        path_label.setWordWrap(True)
        setattr(self, f"{image_type}_path_label", path_label)
        
        # 선택 버튼
        select_btn = QPushButton("파일 선택")
        select_btn.setFont(font_loader.get_font('Medium', 14))
        select_btn.setProperty("class", "secondary")
        select_btn.clicked.connect(lambda: self.select_image(image_type))
        
        layout.addWidget(title_label)
        layout.addWidget(preview_label)
        layout.addWidget(path_label)
        layout.addWidget(select_btn)
        
        return widget
    
    def select_image(self, image_type):
        """이미지 파일 선택"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("이미지 파일 (*.jpg *.jpeg *.png *.bmp)")
        
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.set_image(image_type, file_path)
    
    def set_image(self, image_type, file_path):
        """선택된 이미지 설정"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "오류", "파일을 찾을 수 없습니다.")
            return
        
        try:
            # 이미지 미리보기
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "오류", "올바른 이미지 파일이 아닙니다.")
                return
            
            # 미리보기 크기 조정
            preview_label = getattr(self, f"{image_type}_preview")
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            preview_label.setPixmap(scaled_pixmap)
            
            # 파일 경로 표시
            path_label = getattr(self, f"{image_type}_path_label")
            file_name = os.path.basename(file_path)
            path_label.setText(f"✅ {file_name}")
            path_label.setStyleSheet(f"color: {COLORS['success_500']};")
            
            # 선택된 이미지 저장
            self.selected_images[image_type] = file_path
            
            # 시그널 발송
            self.images_selected.emit(self.selected_images)
            
        except Exception as e:
            QMessageBox.warning(self, "오류", f"이미지 로드 중 오류가 발생했습니다: {str(e)}")
    
    def clear_images(self):
        """선택된 이미지 초기화"""
        for image_type in ['xray', 'face']:
            preview_label = getattr(self, f"{image_type}_preview")
            preview_label.clear()
            preview_label.setText("📷")
            preview_label.setStyleSheet(f"color: {COLORS['gray_400']};")
            
            path_label = getattr(self, f"{image_type}_path_label")
            path_label.setText("파일을 선택하세요")
            path_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        
        self.selected_images = {'xray': None, 'face': None}

class PatientFormWidget(QWidget):
    """환자 폼 메인 위젯"""
    
    def __init__(self):
        super().__init__()
        self.current_patient_data = {}
        self.current_images = {}
        self.dentweb_worker = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # 페이지 제목
        self.create_page_header(main_layout)
        
        # 탭 위젯
        self.create_tab_widget(main_layout)
        
        # 액션 버튼들
        self.create_action_buttons(main_layout)
    
    def create_page_header(self, layout):
        """페이지 헤더 생성"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("환자 관리")
        title_label.setFont(font_loader.get_font('Bold', 24))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        subtitle_label = QLabel("새로운 환자를 등록하고 이미지를 업로드하세요")
        subtitle_label.setFont(font_loader.get_font('Regular', 14))
        subtitle_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
    
    def create_tab_widget(self, layout):
        """탭 위젯 생성"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(font_loader.get_font('Medium', 14))
        
        # 환자 정보 탭
        self.patient_info_widget = PatientInfoWidget()
        self.tab_widget.addTab(self.patient_info_widget, "📝 환자 정보")
        
        # 이미지 선택 탭
        self.image_selection_widget = ImageSelectionWidget()
        self.tab_widget.addTab(self.image_selection_widget, "📷 이미지 선택")
        
        layout.addWidget(self.tab_widget)
    
    def create_action_buttons(self, layout):
        """액션 버튼 생성"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # Dentweb OCR 버튼
        dentweb_ocr_btn = QPushButton("📷 Dentweb에서 가져오기")
        dentweb_ocr_btn.setFont(font_loader.get_font('Medium', 14))
        dentweb_ocr_btn.setMinimumHeight(44)
        dentweb_ocr_btn.setProperty("class", "secondary")
        dentweb_ocr_btn.clicked.connect(self.extract_from_dentweb)
        
        # OCR 테스트 버튼
        ocr_test_btn = QPushButton("🔍 OCR 테스트")
        ocr_test_btn.setFont(font_loader.get_font('Medium', 14))
        ocr_test_btn.setMinimumHeight(44)
        ocr_test_btn.setProperty("class", "ghost")
        ocr_test_btn.clicked.connect(self.test_ocr_function)
        ocr_test_btn.setToolTip("현재 화면의 지정된 영역으로 OCR 기능을 테스트합니다")
        
        # 초기화 버튼
        clear_btn = QPushButton("🔄 초기화")
        clear_btn.setFont(font_loader.get_font('Medium', 14))
        clear_btn.setMinimumHeight(44)
        clear_btn.setProperty("class", "ghost")
        clear_btn.clicked.connect(self.clear_all)
        
        # 미리보기 버튼
        preview_btn = QPushButton("👁️ 미리보기")
        preview_btn.setFont(font_loader.get_font('Medium', 14))
        preview_btn.setMinimumHeight(44)
        preview_btn.setProperty("class", "secondary")
        preview_btn.clicked.connect(self.show_preview)
        
        # 자동화 시작 버튼
        self.start_btn = QPushButton("⚡ 자동화 시작")
        self.start_btn.setFont(font_loader.get_font('SemiBold', 16))
        self.start_btn.setMinimumHeight(48)
        self.start_btn.setProperty("class", "primary")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_automation)
        
        button_layout.addWidget(dentweb_ocr_btn)
        button_layout.addWidget(ocr_test_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(preview_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """시그널 연결 설정"""
        self.patient_info_widget.form_validated.connect(self.on_form_validated)
        self.image_selection_widget.images_selected.connect(self.on_images_selected)
    
    def on_form_validated(self, is_valid, patient_data):
        """폼 검증 결과 처리"""
        self.current_patient_data = patient_data if is_valid else {}
        self.update_start_button()
    
    def on_images_selected(self, images):
        """이미지 선택 결과 처리"""
        self.current_images = images
        self.update_start_button()
    
    def update_start_button(self):
        """시작 버튼 상태 업데이트"""
        has_patient_data = bool(self.current_patient_data) if self.current_patient_data else False
        has_required_images = bool(self.current_images.get('xray') and self.current_images.get('face')) if hasattr(self, 'current_images') else False
        
        self.start_btn.setEnabled(has_patient_data and has_required_images)
        
        if not has_patient_data:
            self.start_btn.setText("⚡ 환자 정보를 입력하세요")
        elif not has_required_images:
            self.start_btn.setText("⚡ 이미지를 선택하세요")
        else:
            self.start_btn.setText("⚡ 자동화 시작")
    
    def clear_all(self):
        """모든 입력 초기화"""
        reply = QMessageBox.question(
            self,
            "초기화 확인",
            "모든 입력 내용을 초기화하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.patient_info_widget.clear_form()
            self.image_selection_widget.clear_images()
            self.current_patient_data = {}
            self.current_images = {}
            self.update_start_button()
    
    def show_preview(self):
        """입력 내용 미리보기"""
        if not self.current_patient_data:
            QMessageBox.information(self, "미리보기", "먼저 환자 정보를 입력해주세요.")
            return
        
        data = self.current_patient_data
        preview_text = f"""
환자 정보 미리보기

이름: {data.get('name', '')}
생년월일: {data.get('birth_date', '')}
등록번호: {data.get('registration_number', '')}
성별: {'남성' if data.get('gender') == 'M' else '여성'}
연락처: {data.get('phone', '없음')}
이메일: {data.get('email', '없음')}
특이사항: {data.get('notes', '없음')}

이미지:
X-ray: {'선택됨' if self.current_images.get('xray') else '선택 안됨'}
얼굴 사진: {'선택됨' if self.current_images.get('face') else '선택 안됨'}
        """.strip()
        
        QMessageBox.information(self, "미리보기", preview_text)
    
    def start_automation(self):
        """자동화 프로세스 시작"""
        if not self.current_patient_data or not all(self.current_images.values()):
            QMessageBox.warning(self, "오류", "환자 정보와 이미지를 모두 입력해주세요.")
            return
        
        # 자동화 페이지로 이동하며 데이터 전달
        main_window = self.window()
        automation_widget = main_window.pages.get("automation")
        
        if automation_widget:
            automation_widget.start_patient_process(
                self.current_patient_data, 
                self.current_images
            )
            main_window.navigate_to_page("automation")
        else:
            QMessageBox.warning(self, "오류", "자동화 모듈을 찾을 수 없습니다.")
    
    def extract_from_dentweb(self):
        """Dentweb에서 환자 정보 추출"""
        try:
            # Upstage API 키 확인
            api_key = config.get('upstage', 'api_key', '')
            if not api_key:
                QMessageBox.warning(
                    self, 
                    "API 키 필요", 
                    "Upstage OCR API 키가 설정되지 않았습니다.\n설정 메뉴에서 API 키를 먼저 설정해주세요."
                )
                return
            
            # 진행 중인 작업이 있으면 중단
            if self.dentweb_worker and self.dentweb_worker.isRunning():
                self.dentweb_worker.terminate()
                self.dentweb_worker.wait()
            
            # 워커 스레드 생성 및 시그널 연결
            self.dentweb_worker = DentwebAutomationWorker()
            self.dentweb_worker.patient_info_extracted.connect(self.on_patient_info_extracted)
            self.dentweb_worker.error_occurred.connect(self.on_dentweb_error)
            self.dentweb_worker.status_updated.connect(self.on_dentweb_status_update)
            
            # 사용자에게 안내 메시지 표시
            result = QMessageBox.question(
                self,
                "Dentweb 스크린샷",
                "Dentweb 프로그램에서 환자 정보가 표시된 화면을 준비하신 후 '확인'을 클릭하세요.\n\n"
                "스크린샷 영역: 400x400 픽셀 (설정에서 변경 가능)\n"
                "3초 후 자동으로 스크린샷을 촬영합니다.",
                QMessageBox.Ok | QMessageBox.Cancel
            )
            
            if result == QMessageBox.Ok:
                # 3초 대기 후 스크린샷 촬영
                QTimer.singleShot(3000, self.start_dentweb_extraction)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Dentweb 정보 추출 중 오류가 발생했습니다:\n{str(e)}")
    
    def start_dentweb_extraction(self):
        """Dentweb 정보 추출 시작"""
        try:
            # 워커 스레드 시작
            self.dentweb_worker.start()
            
            # UI 상태 업데이트
            self.update_dentweb_ui_state(True)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"추출 시작 중 오류가 발생했습니다:\n{str(e)}")
    
    def on_patient_info_extracted(self, patient_info):
        """환자 정보 추출 완료 처리"""
        try:
            # UI 상태 복원
            self.update_dentweb_ui_state(False)
            
            # 추출된 정보 검증
            if not any([patient_info.get('name'), patient_info.get('birth_date'), patient_info.get('registration_number')]):
                QMessageBox.warning(
                    self,
                    "정보 추출 실패",
                    "환자 정보를 추출할 수 없었습니다.\n\n"
                    "다음 사항을 확인해주세요:\n"
                    "- Dentweb 화면에 환자 정보가 명확히 표시되어 있는지\n"
                    "- 스크린샷 영역 설정이 올바른지\n"
                    "- OCR이 읽을 수 있는 텍스트 형태인지"
                )
                return
            
            # 폼에 정보 입력
            self.fill_form_with_extracted_data(patient_info)
            
            # 성공 메시지
            extracted_fields = []
            if patient_info.get('name'):
                extracted_fields.append(f"이름: {patient_info['name']}")
            if patient_info.get('birth_date'):
                extracted_fields.append(f"생년월일: {patient_info['birth_date']}")
            if patient_info.get('registration_number'):
                extracted_fields.append(f"등록번호: {patient_info['registration_number']}")
            
            QMessageBox.information(
                self,
                "정보 추출 완료",
                f"다음 정보가 성공적으로 추출되었습니다:\n\n" + "\n".join(extracted_fields)
            )
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"정보 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def on_dentweb_error(self, error_message):
        """Dentweb 추출 오류 처리"""
        self.update_dentweb_ui_state(False)
        QMessageBox.critical(self, "추출 오류", f"환자 정보 추출 중 오류가 발생했습니다:\n{error_message}")
    
    def on_dentweb_status_update(self, status):
        """Dentweb 상태 업데이트"""
        # 상태바나 로그에 상태 표시 (현재는 콘솔 출력)
        print(f"Dentweb 상태: {status}")
    
    def update_dentweb_ui_state(self, is_extracting):
        """Dentweb 추출 중 UI 상태 업데이트"""
        # 모든 버튼 비활성화/활성화
        for button in self.findChildren(QPushButton):
            button.setEnabled(not is_extracting)
        
        if is_extracting:
            # 진행 상태 표시 (간단한 텍스트로)
            if hasattr(self, 'status_label'):
                self.status_label.setText("Dentweb에서 환자 정보를 추출하는 중...")
    
    def fill_form_with_extracted_data(self, patient_info):
        """추출된 데이터로 폼 채우기"""
        try:
            # 직접 patient_info_widget 접근
            if not hasattr(self, 'patient_info_widget'):
                print("환자 정보 위젯을 찾을 수 없습니다")
                return
            
            patient_form = self.patient_info_widget
            
            # 이름 입력 (환자 ID는 이름으로 처리)
            if patient_info.get('name'):
                if hasattr(patient_form, 'name_input'):
                    patient_form.name_input.setText(patient_info['name'])
                    print(f"이름 입력됨: {patient_info['name']}")
            
            # 생년월일 입력
            if patient_info.get('birth_date'):
                if hasattr(patient_form, 'birth_date_input'):
                    try:
                        # 다양한 날짜 형식 처리
                        birth_date_str = patient_info['birth_date']
                        birth_date_str = re.sub(r'[./]', '-', birth_date_str)  # 구분자 통일
                        
                        # YYYY-MM-DD 형식으로 파싱
                        date_parts = birth_date_str.split('-')
                        if len(date_parts) == 3:
                            year, month, day = map(int, date_parts)
                            # 연도가 2자리인 경우 4자리로 변환
                            if year < 100:
                                year += 1900 if year > 50 else 2000
                            
                            patient_form.birth_date_input.setDate(QDate(year, month, day))
                            print(f"생년월일 입력됨: {year}-{month:02d}-{day:02d}")
                    except (ValueError, IndexError) as e:
                        print(f"날짜 파싱 오류: {patient_info['birth_date']} - {e}")
            
            # 등록번호 입력 (환자 ID로 처리)
            if patient_info.get('registration_number'):
                if hasattr(patient_form, 'reg_num_input'):
                    patient_form.reg_num_input.setText(patient_info['registration_number'])
                    print(f"등록번호 입력됨: {patient_info['registration_number']}")
            
            # 성별 자동 추론 (이름 기반 간단한 추론)
            if patient_info.get('name') and hasattr(patient_form, 'gender_input'):
                name = patient_info['name']
                # 한국어 이름 끝자리 기반 성별 추론 (간단한 방식)
                male_endings = ['호', '준', '민', '진', '현', '성', '용', '석', '영', '철', '수', '환', '욱', '빈', '건', '훈']
                female_endings = ['희', '영', '정', '미', '은', '아', '연', '주', '서', '지', '인', '혜', '현', '원', '나', '별']
                
                if name and len(name) >= 2:
                    last_char = name[-1]
                    if last_char in male_endings:
                        patient_form.gender_input.setCurrentText("남성")
                        print("성별 추론됨: 남성")
                    elif last_char in female_endings:
                        patient_form.gender_input.setCurrentText("여성")
                        print("성별 추론됨: 여성")
            
            # 동의 체크박스 자동 체크 (OCR로 정보를 가져왔다면 동의했다고 가정)
            if hasattr(patient_form, 'consent_checkbox'):
                patient_form.consent_checkbox.setChecked(True)
                print("개인정보 이용 동의 자동 체크됨")
            
            # 폼 검증 트리거
            if hasattr(patient_form, 'validate_form'):
                patient_form.validate_form()
                print("폼 검증 실행됨")
                
        except Exception as e:
            print(f"폼 채우기 오류: {e}")
            QMessageBox.warning(self, "오류", f"추출된 정보를 폼에 입력하는 중 오류가 발생했습니다:\n{str(e)}")
    
    def get_form_data(self):
        """현재 폼 데이터 반환"""
        return {
            'patient_data': self.current_patient_data,
            'images': self.current_images
        } 

    def test_ocr_function(self):
        """OCR 기능 테스트"""
        try:
            # API 키 확인
            api_key = config.get('upstage', 'api_key', '')
            if not api_key:
                QMessageBox.warning(
                    self, 
                    "API 키 필요", 
                    "Upstage OCR API 키가 설정되지 않았습니다.\n"
                    "설정 메뉴에서 API 키를 먼저 설정해주세요."
                )
                return
            
            # 좌표 입력 다이얼로그
            dialog = QDialog(self)
            dialog.setWindowTitle("OCR 테스트 영역 설정")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # 설명 라벨
            desc_label = QLabel(
                "화면에서 OCR 테스트를 수행할 영역을 설정하세요.\n"
                "좌표는 화면의 왼쪽 상단을 (0,0) 기준으로 합니다."
            )
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {COLORS['gray_600']}; margin-bottom: 16px;")
            
            # 좌표 입력 폼
            form_layout = QGridLayout()
            
            # X 좌표
            form_layout.addWidget(QLabel("X 좌표:"), 0, 0)
            x_input = QSpinBox()
            x_input.setRange(0, 9999)
            x_input.setValue(config.get_int('dentweb', 'screenshot_x', 400))
            form_layout.addWidget(x_input, 0, 1)
            
            # Y 좌표  
            form_layout.addWidget(QLabel("Y 좌표:"), 1, 0)
            y_input = QSpinBox()
            y_input.setRange(0, 9999)
            y_input.setValue(config.get_int('dentweb', 'screenshot_y', 400))
            form_layout.addWidget(y_input, 1, 1)
            
            # 너비
            form_layout.addWidget(QLabel("너비:"), 2, 0)
            width_input = QSpinBox()
            width_input.setRange(50, 2000)
            width_input.setValue(config.get_int('dentweb', 'screenshot_width', 400))
            form_layout.addWidget(width_input, 2, 1)
            
            # 높이
            form_layout.addWidget(QLabel("높이:"), 3, 0)
            height_input = QSpinBox()
            height_input.setRange(50, 2000)
            height_input.setValue(config.get_int('dentweb', 'screenshot_height', 400))
            form_layout.addWidget(height_input, 3, 1)
            
            # 버튼들
            button_layout = QHBoxLayout()
            cancel_btn = QPushButton("취소")
            cancel_btn.clicked.connect(dialog.reject)
            
            test_btn = QPushButton("OCR 테스트 실행")
            test_btn.setProperty("class", "primary")
            test_btn.clicked.connect(lambda: self.execute_ocr_test_from_dialog(
                dialog, x_input.value(), y_input.value(), 
                width_input.value(), height_input.value()
            ))
            
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(test_btn)
            
            layout.addWidget(desc_label)
            layout.addLayout(form_layout)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"OCR 테스트 중 오류가 발생했습니다:\n{str(e)}")
    
    def execute_ocr_test_from_dialog(self, dialog, x, y, width, height):
        """다이얼로그에서 OCR 테스트 실행"""
        dialog.accept()
        QTimer.singleShot(1000, lambda: self.execute_ocr_test(x, y, width, height))
    
    def execute_ocr_test(self, x: int, y: int, width: int, height: int):
        """OCR 테스트 실행"""
        try:
            from ..automation.dentweb_automation import DentwebOCRExtractor
            
            # OCR 추출기 생성
            extractor = DentwebOCRExtractor()
            
            # 테스트 실행
            result = extractor.test_ocr_with_current_screen(x, y, width, height)
            
            if result['success']:
                # 성공 결과 표시
                result_dialog = QDialog(self)
                result_dialog.setWindowTitle("OCR 테스트 결과")
                result_dialog.setModal(True)
                result_dialog.resize(600, 500)
                
                layout = QVBoxLayout(result_dialog)
                
                # 성공 메시지
                success_label = QLabel("✅ OCR 테스트가 성공적으로 완료되었습니다!")
                success_label.setStyleSheet(f"color: {COLORS['success_600']}; font-weight: bold; font-size: 14px;")
                
                # 스크린샷 경로
                if result['screenshot_path']:
                    path_label = QLabel(f"📷 스크린샷: {result['screenshot_path']}")
                    path_label.setStyleSheet(f"color: {COLORS['gray_600']}; margin: 8px 0;")
                    path_label.setWordWrap(True)
                
                # 추출된 텍스트
                text_label = QLabel("📋 추출된 텍스트:")
                text_label.setStyleSheet(f"color: {COLORS['gray_700']}; font-weight: bold;")
                
                text_area = QTextEdit()
                text_area.setPlainText(result['text'])
                text_area.setReadOnly(True)
                text_area.setMinimumHeight(200)
                
                # 닫기 버튼
                close_btn = QPushButton("닫기")
                close_btn.setProperty("class", "secondary")
                close_btn.clicked.connect(result_dialog.accept)
                
                layout.addWidget(success_label)
                if result['screenshot_path']:
                    layout.addWidget(path_label)
                layout.addWidget(text_label)
                layout.addWidget(text_area)
                layout.addWidget(close_btn)
                
                result_dialog.exec_()
                
            else:
                # 실패 결과 표시
                error_msg = result.get('error', '알 수 없는 오류가 발생했습니다')
                screenshot_info = ""
                if result['screenshot_path']:
                    screenshot_info = f"\n\n📷 스크린샷 저장됨: {result['screenshot_path']}"
                
                QMessageBox.warning(
                    self,
                    "OCR 테스트 실패",
                    f"❌ OCR 테스트에 실패했습니다.\n\n"
                    f"오류: {error_msg}{screenshot_info}"
                )
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"OCR 테스트 실행 중 오류가 발생했습니다:\n{str(e)}") 

    def clear_form(self):
        """폼 전체 초기화"""
        try:
            # 환자 정보 위젯 초기화
            if hasattr(self, 'patient_info_widget'):
                self.patient_info_widget.clear_form()
            
            # 이미지 선택 위젯 초기화
            if hasattr(self, 'image_selection_widget'):
                self.image_selection_widget.clear_images()
            
            # 현재 데이터 초기화
            self.current_patient_data = {}
            self.current_images = {}
            
            # 시작 버튼 상태 업데이트
            self.update_start_button()
            
        except Exception as e:
            print(f"폼 초기화 오류: {e}") 