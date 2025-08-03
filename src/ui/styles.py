"""
PyQt5 스타일시트 정의
Design Guide의 컬러 팔레트와 디자인 원칙을 적용
"""

# 컬러 팔레트 (Design Guide 기준)
COLORS = {
    'primary': {
        '50': '#EFF6FF',
        '100': '#DBEAFE', 
        '200': '#BFDBFE',
        '300': '#93C5FD',
        '400': '#60A5FA',
        '500': '#3B82F6',  # 메인 컬러
        '600': '#2563EB',
        '700': '#1D4ED8',
        '800': '#1E40AF',
        '900': '#1E3A8A',
    },
    'gray': {
        '50': '#F9FAFB',
        '100': '#F3F4F6',
        '200': '#E5E7EB',
        '300': '#D1D5DB',
        '400': '#9CA3AF',
        '500': '#6B7280',
        '600': '#4B5563',
        '700': '#374151',
        '800': '#1F2937',
        '900': '#111827',
    },
    'success': {
        '500': '#10B981',
        '600': '#059669',
        '700': '#047857',
    },
    'warning': {
        '500': '#F59E0B',
    },
    'error': {
        '500': '#EF4444',
    },
    'info': {
        '500': '#3B82F6',
    },
    # 기존 호환성을 위한 별칭
    'primary_50': '#EFF6FF',
    'primary_100': '#DBEAFE',
    'primary_200': '#BFDBFE',
    'primary_300': '#93C5FD',
    'primary_400': '#60A5FA',
    'primary_500': '#3B82F6',
    'primary_600': '#2563EB',
    'primary_700': '#1D4ED8',
    'primary_800': '#1E40AF',
    'primary_900': '#1E3A8A',
    'gray_50': '#F9FAFB',
    'gray_100': '#F3F4F6',
    'gray_200': '#E5E7EB',
    'gray_300': '#D1D5DB',
    'gray_400': '#9CA3AF',
    'gray_500': '#6B7280',
    'gray_600': '#4B5563',
    'gray_700': '#374151',
    'gray_800': '#1F2937',
    'gray_900': '#111827',
    'success_500': '#10B981',
    'success_600': '#059669',
    'success_700': '#047857',
    'warning_500': '#F59E0B',
    'error_500': '#EF4444',
    'info_500': '#3B82F6',
    'white': '#FFFFFF',
    'black': '#000000'
}

