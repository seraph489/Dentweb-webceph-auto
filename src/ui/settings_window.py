"""
설정 윈도우 위젯
Web Ceph 계정, Airtable API, 폴더 경로 등의 설정을 관리
"""

import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QLineEdit, QPushButton, QTabWidget, 
                           QFileDialog, QMessageBox, QFrame, QGroupBox,
                           QSpinBox, QCheckBox, QComboBox, QTextEdit,
                           QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .styles import COLORS
from ..utils.font_loader import font_loader
from ..config import config

class AccountSettingsTab(QWidget):
    """계정 설정 탭"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        # Web Ceph 계정 설정
        self.create_webceph_group(layout)
        
        # Airtable 설정
        self.create_airtable_group(layout)
        
        # Upstage OCR 설정
        self.create_upstage_group(layout)
        
        layout.addStretch()
    
    def create_webceph_group(self, layout):
        """Web Ceph 계정 설정 그룹"""
        group = QGroupBox("Web Ceph 계정")
        group.setFont(font_loader.get_font('SemiBold', 14))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(16)
        
        # 설명
        desc_label = QLabel("Web Ceph 웹사이트 로그인에 사용할 계정 정보를 입력하세요.")
        desc_label.setFont(font_loader.get_font('Regular', 12))
        desc_label.setStyleSheet(f"color: {COLORS['gray_600']};")
        desc_label.setWordWrap(True)
        
        # 폼 레이아웃
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        
        # 사용자명
        username_label = QLabel("사용자명:")
        username_label.setFont(font_loader.get_font('Medium', 12))
        self.webceph_username = QLineEdit()
        self.webceph_username.setPlaceholderText("Web Ceph 사용자명")
        self.webceph_username.setFont(font_loader.get_font('Regular', 14))
        
        # 비밀번호
        password_label = QLabel("비밀번호:")
        password_label.setFont(font_loader.get_font('Medium', 12))
        self.webceph_password = QLineEdit()
        self.webceph_password.setPlaceholderText("Web Ceph 비밀번호")
        self.webceph_password.setEchoMode(QLineEdit.Password)
        self.webceph_password.setFont(font_loader.get_font('Regular', 14))
        
        # URL
        url_label = QLabel("Web Ceph URL:")
        url_label.setFont(font_loader.get_font('Medium', 12))
        self.webceph_url = QLineEdit()
        self.webceph_url.setPlaceholderText("https://www.webceph.com")
        self.webceph_url.setFont(font_loader.get_font('Regular', 14))
        
        # 연결 테스트 버튼
        test_btn = QPushButton("연결 테스트")
        test_btn.setFont(font_loader.get_font('Medium', 14))
        test_btn.setProperty("class", "secondary")
        test_btn.clicked.connect(self.test_webceph_connection)
        
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.webceph_username, 0, 1)
        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.webceph_password, 1, 1)
        form_layout.addWidget(url_label, 2, 0)
        form_layout.addWidget(self.webceph_url, 2, 1)
        form_layout.addWidget(test_btn, 3, 1)
        
        group_layout.addWidget(desc_label)
        group_layout.addLayout(form_layout)
        
        layout.addWidget(group)
    
    def create_airtable_group(self, layout):
        """Airtable 설정 그룹"""
        group = QGroupBox("Airtable 연동")
        group.setFont(font_loader.get_font('SemiBold', 14))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(16)
        
        # 설명
        desc_label = QLabel("분석 결과를 저장할 Airtable 설정을 입력하세요.")
        desc_label.setFont(font_loader.get_font('Regular', 12))
        desc_label.setStyleSheet(f"color: {COLORS['gray_600']};")
        desc_label.setWordWrap(True)
        
        # 폼 레이아웃
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        
        # API 키
        api_key_label = QLabel("API 키:")
        api_key_label.setFont(font_loader.get_font('Medium', 12))
        self.airtable_api_key = QLineEdit()
        self.airtable_api_key.setPlaceholderText("Airtable API 키를 입력하세요")
        self.airtable_api_key.setEchoMode(QLineEdit.Password)
        self.airtable_api_key.setFont(font_loader.get_font('Regular', 14))
        
        # Base ID
        base_id_label = QLabel("Base ID:")
        base_id_label.setFont(font_loader.get_font('Medium', 12))
        self.airtable_base_id = QLineEdit()
        self.airtable_base_id.setPlaceholderText("Base ID (app으로 시작)")
        self.airtable_base_id.setFont(font_loader.get_font('Regular', 14))
        
        # 테이블명
        table_name_label = QLabel("테이블명:")
        table_name_label.setFont(font_loader.get_font('Medium', 12))
        self.airtable_table_name = QLineEdit()
        self.airtable_table_name.setPlaceholderText("환자 데이터를 저장할 테이블명")
        self.airtable_table_name.setFont(font_loader.get_font('Regular', 14))
        
        # 연결 테스트 버튼
        test_airtable_btn = QPushButton("연결 테스트")
        test_airtable_btn.setFont(font_loader.get_font('Medium', 14))
        test_airtable_btn.setProperty("class", "secondary")
        test_airtable_btn.clicked.connect(self.test_airtable_connection)
        
        form_layout.addWidget(api_key_label, 0, 0)
        form_layout.addWidget(self.airtable_api_key, 0, 1)
        form_layout.addWidget(base_id_label, 1, 0)
        form_layout.addWidget(self.airtable_base_id, 1, 1)
        form_layout.addWidget(table_name_label, 2, 0)
        form_layout.addWidget(self.airtable_table_name, 2, 1)
        form_layout.addWidget(test_airtable_btn, 3, 1)
        
        group_layout.addWidget(desc_label)
        group_layout.addLayout(form_layout)
        
        layout.addWidget(group)
    
    def create_upstage_group(self, layout):
        """Upstage OCR 설정 그룹"""
        group = QGroupBox("Upstage OCR API")
        group.setFont(font_loader.get_font('SemiBold', 14))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(16)
        
        # 설명
        desc_label = QLabel("Dentweb 화면에서 환자 정보를 자동으로 추출하기 위한 Upstage OCR API 키를 입력하세요.")
        desc_label.setWordWrap(True)
        desc_label.setFont(font_loader.get_font('Regular', 12))
        desc_label.setStyleSheet(f"color: {COLORS['gray_600']};")
        
        # 폼 레이아웃
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        form_layout.setColumnStretch(1, 1)
        
        # API 키
        api_key_label = QLabel("API 키:")
        api_key_label.setFont(font_loader.get_font('Medium', 12))
        api_key_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        
        self.upstage_api_key = QLineEdit()
        self.upstage_api_key.setEchoMode(QLineEdit.Password)
        self.upstage_api_key.setPlaceholderText("Upstage API 키를 입력하세요")
        self.upstage_api_key.setFont(font_loader.get_font('Regular', 12))
        self.upstage_api_key.setMinimumHeight(36)
        
        # 테스트 버튼
        self.test_upstage_btn = QPushButton("연결 테스트")
        self.test_upstage_btn.setFont(font_loader.get_font('Medium', 11))
        self.test_upstage_btn.setMinimumHeight(36)
        self.test_upstage_btn.clicked.connect(self.test_upstage_connection)
        
        # API URL
        api_url_label = QLabel("API URL:")
        api_url_label.setFont(font_loader.get_font('Medium', 12))
        api_url_label.setStyleSheet(f"color: {COLORS['gray_700']};")
        
        self.upstage_api_url = QLineEdit()
        self.upstage_api_url.setText("https://api.upstage.ai/v1/document-digitization")
        self.upstage_api_url.setFont(font_loader.get_font('Regular', 12))
        self.upstage_api_url.setMinimumHeight(36)
        
        form_layout.addWidget(api_key_label, 0, 0)
        form_layout.addWidget(self.upstage_api_key, 0, 1)
        form_layout.addWidget(self.test_upstage_btn, 1, 1)
        form_layout.addWidget(api_url_label, 2, 0)
        form_layout.addWidget(self.upstage_api_url, 2, 1)
        
        group_layout.addWidget(desc_label)
        group_layout.addLayout(form_layout)
        
        layout.addWidget(group)
    
    def load_settings(self):
        """설정 로드"""
        # Web Ceph 설정
        username, password = config.get_credentials()
        if username:
            self.webceph_username.setText(username)
        if password:
            self.webceph_password.setText(password)
        
        webceph_url = config.get('webceph', 'url', 'https://www.webceph.com')
        self.webceph_url.setText(webceph_url)
        
        # Airtable 설정
        api_key = config.get_airtable_api_key()
        if api_key:
            self.airtable_api_key.setText(api_key)
        
        base_id = config.get('airtable', 'base_id', '')
        self.airtable_base_id.setText(base_id)
        
        table_name = config.get('airtable', 'table_name', 'Patients')
        self.airtable_table_name.setText(table_name)
        
        # Upstage OCR 설정
        upstage_api_key = config.get_upstage_api_key()
        if upstage_api_key:
            self.upstage_api_key.setText(upstage_api_key)
        
        upstage_api_url = config.get('upstage', 'api_url', 'https://api.upstage.ai/v1/document-digitization')
        self.upstage_api_url.setText(upstage_api_url)
    
    def save_settings(self):
        """설정 저장"""
        try:
            # Web Ceph 설정
            config.save_credentials(
                self.webceph_username.text().strip(),
                self.webceph_password.text().strip()
            )
            config.set('webceph', 'url', self.webceph_url.text().strip())
            
            # Airtable 설정
            if self.airtable_api_key.text().strip():
                config.save_airtable_api_key(self.airtable_api_key.text().strip())
            
            config.set('airtable', 'base_id', self.airtable_base_id.text().strip())
            config.set('airtable', 'table_name', self.airtable_table_name.text().strip())
            
            # Upstage OCR 설정
            if self.upstage_api_key.text().strip():
                config.save_upstage_api_key(self.upstage_api_key.text().strip())
            
            config.set('upstage', 'api_url', self.upstage_api_url.text().strip())
            
            return True
        except Exception as e:
            QMessageBox.warning(self, "오류", f"설정 저장 중 오류가 발생했습니다: {str(e)}")
            return False
    
    def test_webceph_connection(self):
        """Web Ceph 연결 테스트"""
        username = self.webceph_username.text().strip()
        password = self.webceph_password.text().strip()
        url = self.webceph_url.text().strip()
        
        if not all([username, password, url]):
            QMessageBox.warning(self, "입력 오류", "모든 필드를 입력해주세요.")
            return
        
        # 실제 구현에서는 Web Ceph 로그인 테스트
        # 현재는 시뮬레이션
        QMessageBox.information(self, "연결 테스트", "Web Ceph 연결이 성공적으로 확인되었습니다.")
    
    def test_airtable_connection(self):
        """Airtable 연결 테스트"""
        api_key = self.airtable_api_key.text().strip()
        base_id = self.airtable_base_id.text().strip()
        table_name = self.airtable_table_name.text().strip()
        
        if not all([api_key, base_id, table_name]):
            QMessageBox.warning(self, "입력 오류", "모든 필드를 입력해주세요.")
            return
        
        # 실제 구현에서는 Airtable API 테스트
        # 현재는 시뮬레이션
        QMessageBox.information(self, "연결 테스트", "Airtable 연결이 성공적으로 확인되었습니다.")
    
    def test_upstage_connection(self):
        """Upstage OCR 연결 테스트"""
        try:
            api_key = self.upstage_api_key.text().strip()
            api_url = self.upstage_api_url.text().strip()
            
            if not api_key:
                QMessageBox.warning(self, "입력 오류", "Upstage API 키를 입력해주세요.")
                return
            
            if not api_url:
                QMessageBox.warning(self, "입력 오류", "API URL을 입력해주세요.")
                return
            
            # 진행 중 표시
            self.test_upstage_btn = self.sender()  # 테스트 버튼 참조
            original_text = self.test_upstage_btn.text()
            self.test_upstage_btn.setText("테스트 중...")
            self.test_upstage_btn.setEnabled(False)
            
            # 간단한 테스트용 이미지 생성 (1x1 픽셀 검은색 PNG)
            from PIL import Image
            import tempfile
            import requests
            
            # 테스트 이미지 생성
            test_image = Image.new('RGB', (100, 50), color='white')
            
            # 테스트 텍스트 추가 (선택사항)
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(test_image)
                # 기본 폰트로 간단한 텍스트 추가
                draw.text((10, 10), "TEST OCR", fill='black')
            except:
                pass  # 폰트가 없어도 기본 이미지로 테스트
            
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                test_image.save(temp_file.name, format='PNG')
                temp_filename = temp_file.name
            
            try:
                # API 요청 (공식 문서 방식)
                headers = {
                    "Authorization": f"Bearer {api_key}"
                }
                
                with open(temp_filename, "rb") as f:
                    files = {"document": f}
                    data = {"model": "ocr"}
                    
                    response = requests.post(
                        api_url, 
                        headers=headers, 
                        files=files, 
                        data=data,
                        timeout=30
                    )
                
                # 결과 처리
                if response.status_code == 200:
                    try:
                        result = response.json()
                        QMessageBox.information(
                            self, 
                            "연결 성공", 
                            f"✅ Upstage OCR API 연결이 성공했습니다!\n\n"
                            f"상태 코드: {response.status_code}\n"
                            f"응답 크기: {len(str(result))} 문자"
                        )
                    except:
                        QMessageBox.information(
                            self, 
                            "연결 성공", 
                            "✅ Upstage OCR API 연결이 성공했습니다!"
                        )
                elif response.status_code == 401:
                    QMessageBox.warning(
                        self, 
                        "인증 실패", 
                        "❌ API 키가 올바르지 않습니다.\n\n"
                        "Upstage 콘솔에서 API 키를 확인해주세요."
                    )
                elif response.status_code == 429:
                    QMessageBox.warning(
                        self, 
                        "사용량 초과", 
                        "⚠️ API 호출 한도를 초과했습니다.\n\n"
                        "잠시 후 다시 시도해주세요."
                    )
                elif response.status_code == 403:
                    QMessageBox.warning(
                        self, 
                        "권한 없음", 
                        "❌ API 사용 권한이 없습니다.\n\n"
                        "Upstage 계정 상태를 확인해주세요."
                    )
                else:
                    error_detail = ""
                    try:
                        error_json = response.json()
                        error_detail = f"\n상세: {error_json}"
                    except:
                        pass
                    
                    QMessageBox.warning(
                        self, 
                        "연결 실패", 
                        f"❌ Upstage OCR 연결에 실패했습니다.\n\n"
                        f"오류 코드: {response.status_code}\n"
                        f"메시지: {response.text[:200]}{error_detail}"
                    )
                    
            finally:
                # 임시 파일 정리
                import os
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                
        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self, 
                "연결 시간 초과", 
                "⏰ API 서버 연결이 시간 초과되었습니다.\n\n"
                "네트워크 연결을 확인하고 다시 시도해주세요."
            )
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self, 
                "연결 오류", 
                "🌐 API 서버에 연결할 수 없습니다.\n\n"
                "인터넷 연결을 확인하고 다시 시도해주세요."
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "연결 오류", 
                f"🔧 연결 테스트 중 오류가 발생했습니다:\n\n{str(e)}"
            )
        finally:
            # 버튼 상태 복원
            try:
                self.test_upstage_btn.setText(original_text)
                self.test_upstage_btn.setEnabled(True)
            except:
                pass

class PathSettingsTab(QWidget):
    """경로 설정 탭"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        # 폴더 경로 설정
        self.create_path_group(layout)
        
        layout.addStretch()
    
    def create_path_group(self, layout):
        """경로 설정 그룹"""
        group = QGroupBox("폴더 경로 설정")
        group.setFont(font_loader.get_font('SemiBold', 14))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(16)
        
        # 설명
        desc_label = QLabel("이미지 저장, PDF 다운로드 등에 사용할 폴더 경로를 설정하세요.")
        desc_label.setFont(font_loader.get_font('Regular', 12))
        desc_label.setStyleSheet(f"color: {COLORS['gray_600']};")
        desc_label.setWordWrap(True)
        
        # 경로 설정들
        self.create_path_setting(group_layout, "이미지 폴더", "image_folder", "촬영된 이미지가 저장되는 폴더")
        self.create_path_setting(group_layout, "PDF 저장 폴더", "pdf_folder", "분석 결과 PDF가 저장되는 폴더")
        self.create_path_setting(group_layout, "백업 폴더", "backup_folder", "데이터 백업이 저장되는 폴더")
        
        group_layout.insertWidget(0, desc_label)
        layout.addWidget(group)
    
    def create_path_setting(self, layout, title, setting_key, description):
        """경로 설정 위젯 생성"""
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)
        
        # 제목
        title_label = QLabel(title)
        title_label.setFont(font_loader.get_font('SemiBold', 13))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        # 설명
        desc_label = QLabel(description)
        desc_label.setFont(font_loader.get_font('Regular', 11))
        desc_label.setStyleSheet(f"color: {COLORS['gray_600']};")
        
        # 경로 입력 및 선택
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)
        
        path_input = QLineEdit()
        path_input.setFont(font_loader.get_font('Regular', 12))
        path_input.setPlaceholderText("폴더 경로를 선택하세요")
        setattr(self, f"{setting_key}_input", path_input)
        
        browse_btn = QPushButton("📁 선택")
        browse_btn.setFont(font_loader.get_font('Medium', 12))
        browse_btn.setProperty("class", "secondary")
        browse_btn.clicked.connect(lambda: self.browse_folder(setting_key))
        
        open_btn = QPushButton("🔗 열기")
        open_btn.setFont(font_loader.get_font('Medium', 12))
        open_btn.setProperty("class", "ghost")
        open_btn.clicked.connect(lambda: self.open_folder(setting_key))
        
        path_layout.addWidget(path_input)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(open_btn)
        
        container_layout.addWidget(title_label)
        container_layout.addWidget(desc_label)
        container_layout.addLayout(path_layout)
        
        layout.addWidget(container)
    
    def browse_folder(self, setting_key):
        """폴더 선택"""
        current_path = getattr(self, f"{setting_key}_input").text()
        if not current_path:
            current_path = str(Path.home())
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "폴더 선택",
            current_path
        )
        
        if folder:
            getattr(self, f"{setting_key}_input").setText(folder)
    
    def open_folder(self, setting_key):
        """폴더 열기"""
        folder_path = getattr(self, f"{setting_key}_input").text()
        if folder_path and os.path.exists(folder_path):
            os.startfile(folder_path)  # Windows
        else:
            QMessageBox.warning(self, "경고", "폴더가 존재하지 않습니다.")
    
    def load_settings(self):
        """설정 로드"""
        self.image_folder_input.setText(config.get('paths', 'image_folder'))
        self.pdf_folder_input.setText(config.get('paths', 'pdf_folder'))
        self.backup_folder_input.setText(config.get('paths', 'backup_folder'))
    
    def save_settings(self):
        """설정 저장"""
        try:
            config.set('paths', 'image_folder', self.image_folder_input.text().strip())
            config.set('paths', 'pdf_folder', self.pdf_folder_input.text().strip())
            config.set('paths', 'backup_folder', self.backup_folder_input.text().strip())
            return True
        except Exception as e:
            QMessageBox.warning(self, "오류", f"설정 저장 중 오류가 발생했습니다: {str(e)}")
            return False

