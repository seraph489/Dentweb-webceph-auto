"""
한국어 폰트 로더 모듈
public 폴더의 폰트를 로드하여 PyQt5에서 사용
"""

import os
import sys
from pathlib import Path
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtCore import QDir

class FontLoader:
    """한국어 폰트 로더 클래스"""
    
    def __init__(self):
        self.font_db = None
        self.loaded_fonts = {}
        self.base_path = self._get_base_path()
        
    def _get_base_path(self):
        """실행 파일의 기본 경로 가져오기"""
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 경우
            return Path(sys._MEIPASS)
        else:
            # 개발 환경
            return Path(__file__).parent.parent.parent
    
    def load_korean_fonts(self):
        """한국어 폰트 로드"""
        # QFontDatabase 초기화 (QApplication 생성 후에 호출됨)
        if self.font_db is None:
            self.font_db = QFontDatabase()
            
        font_dirs = [
            self.base_path / "public" / "Pretendard-1.3.9" / "public" / "static",
            self.base_path / "public" / "Noto_Sans_KR" / "static"
        ]
        
        # Pretendard 폰트 로드
        pretendard_dir = font_dirs[0]
        if pretendard_dir.exists():
            self._load_pretendard_fonts(pretendard_dir)
        
        # Noto Sans KR 폰트 로드
        noto_dir = font_dirs[1]
        if noto_dir.exists():
            self._load_noto_fonts(noto_dir)
    
    def _load_pretendard_fonts(self, font_dir):
        """Pretendard 폰트 로드"""
        pretendard_files = {
            'Pretendard-Light.otf': 'Pretendard Light',
            'Pretendard-Regular.otf': 'Pretendard Regular',
            'Pretendard-Medium.otf': 'Pretendard Medium',
            'Pretendard-SemiBold.otf': 'Pretendard SemiBold',
            'Pretendard-Bold.otf': 'Pretendard Bold'
        }
        
        for file_name, font_name in pretendard_files.items():
            font_path = font_dir / file_name
            if font_path.exists():
                font_id = self.font_db.addApplicationFont(str(font_path))
                if font_id != -1:
                    families = self.font_db.applicationFontFamilies(font_id)
                    if families:
                        self.loaded_fonts[font_name] = families[0]
                        print(f"✓ Pretendard 폰트 로드: {font_name} -> {families[0]}")
    
    def _load_noto_fonts(self, font_dir):
        """Noto Sans KR 폰트 로드"""
        noto_files = {
            'NotoSansKR-Light.ttf': 'Noto Sans KR Light',
            'NotoSansKR-Regular.ttf': 'Noto Sans KR Regular',
            'NotoSansKR-Medium.ttf': 'Noto Sans KR Medium',
            'NotoSansKR-SemiBold.ttf': 'Noto Sans KR SemiBold',
            'NotoSansKR-Bold.ttf': 'Noto Sans KR Bold'
        }
        
        for file_name, font_name in noto_files.items():
            font_path = font_dir / file_name
            if font_path.exists():
                font_id = self.font_db.addApplicationFont(str(font_path))
                if font_id != -1:
                    families = self.font_db.applicationFontFamilies(font_id)
                    if families:
                        self.loaded_fonts[font_name] = families[0]
                        print(f"✓ Noto Sans KR 폰트 로드: {font_name} -> {families[0]}")
    
    def get_font(self, weight='Regular', size=10):
        """폰트 객체 가져오기"""
        # Pretendard 우선, 없으면 Noto Sans KR
        font_name = None
        
        if weight == 'Light':
            font_name = self.loaded_fonts.get('Pretendard Light') or self.loaded_fonts.get('Noto Sans KR Light')
        elif weight == 'Regular':
            font_name = self.loaded_fonts.get('Pretendard Regular') or self.loaded_fonts.get('Noto Sans KR Regular')
        elif weight == 'Medium':
            font_name = self.loaded_fonts.get('Pretendard Medium') or self.loaded_fonts.get('Noto Sans KR Medium')
        elif weight == 'SemiBold':
            font_name = self.loaded_fonts.get('Pretendard SemiBold') or self.loaded_fonts.get('Noto Sans KR SemiBold')
        elif weight == 'Bold':
            font_name = self.loaded_fonts.get('Pretendard Bold') or self.loaded_fonts.get('Noto Sans KR Bold')
        
        if font_name:
            font = QFont(font_name, size)
            return font
        else:
            # 폴백: 시스템 기본 한국어 폰트
            font = QFont("맑은 고딕", size)
            return font
    
    def get_available_fonts(self):
        """로드된 폰트 목록 반환"""
        return list(self.loaded_fonts.keys())

# 전역 폰트 로더 인스턴스
font_loader = FontLoader() 