def get_main_stylesheet():
    """메인 애플리케이션 스타일시트"""
    return f"""
    /* 전체 애플리케이션 스타일 */
    QMainWindow {{
        background-color: {COLORS['gray_50']};
        color: {COLORS['gray_800']};
    }}
    
    /* 사이드바 스타일 */
    QFrame#sidebar {{
        background-color: {COLORS['white']};
        border-right: 1px solid {COLORS['gray_200']};
    }}
    
    /* 메인 콘텐츠 영역 */
    QFrame#main_content {{
        background-color: {COLORS['gray_50']};
        padding: 24px;
    }}
    
    /* 카드 스타일 */
    QFrame.card {{
        background-color: {COLORS['white']};
        border: 1px solid {COLORS['gray_200']};
        border-radius: 8px;
        padding: 24px;
    }}
    
    /* 제목 레이블 */
    QLabel.title {{
        font-size: 24px;
        font-weight: bold;
        color: {COLORS['gray_800']};
        margin-bottom: 8px;
    }}
    
    QLabel.subtitle {{
        font-size: 16px;
        font-weight: 600;
        color: {COLORS['gray_700']};
        margin-bottom: 16px;
    }}
    
    QLabel.text {{
        font-size: 14px;
        color: {COLORS['gray_600']};
        line-height: 1.5;
    }}
    
    QLabel.small {{
        font-size: 12px;
        color: {COLORS['gray_500']};
    }}
    
    /* 입력 필드 스타일 */
    QLineEdit, QTextEdit, QComboBox {{
        background-color: {COLORS['white']};
        border: 1px solid {COLORS['gray_300']};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 14px;
        color: {COLORS['gray_700']};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 2px solid {COLORS['primary_500']};
        outline: none;
    }}
    
    QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{
        background-color: {COLORS['gray_100']};
        color: {COLORS['gray_400']};
    }}
    
    /* 버튼 스타일 */
    QPushButton.primary {{
        background-color: {COLORS['primary_500']};
        color: {COLORS['white']};
        border: none;
        border-radius: 6px;
        padding: 12px 24px;
        font-size: 14px;
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
    
    QPushButton.secondary {{
        background-color: {COLORS['white']};
        color: {COLORS['primary_500']};
        border: 1px solid {COLORS['primary_500']};
        border-radius: 6px;
        padding: 12px 24px;
        font-size: 14px;
        font-weight: 600;
    }}
    
    QPushButton.secondary:hover {{
        background-color: {COLORS['primary_50']};
    }}
    
    QPushButton.ghost {{
        background-color: transparent;
        color: {COLORS['gray_600']};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
    }}
    
    QPushButton.ghost:hover {{
        background-color: {COLORS['gray_100']};
        color: {COLORS['gray_800']};
    }}
    
    /* 네비게이션 버튼 */
    QPushButton.nav_button {{
        background-color: transparent;
        color: {COLORS['gray_600']};
        border: none;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 14px;
        font-weight: 500;
        text-align: left;
    }}
    
    QPushButton.nav_button:hover {{
        background-color: {COLORS['gray_100']};
        color: {COLORS['gray_800']};
    }}
    
    QPushButton.nav_button:checked {{
        background-color: {COLORS['primary_100']};
        color: {COLORS['primary_700']};
        font-weight: 600;
    }}
    
    /* 프로그레스 바 */
    QProgressBar {{
        background-color: {COLORS['gray_200']};
        border: none;
        border-radius: 4px;
        height: 8px;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['primary_500']};
        border-radius: 4px;
    }}
    
    /* 테이블 스타일 */
    QTableWidget {{
        background-color: {COLORS['white']};
        border: 1px solid {COLORS['gray_200']};
        border-radius: 8px;
        gridline-color: {COLORS['gray_200']};
    }}
    
    QTableWidget QHeaderView::section {{
        background-color: {COLORS['gray_100']};
        border: none;
        border-bottom: 1px solid {COLORS['gray_200']};
        padding: 12px;
        font-weight: 600;
        color: {COLORS['gray_700']};
    }}
    
    QTableWidget::item {{
        padding: 12px;
        border-bottom: 1px solid {COLORS['gray_200']};
    }}
    
    QTableWidget::item:selected {{
        background-color: {COLORS['primary_50']};
        color: {COLORS['primary_700']};
    }}
    
    /* 스크롤바 스타일 */
    QScrollBar:vertical {{
        background-color: {COLORS['gray_100']};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['gray_300']};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['gray_400']};
    }}
    
    /* 체크박스 스타일 */
    QCheckBox {{
        color: {COLORS['gray_700']};
        font-size: 14px;
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLORS['gray_300']};
        border-radius: 4px;
        background-color: {COLORS['white']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {COLORS['primary_500']};
        border-color: {COLORS['primary_500']};
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik04LjUgMUwyLjc1IDYuNzUgMS41IDUuNSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
    }}
    
    /* 메시지 박스 스타일 */
    QMessageBox {{
        background-color: {COLORS['white']};
        color: {COLORS['gray_800']};
    }}
    
    QMessageBox QPushButton {{
        min-width: 80px;
        padding: 8px 16px;
    }}
    """

def get_status_styles():
    """상태별 스타일"""
    return f"""
    /* 성공 상태 */
    .status-success {{
        color: {COLORS['success_500']};
        background-color: rgba(16, 185, 129, 0.1);
        border: 1px solid {COLORS['success_500']};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    
    /* 경고 상태 */
    .status-warning {{
        color: {COLORS['warning_500']};
        background-color: rgba(245, 158, 11, 0.1);
        border: 1px solid {COLORS['warning_500']};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    
    /* 오류 상태 */
    .status-error {{
        color: {COLORS['error_500']};
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid {COLORS['error_500']};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    
    /* 정보 상태 */
    .status-info {{
        color: {COLORS['info_500']};
        background-color: rgba(59, 130, 246, 0.1);
        border: 1px solid {COLORS['info_500']};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    """

def get_animation_styles():
    """애니메이션 스타일"""
    return """
    /* 로딩 애니메이션 */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .spinning {
        animation: spin 1s linear infinite;
    }
    
    /* 페이드 인 애니메이션 */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-in-out;
    }
    """ 