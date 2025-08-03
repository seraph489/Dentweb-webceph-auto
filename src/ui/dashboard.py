"""
대시보드 위젯 클래스
오늘의 처리 현황, 빠른 실행 버튼, 최근 활동 목록을 표시하는 메인 대시보드
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QPushButton, QFrame, QScrollArea,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QProgressBar, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QPixmap, QPainter, QColor

from .styles import COLORS
from ..utils.font_loader import font_loader
from ..config import config

class StatCardWidget(QFrame):
    """통계 카드 위젯"""
    
    def __init__(self, title, value, unit="", icon="📊", color="primary"):
        super().__init__()
        self.title = title
        self.value = value
        self.unit = unit
        self.icon = icon
        self.color = color
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """UI 설정"""
        self.setProperty("class", "card")
        self.setMinimumHeight(120)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # 아이콘
        icon_label = QLabel(self.icon)
        icon_label.setFont(font_loader.get_font('Regular', 32))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(60, 60)
        
        # 텍스트 영역
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        # 제목
        title_label = QLabel(self.title)
        title_label.setFont(font_loader.get_font('Medium', 12))
        title_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        
        # 값
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)
        value_layout.setContentsMargins(0, 0, 0, 0)
        
        self.value_label = QLabel(str(self.value))
        self.value_label.setFont(font_loader.get_font('Bold', 28))
        
        if self.unit:
            unit_label = QLabel(self.unit)
            unit_label.setFont(font_loader.get_font('Regular', 16))
            unit_label.setStyleSheet(f"color: {COLORS['gray_500']};")
            unit_label.setAlignment(Qt.AlignBottom)
            value_layout.addWidget(self.value_label)
            value_layout.addWidget(unit_label)
        else:
            value_layout.addWidget(self.value_label)
        
        value_layout.addStretch()
        
        text_layout.addWidget(title_label)
        text_layout.addLayout(value_layout)
        text_layout.addStretch()
        
        layout.addWidget(icon_label)
        layout.addLayout(text_layout)
    
    def setup_styles(self):
        """스타일 설정"""
        color_map = {
            'primary': COLORS['primary_500'],
            'success': COLORS['success_500'],
            'warning': COLORS['warning_500'],
            'error': COLORS['error_500']
        }
        
        color = color_map.get(self.color, COLORS['primary_500'])
        self.value_label.setStyleSheet(f"color: {color};")
    
    def update_value(self, new_value):
        """값 업데이트"""
        self.value = new_value
        self.value_label.setText(str(new_value))

class QuickActionWidget(QFrame):
    """빠른 실행 위젯"""
    
    action_clicked = pyqtSignal(str)  # action_type
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """UI 설정"""
        self.setProperty("class", "card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 제목
        title_label = QLabel("빠른 실행")
        title_label.setFont(font_loader.get_font('SemiBold', 16))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        # 주요 액션 버튼
        main_action_btn = QPushButton("⚡ 신규 환자 처리 시작")
        main_action_btn.setFont(font_loader.get_font('SemiBold', 16))
        main_action_btn.setMinimumHeight(56)
        main_action_btn.setProperty("class", "primary")
        main_action_btn.clicked.connect(lambda: self.action_clicked.emit("new_patient"))
        
        # 보조 액션 버튼들
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(12)
        
        batch_btn = QPushButton("📋 일괄 처리")
        batch_btn.setFont(font_loader.get_font('Medium', 14))
        batch_btn.setMinimumHeight(40)
        batch_btn.setProperty("class", "secondary")
        batch_btn.clicked.connect(lambda: self.action_clicked.emit("batch_process"))
        
        monitor_btn = QPushButton("📊 진행 모니터")
        monitor_btn.setFont(font_loader.get_font('Medium', 14))
        monitor_btn.setMinimumHeight(40)
        monitor_btn.setProperty("class", "secondary")
        monitor_btn.clicked.connect(lambda: self.action_clicked.emit("monitor"))
        
        secondary_layout.addWidget(batch_btn)
        secondary_layout.addWidget(monitor_btn)
        
        layout.addWidget(title_label)
        layout.addWidget(main_action_btn)
        layout.addLayout(secondary_layout)
    
    def setup_styles(self):
        """스타일 설정"""
        pass

class RecentActivityWidget(QFrame):
    """최근 활동 위젯"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """UI 설정"""
        self.setProperty("class", "card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 헤더
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("최근 활동")
        title_label.setFont(font_loader.get_font('SemiBold', 16))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        view_all_btn = QPushButton("전체 보기")
        view_all_btn.setFont(font_loader.get_font('Regular', 12))
        view_all_btn.setProperty("class", "ghost")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(view_all_btn)
        
        # 활동 테이블
        self.activity_table = QTableWidget()
        self.setup_activity_table()
        
        layout.addLayout(header_layout)
        layout.addWidget(self.activity_table)
    
    def setup_activity_table(self):
        """활동 테이블 설정"""
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["시간", "환자명", "작업", "상태"])
        
        # 헤더 설정
        header = self.activity_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # 테이블 설정
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activity_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.activity_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.activity_table.setMaximumHeight(200)
        
        # 샘플 데이터 추가
        self.load_sample_data()
    
    def load_sample_data(self):
        """샘플 데이터 로드"""
        sample_data = [
            ("10:30", "홍길동", "X-ray 분석 완료", "✅ 성공"),
            ("10:15", "김철수", "얼굴 사진 업로드", "🔄 진행중"),
            ("09:45", "이영희", "PDF 다운로드", "✅ 성공"),
            ("09:30", "박민수", "환자 등록", "❌ 실패"),
            ("09:15", "최지영", "일괄 처리 시작", "✅ 성공")
        ]
        
        self.activity_table.setRowCount(len(sample_data))
        
        for row, (time, patient, task, status) in enumerate(sample_data):
            self.activity_table.setItem(row, 0, QTableWidgetItem(time))
            self.activity_table.setItem(row, 1, QTableWidgetItem(patient))
            self.activity_table.setItem(row, 2, QTableWidgetItem(task))
            self.activity_table.setItem(row, 3, QTableWidgetItem(status))
            
            # 상태별 색상 설정
            status_item = self.activity_table.item(row, 3)
            if "성공" in status:
                status_item.setForeground(QColor(COLORS['success_500']))
            elif "진행중" in status:
                status_item.setForeground(QColor(COLORS['info_500']))
            elif "실패" in status:
                status_item.setForeground(QColor(COLORS['error_500']))
    
    def setup_styles(self):
        """스타일 설정"""
        pass

class DashboardWidget(QWidget):
    """대시보드 메인 위젯"""
    
    def __init__(self):
        super().__init__()
        self.stats_cards = {}
        
        # 타이머 설정 (데이터 자동 새로고침)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # 30초마다 새로고침
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # 페이지 제목
        self.create_page_header(main_layout)
        
        # 통계 카드 섹션
        self.create_stats_section(main_layout)
        
        # 빠른 실행 및 최근 활동 섹션
        self.create_action_section(main_layout)
        
        # 시스템 상태 섹션
        self.create_system_status(main_layout)
        
        # 스트레치 추가
        main_layout.addStretch()
    
    def create_page_header(self, layout):
        """페이지 헤더 생성"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # 제목
        title_label = QLabel("대시보드")
        title_label.setFont(font_loader.get_font('Bold', 24))
        title_label.setStyleSheet(f"color: {COLORS['gray_800']};")
        
        # 부제목
        current_time = QDateTime.currentDateTime()
        subtitle_text = f"오늘 {current_time.toString('yyyy년 MM월 dd일')} 현황"
        subtitle_label = QLabel(subtitle_text)
        subtitle_label.setFont(font_loader.get_font('Regular', 14))
        subtitle_label.setStyleSheet(f"color: {COLORS['gray_500']};")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
    
    def create_stats_section(self, layout):
        """통계 카드 섹션 생성"""
        stats_layout = QGridLayout()
        stats_layout.setSpacing(16)
        
        # 통계 카드들 생성
        self.stats_cards['completed'] = StatCardWidget(
            "처리 완료", 0, "건", "✅", "success"
        )
        
        self.stats_cards['processing'] = StatCardWidget(
            "처리 중", 0, "건", "🔄", "info"
        )
        
        self.stats_cards['failed'] = StatCardWidget(
            "실패", 0, "건", "❌", "error"
        )
        
        self.stats_cards['total_time'] = StatCardWidget(
            "총 처리 시간", 0, "분", "⏱️", "primary"
        )
        
        # 그리드에 배치 (2x2)
        stats_layout.addWidget(self.stats_cards['completed'], 0, 0)
        stats_layout.addWidget(self.stats_cards['processing'], 0, 1)
        stats_layout.addWidget(self.stats_cards['failed'], 1, 0)
        stats_layout.addWidget(self.stats_cards['total_time'], 1, 1)
        
        layout.addLayout(stats_layout)
    
    def create_action_section(self, layout):
        """액션 섹션 생성"""
        action_layout = QHBoxLayout()
        action_layout.setSpacing(24)
        
        # 빠른 실행 위젯
        self.quick_action_widget = QuickActionWidget()
        # 시그널 연결은 MainWindow에서 처리
        
        # 최근 활동 위젯
        self.recent_activity_widget = RecentActivityWidget()
        
        # 레이아웃에 추가 (1:2 비율)
        action_layout.addWidget(self.quick_action_widget, 1)
        action_layout.addWidget(self.recent_activity_widget, 2)
        
        layout.addLayout(action_layout)
    
    def create_system_status(self, main_layout):
        """시스템 상태 섹션 생성"""
        status_frame = QFrame()
        status_frame.setProperty("class", "card")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 16, 20, 16)
        status_layout.setSpacing(16)
        
        # 제목
        status_title = QLabel("🔧 시스템 상태")
        status_title.setFont(font_loader.get_font('SemiBold', 16))
        status_title.setStyleSheet(f"color: {COLORS['gray_800']};")
        status_layout.addWidget(status_title)
        
        # 상태 정보 컨테이너
        status_info_layout = QVBoxLayout()
        status_info_layout.setSpacing(8)
        
        # WebCeph 연결 상태
        self.webceph_status = QLabel("• WebCeph 연결: 🟡 확인 중...")
        self.webceph_status.setFont(font_loader.get_font('Regular', 14))
        self.webceph_status.setStyleSheet(f"color: {COLORS['gray_600']};")
        status_info_layout.addWidget(self.webceph_status)
        
        # Upstage OCR API 상태
        self.ocr_status = QLabel("• Upstage OCR API: 🟡 확인 중...")
        self.ocr_status.setFont(font_loader.get_font('Regular', 14))
        self.ocr_status.setStyleSheet(f"color: {COLORS['gray_600']};")
        status_info_layout.addWidget(self.ocr_status)
        
        # Webhook 상태
        self.webhook_status = QLabel("• Make.com Webhook: 🟡 확인 중...")
        self.webhook_status.setFont(font_loader.get_font('Regular', 14))
        self.webhook_status.setStyleSheet(f"color: {COLORS['gray_600']};")
        status_info_layout.addWidget(self.webhook_status)
        
        # 저장 공간 상태
        self.storage_status = QLabel("• 로컬 저장 공간: 🟢 여유 공간 충분")
        self.storage_status.setFont(font_loader.get_font('Regular', 14))
        self.storage_status.setStyleSheet(f"color: {COLORS['gray_600']};")
        status_info_layout.addWidget(self.storage_status)
        
        status_layout.addLayout(status_info_layout)
        
        # 상태 새로고침 버튼
        refresh_button = QPushButton("🔄 상태 새로고침")
        refresh_button.setFont(font_loader.get_font('Medium', 14))
        refresh_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gray_100']};
                color: {COLORS['gray_700']};
                border: 1px solid {COLORS['gray_300']};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gray_200']};
            }}
        """)
        refresh_button.clicked.connect(self.refresh_system_status)
        status_layout.addWidget(refresh_button)
        
        main_layout.addWidget(status_frame)
        
        # 초기 상태 확인
        QTimer.singleShot(1000, self.refresh_system_status)
    
    def refresh_system_status(self):
        """시스템 상태 새로고침"""
        try:
            from pathlib import Path
            
            # WebCeph 설정 확인
            webceph_id, webceph_pw = config.get_credentials()
            if webceph_id and webceph_pw:
                self.webceph_status.setText("• WebCeph 연결: 🟢 설정 완료")
                self.webceph_status.setStyleSheet(f"color: {COLORS['success_500']};")
            else:
                self.webceph_status.setText("• WebCeph 연결: 🔴 설정 필요")
                self.webceph_status.setStyleSheet(f"color: {COLORS['error_500']};")
            
            # OCR API 설정 확인
            api_key = config.get_upstage_api_key()
            if api_key:
                self.ocr_status.setText("• Upstage OCR API: 🟢 설정 완료")
                self.ocr_status.setStyleSheet(f"color: {COLORS['success_500']};")
            else:
                self.ocr_status.setText("• Upstage OCR API: 🔴 설정 필요")
                self.ocr_status.setStyleSheet(f"color: {COLORS['error_500']};")
            
            # Webhook 설정 확인
            webhook_url = config.get('automation', 'webhook_url', '')
            if webhook_url:
                self.webhook_status.setText("• Make.com Webhook: 🟢 설정 완료")
                self.webhook_status.setStyleSheet(f"color: {COLORS['success_500']};")
            else:
                self.webhook_status.setText("• Make.com Webhook: 🟡 선택 사항")
                self.webhook_status.setStyleSheet(f"color: {COLORS['warning_500']};")
            
            # 저장 공간 확인
            import shutil
            try:
                total, used, free = shutil.disk_usage(Path.home())
                free_gb = free // (1024**3)
                if free_gb > 5:
                    self.storage_status.setText(f"• 로컬 저장 공간: 🟢 여유 ({free_gb:.1f}GB)")
                    self.storage_status.setStyleSheet(f"color: {COLORS['success_500']};")
                elif free_gb > 1:
                    self.storage_status.setText(f"• 로컬 저장 공간: 🟡 주의 ({free_gb:.1f}GB)")
                    self.storage_status.setStyleSheet(f"color: {COLORS['warning_500']};")
                else:
                    self.storage_status.setText(f"• 로컬 저장 공간: 🔴 부족 ({free_gb:.1f}GB)")
                    self.storage_status.setStyleSheet(f"color: {COLORS['error_500']};")
            except:
                self.storage_status.setText("• 로컬 저장 공간: 🟡 확인 불가")
                self.storage_status.setStyleSheet(f"color: {COLORS['warning_500']};")
                
        except Exception as e:
            print(f"시스템 상태 확인 오류: {e}")
    
    def load_initial_data(self):
        """초기 데이터 로드"""
        # 샘플 데이터로 초기화
        self.stats_cards['completed'].update_value(24)
        self.stats_cards['processing'].update_value(3)
        self.stats_cards['failed'].update_value(1)
        self.stats_cards['total_time'].update_value(125)
    
    def refresh_data(self):
        """데이터 새로고침"""
        # 실제 구현에서는 데이터베이스나 로그 파일에서 데이터 조회
        # 현재는 시뮬레이션을 위한 랜덤 값
        import random
        
        # 통계 업데이트 (약간의 변화)
        current_completed = int(self.stats_cards['completed'].value_label.text())
        if random.random() > 0.7:  # 30% 확률로 업데이트
            self.stats_cards['completed'].update_value(current_completed + random.randint(0, 2))
        
        current_processing = int(self.stats_cards['processing'].value_label.text())
        if random.random() > 0.8:  # 20% 확률로 업데이트
            self.stats_cards['processing'].update_value(max(0, current_processing + random.randint(-1, 1)))
    

    
    def get_today_stats(self):
        """오늘의 통계 데이터 반환"""
        return {
            'completed': int(self.stats_cards['completed'].value_label.text()),
            'processing': int(self.stats_cards['processing'].value_label.text()),
            'failed': int(self.stats_cards['failed'].value_label.text()),
            'total_time': int(self.stats_cards['total_time'].value_label.text())
        }
    
    def update_stats(self, stats_data):
        """통계 데이터 업데이트"""
        for key, value in stats_data.items():
            if key in self.stats_cards:
                self.stats_cards[key].update_value(value)
    
    def update_daily_stats(self):
        """일일 통계 업데이트"""
        try:
            # 실제 구현에서는 데이터베이스나 로그에서 통계를 가져옴
            # 현재는 간단한 증가로 시뮬레이션
            current_completed = int(self.stats_cards['completed'].value_label.text())
            self.stats_cards['completed'].update_value(current_completed + 1)
            
            # 최근 활동에 새 항목 추가
            current_time = QDateTime.currentDateTime().toString('HH:mm')
            self.add_recent_activity(
                current_time,
                "자동화 환자",
                "자동화 프로세스 완료",
                "✅ 성공"
            )
        except Exception as e:
            print(f"일일 통계 업데이트 오류: {e}")
    
    def add_recent_activity(self, time, patient, task, status):
        """최근 활동에 새 항목 추가"""
        try:
            table = self.recent_activity_widget.activity_table
            
            # 맨 위에 새 행 삽입
            table.insertRow(0)
            table.setItem(0, 0, QTableWidgetItem(time))
            table.setItem(0, 1, QTableWidgetItem(patient))
            table.setItem(0, 2, QTableWidgetItem(task))
            table.setItem(0, 3, QTableWidgetItem(status))
            
            # 상태별 색상 설정
            status_item = table.item(0, 3)
            if "성공" in status:
                status_item.setForeground(QColor(COLORS['success_500']))
            elif "진행중" in status:
                status_item.setForeground(QColor(COLORS['info_500']))
            elif "실패" in status:
                status_item.setForeground(QColor(COLORS['error_500']))
            
            # 최대 10개 항목만 유지
            if table.rowCount() > 10:
                table.removeRow(table.rowCount() - 1)
        except Exception as e:
            print(f"최근 활동 추가 오류: {e}")
    
    def showEvent(self, event):
        """위젯이 표시될 때 호출"""
        super().showEvent(event)
        self.refresh_data()
    
    def hideEvent(self, event):
        """위젯이 숨겨질 때 호출"""
        super().hideEvent(event) 