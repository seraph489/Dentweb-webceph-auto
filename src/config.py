"""
애플리케이션 설정 관리 모듈
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from cryptography.fernet import Fernet
import configparser

class Config:
    """애플리케이션 설정 관리 클래스"""
    
    def __init__(self):
        self.app_dir = Path.home() / "AppData" / "Local" / "WebCephAuto"
        self.config_file = self.app_dir / "config.ini"
        self.key_file = self.app_dir / "key.key"
        
        # 디렉토리 생성
        self.app_dir.mkdir(exist_ok=True)
        
        # 암호화 키 생성 또는 로드
        self._init_encryption()
        
        # 기본 설정 (API 키는 하드코딩하지 않음)
        self.default_settings = {
            'general': {
                'auto_login': 'false',
                'language': 'ko',
                'theme': 'light'
            },
            'paths': {
                'image_folder': str(Path.home() / "Documents" / "WebCephAuto" / "Images"),
                'pdf_folder': str(Path.home() / "Documents" / "WebCephAuto" / "Results"),
                'backup_folder': str(Path.home() / "Documents" / "WebCephAuto" / "Backup")
            },
            'webceph': {
                'url': 'https://www.webceph.com',
                'timeout': '30',
                'retry_count': '3'
            },
            'automation': {
                'auto_start': 'false',
                'batch_size': '5',
                'wait_time': '3'
            },
            'upstage': {
                'api_url': 'https://api.upstage.ai/v1/document-digitization',
                'timeout': '30'
            },
            'dentweb': {
                'screenshot_x': '400',
                'screenshot_y': '400',
                'screenshot_width': '400',
                'screenshot_height': '400'
            }
        }
        
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _init_encryption(self):
        """암호화 키 초기화"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def _load_config(self):
        """설정 파일 로드"""
        if self.config_file.exists():
            self.config.read(self.config_file, encoding='utf-8')
        else:
            # 기본 설정으로 초기화
            for section, settings in self.default_settings.items():
                self.config.add_section(section)
                for key, value in settings.items():
                    self.config.set(section, key, value)
            self.save_config()
    
    def save_config(self):
        """설정 파일 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback: str = None) -> str:
        """설정 값 가져오기"""
        return self.config.get(section, key, fallback=fallback)
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """boolean 설정 값 가져오기"""
        value = self.config.get(section, key, fallback=str(fallback).lower())
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """정수 값 가져오기"""
        try:
            value = self.get(section, key, str(default))
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def set(self, section: str, key: str, value: str):
        """설정 값 저장"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save_config()
    
    def encrypt_data(self, data: str) -> str:
        """데이터 암호화"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def save_credentials(self, username: str, password: str):
        """로그인 정보 암호화 저장"""
        encrypted_username = self.encrypt_data(username)
        encrypted_password = self.encrypt_data(password)
        
        self.set('credentials', 'username', encrypted_username)
        self.set('credentials', 'password', encrypted_password)
    
    def get_credentials(self) -> tuple:
        """저장된 로그인 정보 가져오기"""
        try:
            encrypted_username = self.get('credentials', 'username')
            encrypted_password = self.get('credentials', 'password')
            
            if encrypted_username and encrypted_password:
                username = self.decrypt_data(encrypted_username)
                password = self.decrypt_data(encrypted_password)
                return username, password
        except Exception:
            pass
        return None, None
    
    def save_airtable_api_key(self, api_key: str):
        """Airtable API 키 암호화 저장"""
        encrypted_key = self.encrypt_data(api_key)
        self.set('airtable', 'api_key', encrypted_key)
    
    def get_airtable_api_key(self) -> str:
        """Airtable API 키 가져오기"""
        try:
            encrypted_key = self.get('airtable', 'api_key')
            if encrypted_key:
                return self.decrypt_data(encrypted_key)
        except Exception:
            pass
        return None
    
    def save_upstage_api_key(self, api_key: str):
        """Upstage API 키 암호화 저장"""
        if api_key and api_key.strip():
            encrypted_key = self.encrypt_data(api_key.strip())
            self.set('upstage', 'api_key', encrypted_key)
        else:
            # 빈 키인 경우 설정에서 제거
            if self.config.has_option('upstage', 'api_key'):
                self.config.remove_option('upstage', 'api_key')
                self.save_config()
    
    def get_upstage_api_key(self) -> str:
        """Upstage API 키 가져오기"""
        try:
            encrypted_key = self.get('upstage', 'api_key', '')
            if encrypted_key:
                decrypted_key = self.decrypt_data(encrypted_key)
                return decrypted_key if decrypted_key else ''
        except Exception as e:
            print(f"API 키 복호화 실패: {e}")
        return ''
    
    def create_directories(self):
        """필요한 디렉토리 생성"""
        dirs = [
            self.get('paths', 'image_folder'),
            self.get('paths', 'pdf_folder'),
            self.get('paths', 'backup_folder')
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

# 전역 설정 인스턴스
config = Config() 