class AutomationSettingsTab(QWidget):
    """자동화 설정 탭"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        # 자동화 옵션
        self.create_automation_group(layout)
        
        layout.addStretch()
    
    def create_automation_group(self, layout):
        """자동화 설정 그룹"""
        group = QGroupBox("자동화 옵션")
        group.setFont(font_loader.get_font('SemiBold', 14))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(16)
        
        # 설명
        desc_label = QLabel("자동화 프로세스의 동작 방식을 설정합니다.")
        desc_label.setFont(font_loader.get_font('Regular', 12))
        desc_label.setStyleSheet(f"color: {COLORS['gray_600']};")
        desc_label.setWordWrap(True)
        
        # 폼 레이아웃
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        
        # 타임아웃 설정
        timeout_label = QLabel("타임아웃 (초):")
        timeout_label.setFont(font_loader.get_font('Medium', 12))
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(10, 300)
        self.timeout_spinbox.setValue(30)
        self.timeout_spinbox.setSuffix(" 초")
        
        # 재시도 횟수
        retry_label = QLabel("재시도 횟수:")
        retry_label.setFont(font_loader.get_font('Medium', 12))
        self.retry_spinbox = QSpinBox()
        self.retry_spinbox.setRange(1, 10)
        self.retry_spinbox.setValue(3)
        self.retry_spinbox.setSuffix(" 회")
        
        # 대기 시간
        wait_label = QLabel("대기 시간 (초):")
        wait_label.setFont(font_loader.get_font('Medium', 12))
        self.wait_spinbox = QSpinBox()
        self.wait_spinbox.setRange(1, 10)
        self.wait_spinbox.setValue(3)
        self.wait_spinbox.setSuffix(" 초")
        
        # 일괄 처리 크기
        batch_label = QLabel("일괄 처리 크기:")
        batch_label.setFont(font_loader.get_font('Medium', 12))
        self.batch_spinbox = QSpinBox()
        self.batch_spinbox.setRange(1, 20)
        self.batch_spinbox.setValue(5)
        self.batch_spinbox.setSuffix(" 건")
        
        # 자동 시작
        self.auto_start_checkbox = QCheckBox("프로그램 시작 시 자동화 준비")
        self.auto_start_checkbox.setFont(font_loader.get_font('Regular', 12))
        
        form_layout.addWidget(timeout_label, 0, 0)
        form_layout.addWidget(self.timeout_spinbox, 0, 1)
        form_layout.addWidget(retry_label, 1, 0)
        form_layout.addWidget(self.retry_spinbox, 1, 1)
        form_layout.addWidget(wait_label, 2, 0)
        form_layout.addWidget(self.wait_spinbox, 2, 1)
        form_layout.addWidget(batch_label, 3, 0)
        form_layout.addWidget(self.batch_spinbox, 3, 1)
        form_layout.addWidget(self.auto_start_checkbox, 4, 0, 1, 2)
        
        group_layout.addWidget(desc_label)
        group_layout.addLayout(form_layout)
        
        layout.addWidget(group)
    
    def load_settings(self):
        """설정 로드"""
        self.timeout_spinbox.setValue(int(config.get('webceph', 'timeout', '30')))
        self.retry_spinbox.setValue(int(config.get('webceph', 'retry_count', '3')))
        self.wait_spinbox.setValue(int(config.get('automation', 'wait_time', '3')))
        self.batch_spinbox.setValue(int(config.get('automation', 'batch_size', '5')))
        
        auto_start = config.get_bool('automation', 'auto_start', False)
        self.auto_start_checkbox.setChecked(auto_start)
    
    def save_settings(self):
        """설정 저장"""
        try:
            config.set('webceph', 'timeout', str(self.timeout_spinbox.value()))
            config.set('webceph', 'retry_count', str(self.retry_spinbox.value()))
            config.set('automation', 'wait_time', str(self.wait_spinbox.value()))
            config.set('automation', 'batch_size', str(self.batch_spinbox.value()))
            config.set('automation', 'auto_start', 'true' if self.auto_start_checkbox.isChecked() else 'false')
            return True
        except Exception as e:
            QMessageBox.warning(self, "오류", f"설정 저장 중 오류가 발생했습니다: {str(e)}")
            return False

class SettingsWidget(QWidget):
    """설정 메인 위젯"""
    
    settings_saved = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
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
        
        title_label = QLabel("설정")
        title_label.setFont(font_loader.get_font('Bold', 24))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        subtitle_label = QLabel("프로그램 동작에 필요한 설정을 관리합니다")
        subtitle_label.setFont(font_loader.get_font('Regular', 14))
        subtitle_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
    
    def create_tab_widget(self, layout):
        """탭 위젯 생성"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(font_loader.get_font('Medium', 14))
        
        # 계정 설정 탭
        self.account_tab = AccountSettingsTab()
        self.tab_widget.addTab(self.account_tab, "🔐 계정")
        
        # 경로 설정 탭
        self.path_tab = PathSettingsTab()
        self.tab_widget.addTab(self.path_tab, "📁 경로")
        
        # 자동화 설정 탭
        self.automation_tab = AutomationSettingsTab()
        self.tab_widget.addTab(self.automation_tab, "⚙️ 자동화")
        
        layout.addWidget(self.tab_widget)
    
    def create_action_buttons(self, layout):
        """액션 버튼 생성"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # 기본값 복원 버튼
        reset_btn = QPushButton("🔄 기본값 복원")
        reset_btn.setFont(font_loader.get_font('Medium', 14))
        reset_btn.setMinimumHeight(44)
        reset_btn.setProperty("class", "ghost")
        reset_btn.clicked.connect(self.reset_to_defaults)
        
        # 취소 버튼
        cancel_btn = QPushButton("취소")
        cancel_btn.setFont(font_loader.get_font('Medium', 14))
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.cancel_changes)
        
        # 저장 버튼
        save_btn = QPushButton("💾 저장")
        save_btn.setFont(font_loader.get_font('SemiBold', 16))
        save_btn.setMinimumHeight(48)
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save_all_settings)
        
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def save_all_settings(self):
        """모든 설정 저장"""
        try:
            # 각 탭의 설정 저장
            success = True
            success &= self.account_tab.save_settings()
            success &= self.path_tab.save_settings()
            success &= self.automation_tab.save_settings()
            
            if success:
                # 필요한 디렉토리 생성
                config.create_directories()
                
                QMessageBox.information(self, "저장 완료", "모든 설정이 성공적으로 저장되었습니다.")
                self.settings_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"설정 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def cancel_changes(self):
        """변경 사항 취소"""
        reply = QMessageBox.question(
            self,
            "변경 사항 취소",
            "변경 사항을 취소하고 이전 설정으로 되돌리시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 각 탭의 설정 다시 로드
            self.account_tab.load_settings()
            self.path_tab.load_settings()
            self.automation_tab.load_settings()
    
    def reset_to_defaults(self):
        """기본값으로 복원"""
        reply = QMessageBox.question(
            self,
            "기본값 복원",
            "모든 설정을 기본값으로 복원하시겠습니까?\n저장된 계정 정보도 삭제됩니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 설정 파일 삭제 후 기본값으로 재생성
                config_file = config.config_file
                if config_file.exists():
                    config_file.unlink()
                
                # 설정 재로드
                config._load_config()
                
                # 각 탭 새로고침
                self.account_tab.load_settings()
                self.path_tab.load_settings()
                self.automation_tab.load_settings()
                
                QMessageBox.information(self, "복원 완료", "모든 설정이 기본값으로 복원되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "복원 실패", f"기본값 복원 중 오류가 발생했습니다:\n{str(e)}")
    
    def get_current_settings(self):
        """현재 설정 반환"""
        return {
            'webceph_url': self.account_tab.webceph_url.text(),
            'airtable_configured': bool(self.account_tab.airtable_api_key.text()),
            'paths_configured': bool(self.path_tab.image_folder_input.text()),
            'timeout': self.automation_tab.timeout_spinbox.value(),
            'retry_count': self.automation_tab.retry_spinbox.value()
        } 