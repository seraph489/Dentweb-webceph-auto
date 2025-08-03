#!/usr/bin/env python3
"""
WebCeph 자동화 모듈

웹셉(WebCeph) 플랫폼에서 환자 등록, 이미지 업로드, 분석 실행을 자동화하는 모듈입니다.

주요 기능:
- 자동 로그인 및 세션 관리
- 신규 환자 등록 및 자동 감지/선택 ✨ NEW!
- 이미지 업로드 (X-ray, 얼굴 사진)
- 분석 시작 및 완료 대기
- PDF 결과 다운로드

신규 환자 자동 감지 기능:
- 웹셉에서 새로운 환자 생성 후 자동으로 최상단의 신규 ID를 감지
- 환자 정보 매칭을 통한 정확한 환자 선택
- 검색 기능과 목록 스캔을 통한 다중 감지 방법

사용법:
    # 기본 프로세스 (신규 환자 감지 포함)
    automation = WebCephAutomation()
    result = automation.process_patient(patient_data, images)
    
    # 신규 환자 전용 프로세스
    result = automation.process_new_patient(patient_data, images)
    
    # 간단한 생성 및 선택
    automation.create_and_select_new_patient(patient_data)

Version: 1.0.0 (신규 환자 자동 감지 기능 추가)
Author: Web Ceph Auto Team
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (TimeoutException, NoSuchElementException, 
                                       WebDriverException, ElementNotInteractableException)
from webdriver_manager.chrome import ChromeDriverManager

from ..config import config

class WebCephAutomation:
    """Web Ceph 자동화 클래스"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.logger = self._setup_logger()
        self.config = config
        
        # 설정값 로드
        self.timeout = int(self.config.get('webceph', 'timeout', '15'))  # 30초 → 15초로 단축
        self.retry_count = int(self.config.get('webceph', 'retry_count', '3'))
        self.wait_time = int(self.config.get('automation', 'wait_time', '1'))  # 3초 → 1초로 단축
        
    def _setup_logger(self):
        """로거 설정"""
        logger = logging.getLogger('WebCephAutomation')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 파일 핸들러
            log_dir = Path.home() / "AppData" / "Local" / "WebCephAuto" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"automation_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 포맷터
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def initialize_browser(self):
        """브라우저 초기화 (안정성 향상 버전)"""
        try:
            self.logger.info("브라우저를 초기화합니다...")
            
            # Chrome 옵션 설정 (안정성 및 호환성 향상)
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 다운로드 설정
            pdf_folder = self.config.get('paths', 'pdf_folder')
            if not pdf_folder:
                # 기본 다운로드 폴더 설정
                pdf_folder = str(Path.home() / "Documents" / "WebCephAuto" / "Results")
                Path(pdf_folder).mkdir(parents=True, exist_ok=True)
                
            prefs = {
                "download.default_directory": pdf_folder,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # ChromeDriver 자동 다운로드 및 설정 (안정성 향상)
            try:
                self.logger.info("Chrome 브라우저 버전을 확인하고 호환 ChromeDriver를 다운로드합니다...")
                
                # 1. 먼저 자동 버전 매칭 시도 (가장 안정적)
                service = Service(ChromeDriverManager().install())
                self.logger.info("ChromeDriver 자동 다운로드 성공")
                
            except Exception as e:
                self.logger.warning(f"자동 다운로드 실패, 수동 버전 확인 시도: {e}")
                try:
                    # 2. Chrome 버전 수동 확인 후 다운로드
                    import subprocess
                    
                    # Windows에서 Chrome 버전 확인 (여러 경로 시도)
                    chrome_paths = [
                        r'HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon',
                        r'HKEY_LOCAL_MACHINE\SOFTWARE\Google\Chrome\BLBeacon',
                        r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon'
                    ]
                    
                    chrome_version = None
                    for path in chrome_paths:
                        try:
                            result = subprocess.run(['reg', 'query', path, '/v', 'version'], 
                                                  capture_output=True, text=True, timeout=10)
                            if result.returncode == 0 and 'version' in result.stdout:
                                version_line = [line for line in result.stdout.split('\n') if 'version' in line.lower()]
                                if version_line:
                                    chrome_version = version_line[0].split()[-1]
                                    break
                        except:
                            continue
                    
                    if chrome_version:
                        major_version = chrome_version.split('.')[0]
                        self.logger.info(f"감지된 Chrome 버전: {chrome_version} (메이저: {major_version})")
                        
                        # 메이저 버전 기반 다운로드 (더 유연한 방식)
                        try:
                            service = Service(ChromeDriverManager(version="latest").install())
                            self.logger.info(f"최신 ChromeDriver 다운로드 성공")
                        except:
                            # 마지막 수단: 캐시된 버전 사용
                            service = Service(ChromeDriverManager(cache_valid_range=365).install())
                            self.logger.info("캐시된 ChromeDriver 사용")
                    else:
                        # Chrome 버전 감지 실패 시 최신 버전 다운로드
                        self.logger.warning("Chrome 버전 감지 실패, 최신 버전 다운로드 시도")
                        service = Service(ChromeDriverManager(version="latest").install())
                        
                except Exception as e2:
                    self.logger.error(f"ChromeDriver 다운로드 완전 실패: {e2}")
                    # 마지막 수단: 시스템에 설치된 chromedriver 사용 시도
                    try:
                        import shutil
                        chromedriver_path = shutil.which('chromedriver')
                        if chromedriver_path:
                            self.logger.info(f"시스템 ChromeDriver 사용: {chromedriver_path}")
                            service = Service(chromedriver_path)
                        else:
                            raise Exception("ChromeDriver를 찾을 수 없습니다. Chrome 브라우저가 설치되어 있는지 확인해주세요.")
                    except Exception as e3:
                        self.logger.error(f"시스템 ChromeDriver 검색 실패: {e3}")
                        raise Exception(f"ChromeDriver 초기화에 완전히 실패했습니다: {e2}")
            
            # 브라우저 실행
            self.logger.info("Chrome 브라우저 시작 중...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 브라우저 설정
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            
            # WebDriverWait 설정
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            # 초기화 검증
            self.logger.info("브라우저 초기화 검증 중...")
            self.driver.get("https://www.google.com")
            time.sleep(0.5)  # 2초 → 0.5초로 단축
            
            self.logger.info("브라우저가 성공적으로 초기화되었습니다")
            return True
            
        except Exception as e:
            error_msg = f"브라우저 초기화 실패: {str(e)}"
            self.logger.error(error_msg)
            
            # 정리 작업
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                
            raise Exception(error_msg)
    
    def login(self, username, password):
        """Web Ceph 로그인 - 순차적 단계별 진행"""
        try:
            self.logger.info("🚀 Web Ceph 자동 로그인을 시작합니다...")
            
            # Web Ceph 메인 페이지로 이동
            webceph_url = self.config.get('webceph', 'url', 'https://www.webceph.com')
            self.logger.info(f"🌐 Web Ceph 접속: {webceph_url}")
            
            self.driver.get(webceph_url)
            time.sleep(self.wait_time)
            
            # 1단계: 로그인 링크 찾기 및 클릭
            self.logger.info("📝 1단계: 로그인 링크를 찾아 클릭합니다...")
            login_clicked = self._click_login_link()
            
            if login_clicked:
                self.logger.info("✅ 로그인 페이지로 이동했습니다")
            else:
                self.logger.info("ℹ️ 이미 로그인 페이지에 있습니다")
            
            # 2단계: 이메일과 비밀번호 입력
            self.logger.info("✏️ 2단계: 저장된 이메일과 비밀번호를 입력합니다...")
            self._input_credentials(username, password)
            
            # 3단계: 로그인 버튼 클릭  
            self.logger.info("🔐 3단계: 로그인 버튼을 클릭합니다...")
            login_success = self._click_login_button()
            
            if login_success:
                self.logger.info("✅ 로그인이 완료되었습니다!")
                return True
            else:
                raise Exception("로그인에 실패했습니다")
                
        except Exception as e:
            self.logger.error(f"❌ 로그인 실패: {str(e)}")
            raise
    
    def _click_login_link(self):
        """로그인 링크 클릭"""
        try:
            # 먼저 현재 페이지에 로그인 폼이 있는지 확인
            try:
                email_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[type='text']")
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                if email_field and password_field:
                    self.logger.info("🔍 현재 페이지에 로그인 폼이 이미 있습니다")
                    return True  # 이미 로그인 페이지에 있음
            except:
                pass
            
            # 로그인 링크 찾기 및 클릭
            login_link_patterns = [
                (By.LINK_TEXT, "로그인"),
                (By.PARTIAL_LINK_TEXT, "로그인"),
                (By.XPATH, "//a[contains(text(), '로그인')]"),
                (By.XPATH, "//button[contains(text(), '로그인')]"),
                (By.CSS_SELECTOR, "a[href*='login']"),
                (By.CSS_SELECTOR, "a[href*='/login']"),
                (By.XPATH, "//a[@href='/login']"),
                (By.XPATH, "//a[@href='#login']"),
                # 영어 버전도 지원
                (By.LINK_TEXT, "Login"),
                (By.PARTIAL_LINK_TEXT, "Login"),
                (By.XPATH, "//a[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Login')]")
            ]
            
            for by, selector in login_link_patterns:
                try:
                    login_link = self.wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    login_link.click()
                    self.logger.info(f"✅ 로그인 링크 클릭: {selector}")
                    time.sleep(0.5)  # 2초 → 0.5초로 단축
                    return True
                except:
                    continue
            
            self.logger.info("🔍 로그인 링크를 찾지 못했습니다. 현재 페이지에서 로그인을 시도합니다.")
            return True  # 링크를 못 찾아도 현재 페이지에서 로그인 시도
            
        except Exception as e:
            self.logger.warning(f"로그인 링크 클릭 실패: {str(e)}")
            return True  # 실패해도 계속 진행
    
    def _input_credentials(self, username, password):
        """이메일과 비밀번호 입력"""
        try:
            # 이메일 필드 찾기 및 입력
            email_field = self._find_email_field()
            if email_field:
                email_field.clear()
                email_field.send_keys(username)
                self.logger.info(f"📧 이메일 입력 완료: {username}")
                time.sleep(1)
            else:
                raise Exception("이메일 입력 필드를 찾을 수 없습니다")
            
            # 비밀번호 필드 찾기 및 입력
            password_field = self._find_password_field()
            if password_field:
                password_field.clear()
                password_field.send_keys(password)
                self.logger.info("🔒 비밀번호 입력 완료")
                time.sleep(1)
            else:
                raise Exception("비밀번호 입력 필드를 찾을 수 없습니다")
                
        except Exception as e:
            self.logger.error(f"정보 입력 실패: {str(e)}")
            raise
    
    def _find_email_field(self):
        """이메일 필드 찾기"""
        email_patterns = [
            # WebCeph 특화 패턴 (개발자 도구에서 확인된 정확한 선택자)
            (By.ID, "id_email"),
            (By.CSS_SELECTOR, "input#id_email.textinput.form-control"),
            (By.CSS_SELECTOR, "#id_email"),
            (By.CSS_SELECTOR, "input.textinput.form-control"),
            # 백업 패턴들
            (By.XPATH, "//input[preceding-sibling::*[contains(text(), '이메일')]]"),
            (By.XPATH, "//label[contains(text(), '이메일')]/following-sibling::input"),
            (By.XPATH, "//label[contains(text(), '이메일')]/parent::*/input"),
            # 일반적인 이메일 필드 패턴
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='이메일']"),
            (By.CSS_SELECTOR, "input[placeholder*='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='Email']"),
            # name/id 속성 기반
            (By.NAME, "email"),
            (By.NAME, "username"),
            (By.NAME, "user_email"),
            (By.ID, "email"),
            (By.ID, "username"),
            (By.ID, "user_email"),
            # 첫 번째 텍스트 입력 필드 (마지막 대안)
            (By.CSS_SELECTOR, "input[type='text']:first-of-type"),
            (By.CSS_SELECTOR, "input:not([type]):first-of-type")
        ]
        
        for by, selector in email_patterns:
            try:
                field = self.wait.until(
                    EC.presence_of_element_located((by, selector))
                )
                self.logger.info(f"✅ 이메일 필드 발견: {selector}")
                return field
            except:
                continue
        
        return None
    
    def _find_password_field(self):
        """비밀번호 필드 찾기"""
        password_patterns = [
            # WebCeph 특화 패턴 (개발자 도구에서 확인된 정확한 선택자)
            (By.ID, "id_password"),
            (By.CSS_SELECTOR, "input#id_password.passwordinput.form-control"),
            (By.CSS_SELECTOR, "#id_password"),
            (By.CSS_SELECTOR, "input.passwordinput.form-control"),
            # 백업 패턴들
            (By.XPATH, "//input[preceding-sibling::*[contains(text(), '비밀번호')]]"),
            (By.XPATH, "//label[contains(text(), '비밀번호')]/following-sibling::input"),
            (By.XPATH, "//label[contains(text(), '비밀번호')]/parent::*/input"),
            # 일반적인 비밀번호 필드 패턴
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[placeholder*='비밀번호']"),
            (By.CSS_SELECTOR, "input[placeholder*='password']"),
            (By.CSS_SELECTOR, "input[placeholder*='Password']"),
            # name/id 속성 기반
            (By.NAME, "password"),
            (By.NAME, "passwd"),
            (By.NAME, "user_password"),
            (By.ID, "password"),
            (By.ID, "passwd"),
            (By.ID, "user_password")
        ]
        
        for by, selector in password_patterns:
            try:
                field = self.driver.find_element(by, selector)
                self.logger.info(f"✅ 비밀번호 필드 발견: {selector}")
                return field
            except:
                continue
        
        return None
    
    def _click_login_button(self):
        """로그인 버튼 클릭"""
        try:
            login_button_patterns = [
                # WebCeph 특화 패턴 (개발자 도구에서 확인된 정확한 선택자)
                (By.CSS_SELECTOR, "input.btn.btn-home-color.btn-block"),
                (By.CSS_SELECTOR, "input[name='로그인']"),
                (By.XPATH, "//input[@name='로그인']"),
                (By.CSS_SELECTOR, "input.btn-home-color"),
                (By.CSS_SELECTOR, "input.btn-block"),
                # 백업 패턴들
                (By.XPATH, "//button[contains(text(), '로그인')]"),
                (By.XPATH, "//button[text()='로그인']"),
                (By.XPATH, "//input[@value='로그인']"),
                # 일반적인 로그인 버튼 패턴
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'login')]"),
                (By.XPATH, "//button[text()='Login']"),
                (By.XPATH, "//input[@value='Login']"),
                # CSS 클래스 기반
                (By.CSS_SELECTOR, ".login-button"),
                (By.CSS_SELECTOR, ".btn-login"),
                (By.CSS_SELECTOR, "#login-button"),
                (By.CSS_SELECTOR, "#loginButton"),
                # 폼 내의 첫 번째 submit 버튼 (마지막 대안)
                (By.CSS_SELECTOR, "form button[type='submit']:first-of-type"),
                (By.CSS_SELECTOR, "form input[type='submit']:first-of-type")
            ]
            
            for by, selector in login_button_patterns:
                try:
                    button = self.driver.find_element(by, selector)
                    if button and button.is_enabled() and button.is_displayed():
                        button.click()
                        self.logger.info(f"✅ 로그인 버튼 클릭 성공: {selector}")
                        time.sleep(1)  # 3초 → 1초로 단축  # 로그인 처리 대기
                        
                        # 로그인 성공 확인
                        if self._check_login_success():
                            self.logger.info("🎉 로그인이 성공적으로 완료되었습니다!")
                            return True
                        else:
                            self.logger.info("🔄 로그인 처리 중...")
                            return True  # 일단 성공으로 간주하고 다음 단계로
                        break
                except Exception as e:
                    continue
            
            self.logger.warning("⚠️ 로그인 버튼을 찾을 수 없습니다")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 로그인 버튼 클릭 실패: {str(e)}")
            return False
    
    def click_new_patient_button(self):
        """신규 환자 입력 버튼 클릭"""
        try:
            self.logger.info("🆕 신규 환자 입력 버튼을 찾습니다...")
            
            # 신규 환자 버튼 패턴들 (실제 WebCeph 화면에서 확인된 선택자)
            new_patient_patterns = [
                # WebCeph 특화 패턴 (실제 화면에서 확인)
                (By.XPATH, "//span[contains(text(), '+ 신규 환자')]"),
                (By.XPATH, "//button[contains(text(), '+ 신규 환자')]"),
                (By.XPATH, "//a[contains(text(), '+ 신규 환자')]"),
                (By.CSS_SELECTOR, "span[class*='full-text']"),
                # 백업 패턴들
                (By.XPATH, "//span[contains(text(), '신규 환자')]"),
                (By.XPATH, "//button[contains(text(), '신규 환자')]"),
                (By.XPATH, "//a[contains(text(), '신규 환자')]"),
                (By.XPATH, "//span[contains(text(), '신규 등록')]"),
                (By.XPATH, "//button[contains(text(), '신규 등록')]"),
                (By.XPATH, "//a[contains(text(), '신규 등록')]"),
                (By.XPATH, "//button[contains(text(), '+ 신규 등록')]"),
                (By.XPATH, "//a[contains(text(), '+ 신규 등록')]"),
                (By.CSS_SELECTOR, ".btn-primary"),
                (By.PARTIAL_LINK_TEXT, "신규"),
                (By.PARTIAL_LINK_TEXT, "등록")
            ]
            
            for by, selector in new_patient_patterns:
                try:
                    button = self.wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    button.click()
                    self.logger.info(f"✅ 신규 환자 버튼 클릭 성공: {selector}")
                    time.sleep(0.5)  # 폼 로딩 대기 (1초 → 0.5초로 추가 단축)
                    return True
                except:
                    continue
            
            raise Exception("신규 환자 입력 버튼을 찾을 수 없습니다")
            
        except Exception as e:
            self.logger.error(f"신규 환자 버튼 클릭 실패: {str(e)}")
            raise
    
    def fill_patient_form(self, patient_data):
        """신규 환자 폼 작성"""
        try:
            self.logger.info("📋 신규 환자 폼 작성을 시작합니다...")
            time.sleep(1)  # 3초 → 1초로 단축
            # 1. 환자 ID 입력
            if patient_data.get('chart_no'):
                self._fill_patient_id(patient_data['chart_no'])
            # 2. 이름 입력 (first_name)
            if patient_data.get('first_name'):
                try:
                    first_name_field = self.driver.find_element(By.ID, "id_first_name")
                    first_name_field.clear()
                    first_name_field.send_keys(patient_data['first_name'])
                    self.logger.info(f"✅ 이름 입력 완료: {patient_data['first_name']}")
                except Exception as e:
                    self.logger.warning(f"이름 입력 실패(id_first_name): {e}")
            # 3. 성 입력 (last_name)
            if patient_data.get('last_name'):
                try:
                    last_name_field = self.driver.find_element(By.ID, "id_last_name")
                    last_name_field.clear()
                    last_name_field.send_keys(patient_data['last_name'])
                    self.logger.info(f"✅ 성 입력 완료: {patient_data['last_name']}")
                except Exception as e:
                    self.logger.warning(f"성 입력 실패(id_last_name): {e}")
            # 4. 이름/성 통합 입력(백업)
            if patient_data.get('name'):
                self._fill_patient_name(patient_data['name'])
            # 5. 인종 선택
            self._select_race_asian()
            # 6. 성별 선택
            if patient_data.get('gender'):
                self._select_gender(patient_data['gender'])
            # 7. 생년월일 입력
            if patient_data.get('birth_date'):
                self._fill_birth_date(patient_data['birth_date'])
            # 8. 동의 체크박스 체크
            self._check_agreement()
            # 9. 만들기 버튼 클릭
            self._click_create_button()
            self.logger.info("✅ 신규 환자 폼 작성이 완료되었습니다!")
            return True
        except Exception as e:
            self.logger.error(f"❌ 신규 환자 폼 작성 실패: {str(e)}")
            raise
    
    def _fill_patient_id(self, chart_no):
        """환자 ID 입력 (chart_no 사용)"""
        try:
            self.logger.info(f"🆔 환자 ID 입력: {chart_no}")
            id_patterns = [
                (By.ID, "id_patient_id"),
                (By.CSS_SELECTOR, "input#id_patient_id.textinput.form-control"),
                (By.CSS_SELECTOR, "#id_patient_id"),
                (By.CSS_SELECTOR, "input.textinput.form-control"),
                (By.NAME, "patient_id"),
                (By.XPATH, "//input[contains(@placeholder, 'ID') or contains(@aria-label, 'ID') or contains(@aria-label, '환자') or contains(@aria-label, 'Patient') or contains(@aria-label, 'patient') or contains(@placeholder, '환자') or contains(@placeholder, 'Patient') or contains(@placeholder, 'patient') or contains(@name, 'patient_id') or contains(@id, 'patient_id') or contains(@id, 'id_patient_id') or contains(@name, 'id_patient_id') or contains(@id, 'id_patient_id') or contains(@name, 'id_patient_id')]")
            ]
            for by, selector in id_patterns:
                try:
                    id_field = self.wait.until(
                        EC.presence_of_element_located((by, selector))
                    )
                    id_field.clear()
                    time.sleep(0.2)  # 0.5초 → 0.2초로 단축
                    id_field.send_keys(str(chart_no))
                    self.logger.info(f"✅ 환자 ID 입력 완료: {chart_no}")
                    return
                except:
                    continue
            self.logger.warning("⚠️ 환자 ID 필드를 찾을 수 없습니다")
        except Exception as e:
            self.logger.error(f"환자 ID 입력 실패: {str(e)}")
    
    def _fill_patient_name(self, full_name):
        """이름/성 입력 (한국어 순서 처리)"""
        try:
            self.logger.info(f"👤 환자 이름 입력: {full_name}")
            
            # 한국어 이름 분리 (첫 글자는 성, 나머지는 이름)
            if len(full_name) >= 2:
                last_name = full_name[0]  # 성 (첫 글자)
                first_name = full_name[1:]  # 이름 (나머지)
            else:
                last_name = full_name
                first_name = ""
            
            self.logger.info(f"성: {last_name}, 이름: {first_name}")
            
            # 이름 필드 찾기 및 입력 (WebCeph 실제 구조)
            first_name_patterns = [
                # WebCeph 실제 선택자 (개발자 도구에서 확인)
                (By.ID, "id_first_name"),
                (By.CSS_SELECTOR, "input#id_first_name.textinput.form-control"),
                (By.CSS_SELECTOR, "#id_first_name"),
                # 백업 패턴들
                (By.XPATH, "//label[contains(text(), '이름')]/following-sibling::input"),
                (By.XPATH, "//label[contains(text(), '이름')]/parent::*/input"),
                (By.XPATH, "//input[@placeholder='이름']"),
                (By.NAME, "first_name"),
                (By.CSS_SELECTOR, "input[name='first_name']")
            ]
            
            for by, selector in first_name_patterns:
                try:
                    first_name_field = self.driver.find_element(by, selector)
                    first_name_field.clear()
                    first_name_field.send_keys(first_name)
                    self.logger.info(f"✅ 이름 입력 완료: {first_name}")
                    break
                except:
                    continue
            
            # 성 필드 찾기 및 입력 (WebCeph 실제 구조)
            last_name_patterns = [
                # WebCeph 실제 선택자 (개발자 도구에서 확인)
                (By.ID, "id_last_name"),
                (By.CSS_SELECTOR, "input#id_last_name.textinput.form-control"),
                (By.CSS_SELECTOR, "#id_last_name"),
                # 백업 패턴들
                (By.XPATH, "//label[contains(text(), '성')]/following-sibling::input"),
                (By.XPATH, "//label[contains(text(), '성')]/parent::*/input"),
                (By.XPATH, "//input[@placeholder='성']"),
                (By.NAME, "last_name"),
                (By.CSS_SELECTOR, "input[name='last_name']")
            ]
            
            for by, selector in last_name_patterns:
                try:
                    last_name_field = self.driver.find_element(by, selector)
                    last_name_field.clear()
                    last_name_field.send_keys(last_name)
                    self.logger.info(f"✅ 성 입력 완료: {last_name}")
                    break
                except:
                    continue
            
        except Exception as e:
            self.logger.error(f"이름 입력 실패: {str(e)}")
    
    def _select_race_asian(self):
        """인종 선택 (아시안)"""
        try:
            self.logger.info("🌏 인종 선택: 아시안")
            
            # 인종 드롭다운 찾기 (WebCeph 실제 구조)
            race_patterns = [
                # WebCeph 실제 선택자 (개발자 도구에서 확인)
                (By.ID, "id_race"),
                (By.CSS_SELECTOR, "select#id_race.select.form-control"),
                (By.CSS_SELECTOR, "#id_race"),
                # 백업 패턴들
                (By.XPATH, "//label[contains(text(), '인종')]/following-sibling::select"),
                (By.XPATH, "//label[contains(text(), '인종')]/parent::*/select"),
                (By.NAME, "race"),
                (By.XPATH, "//select[contains(@name, 'race')]"),
                (By.CSS_SELECTOR, "select[name='race']")
            ]
            
            for by, selector in race_patterns:
                try:
                    race_dropdown = self.driver.find_element(by, selector)
                    
                    # 드롭다운 클릭하여 열기
                    race_dropdown.click()
                    time.sleep(0.3)  # 1초 → 0.3초로 단축
                    
                    # 아시안 옵션 찾기
                    asian_patterns = [
                        (By.XPATH, "//option[contains(text(), 'Asian')]"),
                        (By.XPATH, "//option[contains(text(), 'asian')]"),
                        (By.XPATH, "//option[contains(text(), '아시안')]"),
                        (By.XPATH, "//option[contains(text(), '아시아')]"),
                        (By.XPATH, "//option[@value='asian']"),
                        (By.XPATH, "//option[@value='Asian']")
                    ]
                    
                    for opt_by, opt_selector in asian_patterns:
                        try:
                            asian_option = self.driver.find_element(opt_by, opt_selector)
                            asian_option.click()
                            self.logger.info("✅ 아시안 선택 완료")
                            return
                        except:
                            continue
                    
                    break
                except:
                    continue
            
            self.logger.warning("⚠️ 인종 선택 필드를 찾을 수 없습니다")
            
        except Exception as e:
            self.logger.error(f"인종 선택 실패: {str(e)}")
    
    def _select_gender(self, gender):
        """성별 선택"""
        try:
            # 성별 코드 정리 (M=남자, F=여자)
            if gender.upper() in ['M', 'MALE', '남', '남자']:
                gender_text = '남자'
                gender_value = 'M'
            elif gender.upper() in ['F', 'FEMALE', '여', '여자']:
                gender_text = '여자'
                gender_value = 'F'
            else:
                self.logger.warning(f"⚠️ 알 수 없는 성별: {gender}")
                return
            
            self.logger.info(f"⚥ 성별 선택: {gender_text}")
            
            # 성별 드롭다운 찾기 (WebCeph 실제 구조)
            gender_patterns = [
                # WebCeph 실제 선택자 (개발자 도구에서 확인)
                (By.ID, "id_sex"),
                (By.CSS_SELECTOR, "select#id_sex.select.form-control"),
                (By.CSS_SELECTOR, "#id_sex"),
                # 백업 패턴들
                (By.XPATH, "//label[contains(text(), '성별')]/following-sibling::select"),
                (By.XPATH, "//label[contains(text(), '성별')]/parent::*/select"),
                (By.NAME, "sex"),
                (By.NAME, "gender"),
                (By.XPATH, "//select[contains(@name, 'sex')]"),
                (By.CSS_SELECTOR, "select[name='sex']")
            ]
            
            for by, selector in gender_patterns:
                try:
                    gender_dropdown = self.driver.find_element(by, selector)
                    
                    # 드롭다운 클릭하여 열기
                    gender_dropdown.click()
                    time.sleep(0.3)  # 1초 → 0.3초로 단축
                    
                    # 성별 옵션 찾기
                    gender_option_patterns = [
                        (By.XPATH, f"//option[contains(text(), '{gender_text}')]"),
                        (By.XPATH, f"//option[@value='{gender_value}']"),
                        (By.XPATH, f"//option[@value='{gender.upper()}']"),
                        (By.XPATH, f"//option[@value='{gender.lower()}']")
                    ]
                    
                    for opt_by, opt_selector in gender_option_patterns:
                        try:
                            gender_option = self.driver.find_element(opt_by, opt_selector)
                            gender_option.click()
                            self.logger.info(f"✅ 성별 선택 완료: {gender_text}")
                            return
                        except:
                            continue
                    
                    break
                except:
                    continue
            
            self.logger.warning("⚠️ 성별 선택 필드를 찾을 수 없습니다")
            
        except Exception as e:
            self.logger.error(f"성별 선택 실패: {str(e)}")
    
    def _fill_birth_date(self, birth_date):
        """생년월일 입력 (yyyy-mm-dd 형태)"""
        try:
            self.logger.info(f"📅 생년월일 입력: {birth_date}")
            
            # 생년월일 필드 찾기 (WebCeph 실제 구조)
            birth_patterns = [
                # WebCeph 실제 선택자 (개발자 도구에서 확인)
                (By.ID, "id_birth_date"),
                (By.CSS_SELECTOR, "input#id_birth_date.dateinput.form-control"),
                (By.CSS_SELECTOR, "#id_birth_date"),
                # 백업 패턴들
                (By.XPATH, "//label[contains(text(), 'Date of birth')]/following-sibling::input"),
                (By.XPATH, "//label[contains(text(), '생년월일')]/following-sibling::input"),
                (By.XPATH, "//input[@placeholder='yyyy-mm-dd']"),
                (By.XPATH, "//input[@placeholder='YYYY-MM-DD']"),
                (By.NAME, "birth_date"),
                (By.NAME, "date_of_birth"),
                (By.XPATH, "//input[@type='date']"),
                (By.CSS_SELECTOR, "input[name='birth_date']")
            ]
            
            for by, selector in birth_patterns:
                try:
                    birth_field = self.driver.find_element(by, selector)
                    birth_field.clear()
                    birth_field.send_keys(birth_date)
                    self.logger.info(f"✅ 생년월일 입력 완료: {birth_date}")
                    return
                except:
                    continue
            
            self.logger.warning("⚠️ 생년월일 필드를 찾을 수 없습니다")
            
        except Exception as e:
            self.logger.error(f"생년월일 입력 실패: {str(e)}")
    
    def _check_agreement(self):
        """동의 체크박스 체크"""
        try:
            self.logger.info("☑️ 동의 체크박스를 체크합니다...")
            checkbox_patterns = [
                (By.ID, "check_agreement_from_patient"),
                (By.NAME, "agreement_from_patient"),
                (By.CSS_SELECTOR, "input#check_agreement_from_patient"),
                (By.CSS_SELECTOR, "input[name='agreement_from_patient']"),
                (By.CSS_SELECTOR, "label[for='check_agreement_from_patient']"),
                (By.CSS_SELECTOR, "label.custom-control-label"),
                (By.CSS_SELECTOR, "input[type='checkbox']"),
                (By.XPATH, "//input[@type='checkbox']"),
                (By.XPATH, "//label[contains(@class, 'custom-control-label')]")
            ]
            for by, selector in checkbox_patterns:
                try:
                    element = self.driver.find_element(by, selector)
                    if element.tag_name == 'input' and element.get_attribute('type') == 'checkbox':
                        if not element.is_selected():
                            element.click()
                            self.logger.info("✅ 동의 체크박스 체크 완료 (input)")
                        else:
                            self.logger.info("✅ 동의 체크박스가 이미 체크되어 있습니다 (input)")
                        return
                    elif element.tag_name == 'label':
                        element.click()
                        self.logger.info("✅ 동의 체크박스 체크 완료 (label)")
                        return
                except Exception as e:
                    continue
            self.logger.warning("⚠️ 동의 체크박스를 찾을 수 없습니다")
        except Exception as e:
            self.logger.error(f"동의 체크박스 체크 실패: {str(e)}")
    
    def _click_create_button(self):
        """만들기 버튼 클릭"""
        try:
            self.logger.info("🔨 만들기 버튼을 클릭합니다...")
            
            # 만들기 버튼 찾기 (WebCeph 실제 구조)
            create_patterns = [
                # WebCeph 실제 선택자 (개발자 도구에서 확인)
                (By.ID, "new_patient_submit"),
                (By.CSS_SELECTOR, "button#new_patient_submit.btn.btn-webceph-3"),
                (By.CSS_SELECTOR, "#new_patient_submit"),
                (By.CSS_SELECTOR, "button.btn-webceph-3"),
                # 백업 패턴들
                (By.XPATH, "//button[contains(text(), '만들기')]"),
                (By.XPATH, "//button[text()='만들기']"),
                (By.XPATH, "//input[@value='만들기']"),
                (By.XPATH, "//button[contains(text(), 'Create')]"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, ".btn-primary"),
                (By.CSS_SELECTOR, "button.btn")
            ]
            
            for by, selector in create_patterns:
                try:
                    create_button = self.driver.find_element(by, selector)
                    if create_button.is_enabled() and create_button.is_displayed():
                        create_button.click()
                        self.logger.info("✅ 만들기 버튼 클릭 완료")
                        time.sleep(1)  # 3초 → 1초로 단축  # 환자 생성 처리 대기
                        return True
                except:
                    continue
            
            self.logger.warning("⚠️ 만들기 버튼을 찾을 수 없습니다")
            return False
            
        except Exception as e:
            self.logger.error(f"만들기 버튼 클릭 실패: {str(e)}")
            return False

    def detect_and_select_new_patient(self, patient_data):
        """신규 생성된 환자 ID를 감지하고 선택"""
        try:
            self.logger.info("🔍 신규 생성된 환자 ID를 감지합니다...")
            
            # 환자 목록 페이지로 이동 (메인 대시보드나 환자 목록)
            dashboard_url = f"{self.config.get('webceph', 'url')}/dashboard"
            self.driver.get(dashboard_url)
            time.sleep(1)  # 3초 → 1초로 단축
            
            # 페이지 새로고침으로 최신 목록 로드
            self.driver.refresh()
            time.sleep(1)  # 3초 → 1초로 단축
            
            # 새로 생성된 환자 정보로 검색할 키워드들
            search_keywords = []
            if patient_data.get('chart_no'):
                search_keywords.append(str(patient_data['chart_no']))
            if patient_data.get('name'):
                search_keywords.append(patient_data['name'])
            if patient_data.get('first_name'):
                search_keywords.append(patient_data['first_name'])
            if patient_data.get('last_name'):
                search_keywords.append(patient_data['last_name'])
            
            # 방법 1: 환자 목록에서 첫 번째 항목 선택 (최신순 정렬 가정)
            first_patient_selected = self._select_first_patient_in_list()
            if first_patient_selected:
                self.logger.info("✅ 첫 번째 환자 항목을 선택했습니다 (최신 생성)")
                return True
            
            # 방법 2: 특정 환자 정보로 검색해서 선택
            for keyword in search_keywords:
                if self._search_and_select_patient(keyword):
                    self.logger.info(f"✅ 환자를 검색해서 선택했습니다: {keyword}")
                    return True
            
            # 방법 3: 환자 목록에서 패턴 매칭으로 선택
            if self._select_patient_by_matching(patient_data):
                self.logger.info("✅ 패턴 매칭으로 환자를 선택했습니다")
                return True
            
            self.logger.warning("⚠️ 신규 생성된 환자를 찾지 못했습니다")
            return False
            
        except Exception as e:
            self.logger.error(f"신규 환자 감지 실패: {str(e)}")
            return False

    def _select_first_patient_in_list(self):
        """환자 목록에서 첫 번째 항목 선택 (최신순 가정)"""
        try:
            self.logger.info("📋 환자 목록에서 첫 번째 항목을 찾습니다...")
            
            # 환자 목록 컨테이너 패턴들
            list_patterns = [
                # 테이블 형태의 환자 목록
                (By.CSS_SELECTOR, "table tbody tr:first-child"),
                (By.CSS_SELECTOR, ".patient-list .patient-item:first-child"),
                (By.CSS_SELECTOR, ".patients-table tbody tr:first-child"),
                (By.CSS_SELECTOR, ".table tbody tr:first-child"),
                # 카드 형태의 환자 목록
                (By.CSS_SELECTOR, ".patient-card:first-child"),
                (By.CSS_SELECTOR, ".card:first-child"),
                # 일반적인 목록 형태
                (By.CSS_SELECTOR, ".list-group .list-group-item:first-child"),
                (By.CSS_SELECTOR, "ul li:first-child"),
                (By.CSS_SELECTOR, ".patient-row:first-child"),
                # XPath 패턴들
                (By.XPATH, "(//tr[contains(@class, 'patient') or contains(@onclick, 'patient')])[1]"),
                (By.XPATH, "(//div[contains(@class, 'patient') and contains(@class, 'item')])[1]"),
                (By.XPATH, "(//a[contains(@href, 'patient')])[1]"),
            ]
            
            for by, selector in list_patterns:
                try:
                    first_patient = self.wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    first_patient.click()
                    self.logger.info(f"✅ 첫 번째 환자 선택 성공: {selector}")
                    time.sleep(0.5)  # 2초 → 0.5초로 단축
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"첫 번째 환자 선택 실패: {str(e)}")
            return False

    def _search_and_select_patient(self, keyword):
        """검색 기능을 사용해서 환자 찾기"""
        try:
            self.logger.info(f"🔍 키워드로 환자 검색: {keyword}")
            
            # 검색 입력 필드 패턴들
            search_patterns = [
                (By.ID, "search"),
                (By.ID, "patient-search"),
                (By.CSS_SELECTOR, "input[type='search']"),
                (By.CSS_SELECTOR, "input[placeholder*='검색']"),
                (By.CSS_SELECTOR, "input[placeholder*='Search']"),
                (By.CSS_SELECTOR, "input[placeholder*='환자']"),
                (By.CSS_SELECTOR, "input[placeholder*='Patient']"),
                (By.CSS_SELECTOR, ".search-input"),
                (By.CSS_SELECTOR, ".form-control[placeholder*='검색']"),
                (By.XPATH, "//input[contains(@placeholder, '검색') or contains(@placeholder, 'Search')]"),
            ]
            
            for by, selector in search_patterns:
                try:
                    search_input = self.driver.find_element(by, selector)
                    search_input.clear()
                    search_input.send_keys(keyword)
                    
                    # Enter 키 또는 검색 버튼 클릭
                    try:
                        from selenium.webdriver.common.keys import Keys
                        search_input.send_keys(Keys.ENTER)
                    except:
                        # 검색 버튼 찾기
                        search_button = self.driver.find_element(
                            By.XPATH, "//button[contains(text(), '검색') or contains(text(), 'Search')] | //button[@type='submit']"
                        )
                        search_button.click()
                    
                    time.sleep(0.5)  # 2초 → 0.5초로 단축
                    
                    # 검색 결과에서 첫 번째 항목 클릭
                    return self._select_first_patient_in_list()
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"환자 검색 실패: {str(e)}")
            return False

    def _select_patient_by_matching(self, patient_data):
        """환자 목록에서 데이터 매칭으로 환자 선택"""
        try:
            self.logger.info("🎯 환자 정보 매칭으로 선택을 시도합니다...")
            
            # 환자 목록의 모든 행 또는 아이템 가져오기
            patient_elements_patterns = [
                (By.CSS_SELECTOR, "table tbody tr"),
                (By.CSS_SELECTOR, ".patient-list .patient-item"),
                (By.CSS_SELECTOR, ".patients-table tbody tr"),
                (By.CSS_SELECTOR, ".patient-card"),
                (By.CSS_SELECTOR, ".list-group .list-group-item"),
                (By.XPATH, "//tr[contains(@class, 'patient') or contains(@onclick, 'patient')]"),
                (By.XPATH, "//div[contains(@class, 'patient') and contains(@class, 'item')]"),
            ]
            
            for by, selector in patient_elements_patterns:
                try:
                    patient_elements = self.driver.find_elements(by, selector)
                    if not patient_elements:
                        continue
                    
                    # 각 환자 요소에서 텍스트 확인
                    for element in patient_elements[:5]:  # 최대 5개만 확인
                        element_text = element.text.strip()
                        
                        # 환자 정보 매칭
                        matches = 0
                        total_checks = 0
                        
                        if patient_data.get('chart_no'):
                            total_checks += 1
                            if str(patient_data['chart_no']) in element_text:
                                matches += 1
                        
                        if patient_data.get('name'):
                            total_checks += 1
                            if patient_data['name'] in element_text:
                                matches += 1
                        
                        if patient_data.get('first_name'):
                            total_checks += 1
                            if patient_data['first_name'] in element_text:
                                matches += 1
                        
                        if patient_data.get('last_name'):
                            total_checks += 1
                            if patient_data['last_name'] in element_text:
                                matches += 1
                        
                        # 50% 이상 매칭되면 선택
                        if total_checks > 0 and matches / total_checks >= 0.5:
                            element.click()
                            self.logger.info(f"✅ 매칭된 환자 선택: {element_text[:50]}...")
                            time.sleep(0.5)  # 2초 → 0.5초로 단축
                            return True
                    
                    # 매칭이 안되면 첫 번째 항목 선택 (최신순 가정)
                    if patient_elements:
                        patient_elements[0].click()
                        self.logger.info("✅ 첫 번째 환자 선택 (매칭 실패시 대안)")
                        time.sleep(0.5)  # 2초 → 0.5초로 단축
                        return True
                        
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"환자 매칭 선택 실패: {str(e)}")
            return False
    
    def _check_login_success(self):
        """로그인 성공 여부 확인"""
        try:
            # 로그인 성공 후 나타나는 요소들 확인
            success_indicators = [
                (By.CLASS_NAME, "dashboard"),
                (By.CLASS_NAME, "main-content"),
                (By.CLASS_NAME, "user-menu"),
                (By.XPATH, "//a[contains(text(), 'Logout')]"),
                (By.XPATH, "//a[contains(text(), '로그아웃')]"),
                (By.XPATH, "//button[contains(text(), 'Logout')]"),
                (By.XPATH, "//div[contains(@class, 'user')]"),
                (By.XPATH, "//div[contains(@class, 'profile')]")
            ]
            
            for by_type, selector in success_indicators:
                try:
                    element = self.driver.find_element(by_type, selector)
                    if element.is_displayed():
                        self.logger.info(f"로그인 성공 확인: {selector}")
                        return True
                except:
                    continue
            
            # URL 확인
            current_url = self.driver.current_url.lower()
            login_keywords = ['login', 'signin', 'auth', '로그인']
            if not any(keyword in current_url for keyword in login_keywords):
                self.logger.info("URL 변경으로 로그인 성공 확인")
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"로그인 성공 확인 중 오류: {str(e)}")
            return False
    
    def register_patient(self, patient_data):
        """환자 등록"""
        try:
            self.logger.info(f"환자 '{patient_data['name']}'을(를) 등록합니다...")
            
            # 새 환자 등록 페이지로 이동
            # 실제 Web Ceph의 환자 등록 URL을 사용해야 함
            new_patient_url = f"{self.config.get('webceph', 'url')}/patients/new"
            self.driver.get(new_patient_url)
            time.sleep(self.wait_time)
            
            # 환자 정보 입력
            self._fill_patient_form(patient_data)
            
            # 등록 버튼 클릭
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '등록') or contains(text(), 'Save') or contains(text(), 'Submit')]"))
            )
            submit_button.click()
            
            # 등록 완료 확인
            time.sleep(1)  # 3초 → 1초로 단축
            
            # 성공 메시지나 환자 상세 페이지로 리다이렉트 확인
            try:
                success_indicator = self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "success")),
                        EC.presence_of_element_located((By.CLASS_NAME, "patient-detail")),
                        EC.url_contains("/patients/")
                    )
                )
                self.logger.info(f"환자 '{patient_data['name']}'이(가) 성공적으로 등록되었습니다")
                return True
                
            except TimeoutException:
                # 오류 메시지 확인
                error_elements = self.driver.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_text = error_elements[0].text
                    raise Exception(f"환자 등록 실패: {error_text}")
                else:
                    raise Exception("환자 등록 상태를 확인할 수 없습니다")
            
        except Exception as e:
            self.logger.error(f"환자 등록 실패: {str(e)}")
            raise
    
    def _fill_patient_form(self, patient_data):
        """환자 정보 폼 입력"""
        # 이름
        name_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        name_field.clear()
        name_field.send_keys(patient_data['name'])
        
        # 생년월일
        try:
            birth_date_field = self.driver.find_element(By.NAME, "birth_date")
            birth_date_str = patient_data['birth_date'].strftime('%Y-%m-%d')
            birth_date_field.clear()
            birth_date_field.send_keys(birth_date_str)
        except NoSuchElementException:
            # 년/월/일 개별 필드인 경우
            birth_date = patient_data['birth_date']
            year_field = self.driver.find_element(By.NAME, "birth_year")
            month_field = self.driver.find_element(By.NAME, "birth_month")
            day_field = self.driver.find_element(By.NAME, "birth_day")
            
            year_field.clear()
            year_field.send_keys(str(birth_date.year))
            month_field.clear()
            month_field.send_keys(str(birth_date.month))
            day_field.clear()
            day_field.send_keys(str(birth_date.day))
        
        # 등록번호
        reg_num_field = self.driver.find_element(By.NAME, "registration_number")
        reg_num_field.clear()
        reg_num_field.send_keys(patient_data['registration_number'])
        
        # 성별
        try:
            gender_select = self.driver.find_element(By.NAME, "gender")
            gender_value = "male" if patient_data['gender'] == 'M' else "female"
            
            from selenium.webdriver.support.ui import Select
            select = Select(gender_select)
            select.select_by_value(gender_value)
        except NoSuchElementException:
            # 라디오 버튼인 경우
            gender_value = patient_data['gender']
            gender_radio = self.driver.find_element(By.XPATH, f"//input[@type='radio' and @value='{gender_value}']")
            gender_radio.click()
        
        # 연락처 (선택사항)
        if patient_data.get('phone'):
            try:
                phone_field = self.driver.find_element(By.NAME, "phone")
                phone_field.clear()
                phone_field.send_keys(patient_data['phone'])
            except NoSuchElementException:
                pass
        
        # 이메일 (선택사항)
        if patient_data.get('email'):
            try:
                email_field = self.driver.find_element(By.NAME, "email")
                email_field.clear()
                email_field.send_keys(patient_data['email'])
            except NoSuchElementException:
                pass
        
        # 특이사항 (선택사항)
        if patient_data.get('notes'):
            try:
                notes_field = self.driver.find_element(By.NAME, "notes")
                notes_field.clear()
                notes_field.send_keys(patient_data['notes'])
            except NoSuchElementException:
                pass
    
    def upload_images(self, images):
        """이미지 업로드"""
        try:
            self.logger.info("이미지 업로드를 시작합니다...")
            
            # X-ray 이미지 업로드
            if images.get('xray'):
                self._upload_single_image(images['xray'], 'xray')
            
            # 얼굴 사진 업로드
            if images.get('face'):
                self._upload_single_image(images['face'], 'face')
            
            self.logger.info("모든 이미지가 성공적으로 업로드되었습니다")
            return True
            
        except Exception as e:
            self.logger.error(f"이미지 업로드 실패: {str(e)}")
            raise
    
    def _upload_single_image(self, image_path, image_type):
        """단일 이미지 업로드"""
        try:
            # 이미지 타입에 따른 업로드 버튼 찾기
            if image_type == 'xray':
                upload_selector = "//input[@type='file' and contains(@name, 'xray')]"
            else:
                upload_selector = "//input[@type='file' and contains(@name, 'photo')]"
            
            # 파일 입력 요소 찾기
            file_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, upload_selector))
            )
            
            # 파일 경로 입력
            file_input.send_keys(str(Path(image_path).resolve()))
            
            # 업로드 완료 대기
            time.sleep(0.5)  # 2초 → 0.5초로 단축
            
            # 업로드 성공 확인 (썸네일이나 성공 표시 확인)
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "upload-success")),
                    EC.presence_of_element_located((By.CLASS_NAME, "thumbnail")),
                    EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'thumb')]"))
                )
            )
            
            self.logger.info(f"{image_type} 이미지가 성공적으로 업로드되었습니다")
            
        except Exception as e:
            self.logger.error(f"{image_type} 이미지 업로드 실패: {str(e)}")
            raise
    
    def start_analysis(self):
        """분석 시작"""
        try:
            self.logger.info("분석을 시작합니다...")
            
            # 분석 시작 버튼 찾기 및 클릭
            analyze_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '분석') or contains(text(), 'Analyze') or contains(text(), 'Start')]"))
            )
            analyze_button.click()
            
            # 분석 시작 확인
            time.sleep(1)  # 3초 → 1초로 단축
            
            # 분석 진행 상태 확인
            try:
                progress_indicator = self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "analysis-progress")),
                        EC.presence_of_element_located((By.CLASS_NAME, "processing")),
                        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '분석') and contains(text(), '진행')]"))
                    )
                )
                self.logger.info("분석이 성공적으로 시작되었습니다")
                return True
                
            except TimeoutException:
                raise Exception("분석 시작 상태를 확인할 수 없습니다")
            
        except Exception as e:
            self.logger.error(f"분석 시작 실패: {str(e)}")
            raise
    
    def wait_for_analysis_completion(self, max_wait_minutes=10):
        """분석 완료 대기"""
        try:
            self.logger.info("분석 완료를 대기합니다...")
            
            max_wait_seconds = max_wait_minutes * 60
            check_interval = 15  # 15초마다 확인 (30초 → 15초로 단축)
            
            for elapsed in range(0, max_wait_seconds, check_interval):
                # 분석 완료 확인
                try:
                    # 완료 표시나 PDF 다운로드 버튼 확인
                    completion_indicator = self.driver.find_elements(
                        By.XPATH, 
                        "//button[contains(text(), 'Download') or contains(text(), '다운로드')] | //div[contains(text(), '완료') or contains(text(), 'Complete')]"
                    )
                    
                    if completion_indicator:
                        self.logger.info("분석이 완료되었습니다")
                        return True
                    
                    # 진행 중 표시 확인
                    progress_elements = self.driver.find_elements(
                        By.XPATH,
                        "//div[contains(text(), '진행') or contains(text(), 'Progress') or contains(text(), 'Processing')]"
                    )
                    
                    if progress_elements:
                        self.logger.info(f"분석 진행 중... ({elapsed//60}분 경과)")
                    else:
                        # 진행 표시가 없으면 완료되었을 가능성
                        time.sleep(2)  # 5초 → 2초로 단축
                        completion_indicator = self.driver.find_elements(
                            By.XPATH, 
                            "//button[contains(text(), 'Download') or contains(text(), '다운로드')]"
                        )
                        if completion_indicator:
                            self.logger.info("분석이 완료되었습니다")
                            return True
                    
                except Exception as e:
                    self.logger.warning(f"분석 상태 확인 중 오류: {str(e)}")
                
                time.sleep(check_interval)
            
            raise Exception(f"분석이 {max_wait_minutes}분 내에 완료되지 않았습니다")
            
        except Exception as e:
            self.logger.error(f"분석 대기 실패: {str(e)}")
            raise
    
    def download_pdf(self, patient_data):
        """PDF 다운로드"""
        try:
            self.logger.info("분석 결과 PDF를 다운로드합니다...")
            
            # PDF 다운로드 버튼 찾기 및 클릭
            download_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download') or contains(text(), '다운로드')] | //a[contains(text(), 'PDF')]"))
            )
            download_button.click()
            
            # 다운로드 완료 대기
            time.sleep(2)  # 5초 → 2초로 단축
            
            # 다운로드된 파일 확인 및 이름 변경
            pdf_folder = Path(self.config.get('paths', 'pdf_folder'))
            if not pdf_folder.exists():
                pdf_folder.mkdir(parents=True, exist_ok=True)
            
            # 가장 최근 다운로드된 PDF 파일 찾기
            pdf_files = list(pdf_folder.glob("*.pdf"))
            if pdf_files:
                latest_pdf = max(pdf_files, key=os.path.getctime)
                
                # 새 파일명 생성
                patient_name = patient_data['name']
                reg_num = patient_data['registration_number']
                date_str = datetime.now().strftime("%Y%m%d")
                new_filename = f"{patient_name}_{reg_num}_{date_str}.pdf"
                new_path = pdf_folder / new_filename
                
                # 파일 이름 변경
                latest_pdf.rename(new_path)
                
                self.logger.info(f"PDF가 성공적으로 다운로드되었습니다: {new_filename}")
                return str(new_path)
            else:
                raise Exception("다운로드된 PDF 파일을 찾을 수 없습니다")
            
        except Exception as e:
            self.logger.error(f"PDF 다운로드 실패: {str(e)}")
            raise
    
    def close_browser(self):
        """브라우저 종료"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("브라우저가 정상적으로 종료되었습니다")
        except Exception as e:
            self.logger.error(f"브라우저 종료 중 오류: {str(e)}")
    
    def process_patient(self, patient_data, images):
        """환자 전체 프로세스 실행"""
        try:
            self.logger.info(f"환자 '{patient_data['name']}' 처리를 시작합니다")
            
            # 1. 브라우저 초기화
            self.initialize_browser()
            
            # 2. 로그인
            username, password = self.config.get_credentials()
            if not username or not password:
                raise Exception("로그인 정보가 설정되지 않았습니다")
            
            self.login(username, password)
            
            # 3. 환자 등록
            self.register_patient(patient_data)
            
            # 4. 신규 생성된 환자 ID 감지 및 선택 + 레코드 생성
            self.logger.info("🔍 신규 생성된 환자를 감지하여 선택하고 레코드를 생성합니다...")
            if not self.create_complete_patient_record(patient_data, images):
                self.logger.warning("⚠️ 신규 환자 선택 및 레코드 생성 실패 - 수동으로 진행해주세요")
                # 실패해도 계속 진행 (사용자가 수동으로 선택할 수 있음)
            
            # 5. 이미지 업로드
            self.upload_images(images)
            
            # 6. 분석 시작
            self.start_analysis()
            
            # 7. 분석 완료 대기
            self.wait_for_analysis_completion()
            
            # 8. PDF 다운로드
            pdf_path = self.download_pdf(patient_data)
            
            self.logger.info(f"환자 '{patient_data['name']}' 처리가 완료되었습니다")
            
            return {
                'success': True,
                'pdf_path': pdf_path,
                'message': '모든 작업이 성공적으로 완료되었습니다'
            }
            
        except Exception as e:
            self.logger.error(f"환자 처리 실패: {str(e)}")
            return {
                'success': False,
                'pdf_path': None,
                'message': str(e)
            }
        finally:
            self.close_browser()
    
    def process_new_patient(self, patient_data, images):
        """신규 환자 생성 및 전체 프로세스 실행 (신규 ID 자동 감지 포함)"""
        try:
            self.logger.info(f"신규 환자 '{patient_data['name']}' 생성 및 처리를 시작합니다")
            
            # 1. 브라우저 초기화
            self.initialize_browser()
            
            # 2. 로그인
            username, password = self.config.get_credentials()
            if not username or not password:
                raise Exception("로그인 정보가 설정되지 않았습니다")
            
            self.login(username, password)
            
            # 3. 신규 환자 등록 (새로운 ID 생성)
            self.logger.info("🆕 신규 환자를 등록합니다...")
            self.click_new_patient_button()
            self.fill_patient_form(patient_data)
            
            # 4. 생성된 신규 환자 자동 감지, 선택 및 레코드 생성
            self.logger.info("🔍 방금 생성된 신규 환자를 자동으로 찾아 선택하고 레코드를 생성합니다...")
            if self.detect_and_select_new_patient(patient_data):
                self.logger.info("✅ 신규 생성 환자 자동 선택 성공!")
                
                # 레코드 생성
                self.logger.info("📋 환자 레코드를 생성합니다...")
                if self.create_patient_record(patient_data):
                    self.setup_record_info(patient_data)
                    self.confirm_record_creation()
                    self.wait_for_record_ready()
                    self.logger.info("✅ 레코드 생성 완료!")
                else:
                    self.logger.warning("⚠️ 레코드 생성 실패")
            else:
                self.logger.warning("⚠️ 신규 환자 자동 선택 실패 - 첫 번째 환자를 선택합니다")
                # 대안: 첫 번째 환자 강제 선택 (최신순 가정)
                if self._select_first_patient_in_list():
                    # 선택 성공하면 레코드 생성 시도
                    self.logger.info("📋 선택된 환자의 레코드를 생성합니다...")
                    if self.create_patient_record(patient_data):
                        self.setup_record_info(patient_data)
                        self.confirm_record_creation()
                        self.wait_for_record_ready()
            
            # 5. 이미지 업로드
            self.upload_images(images)
            
            # 6. 분석 시작
            self.start_analysis()
            
            # 7. 분석 완료 대기
            self.wait_for_analysis_completion()
            
            # 8. PDF 다운로드
            pdf_path = self.download_pdf(patient_data)
            
            self.logger.info(f"신규 환자 '{patient_data['name']}' 처리가 완료되었습니다")
            
            return {
                'success': True,
                'pdf_path': pdf_path,
                'message': '신규 환자 생성 및 분석이 성공적으로 완료되었습니다',
                'patient_created': True
            }
            
        except Exception as e:
            self.logger.error(f"신규 환자 처리 실패: {str(e)}")
            return {
                'success': False,
                'pdf_path': None,
                'message': str(e),
                'patient_created': False
            }
        finally:
            self.close_browser()

    def create_and_select_new_patient(self, patient_data):
        """신규 환자 생성하고 즉시 선택하는 원스톱 함수"""
        try:
            self.logger.info(f"🚀 신규 환자 '{patient_data.get('name', 'Unknown')}' 생성 및 선택을 시작합니다")
            
            # 1. 신규 환자 버튼 클릭
            self.click_new_patient_button()
            
            # 2. 환자 폼 작성
            self.fill_patient_form(patient_data)
            
            # 3. 생성된 환자 자동 감지 및 선택
            if self.detect_and_select_new_patient(patient_data):
                self.logger.info("✅ 신규 환자 생성 및 선택 완료!")
                return True
            else:
                self.logger.warning("⚠️ 신규 환자 생성은 완료되었지만 자동 선택에 실패했습니다")
                return False
                
        except Exception as e:
            self.logger.error(f"신규 환자 생성 및 선택 실패: {str(e)}")
            raise

    def wait_for_new_patient_in_list(self, patient_data, timeout_seconds=10):
        """환자 목록에 새로운 환자가 나타날 때까지 대기"""
        try:
            self.logger.info("⏳ 환자 목록에 새로운 환자가 나타날 때까지 대기합니다...")
            
            import time
            start_time = time.time()
            
            while time.time() - start_time < timeout_seconds:
                # 페이지 새로고침
                self.driver.refresh()
                time.sleep(0.5)  # 2초 → 0.5초로 단축
                
                # 첫 번째 환자 확인
                if self._check_patient_in_list(patient_data):
                    self.logger.info("✅ 새로운 환자가 목록에 나타났습니다!")
                    return True
                
                time.sleep(1)
            
            self.logger.warning(f"⚠️ {timeout_seconds}초 내에 새로운 환자를 찾을 수 없었습니다")
            return False
            
        except Exception as e:
            self.logger.error(f"환자 대기 중 오류: {str(e)}")
            return False

    def _check_patient_in_list(self, patient_data):
        """환자 목록에서 특정 환자가 있는지 확인"""
        try:
            # 환자 목록의 첫 번째 항목 텍스트 확인
            first_patient_patterns = [
                (By.CSS_SELECTOR, "table tbody tr:first-child"),
                (By.CSS_SELECTOR, ".patient-list .patient-item:first-child"),
                (By.CSS_SELECTOR, ".patient-card:first-child"),
                (By.XPATH, "(//tr[contains(@class, 'patient')])[1]"),
            ]
            
            for by, selector in first_patient_patterns:
                try:
                    element = self.driver.find_element(by, selector)
                    element_text = element.text.strip().lower()
                    
                    # 환자 정보 매칭
                    if patient_data.get('name') and patient_data['name'].lower() in element_text:
                        return True
                    if patient_data.get('chart_no') and str(patient_data['chart_no']).lower() in element_text:
                        return True
                    if patient_data.get('first_name') and patient_data['first_name'].lower() in element_text:
                        return True
                        
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"환자 목록 확인 중 오류: {str(e)}")
            return False

    def get_latest_patient_id(self):
        """최근 생성된 환자 ID 가져오기 (환자 목록 최상단)"""
        try:
            self.logger.info("📋 최근 생성된 환자 ID를 가져옵니다...")
            
            # 환자 목록 페이지로 이동
            dashboard_url = f"{self.config.get('webceph', 'url')}/dashboard"
            self.driver.get(dashboard_url)
            time.sleep(1)  # 3초 → 1초로 단축
            
            # 페이지 새로고침으로 최신 목록 로드
            self.driver.refresh()
            time.sleep(0.5)  # 2초 → 0.5초로 단축
            
            # 첫 번째 환자의 정보 추출 시도
            patient_info_patterns = [
                # 테이블 형태에서 첫 번째 행의 ID 셀
                (By.CSS_SELECTOR, "table tbody tr:first-child td:first-child"),
                (By.CSS_SELECTOR, "table tbody tr:first-child .patient-id"),
                # 카드 형태에서 첫 번째 카드의 ID 영역
                (By.CSS_SELECTOR, ".patient-card:first-child .patient-id"),
                (By.CSS_SELECTOR, ".patient-item:first-child .id"),
                # 범용 패턴
                (By.XPATH, "(//tr[contains(@class, 'patient')])[1]//td[1]"),
                (By.XPATH, "(//div[contains(@class, 'patient-id')])[1]"),
            ]
            
            for by, selector in patient_info_patterns:
                try:
                    element = self.driver.find_element(by, selector)
                    patient_id = element.text.strip()
                    if patient_id:
                        self.logger.info(f"✅ 최근 환자 ID 감지: {patient_id}")
                        return patient_id
                except:
                    continue
            
            self.logger.warning("⚠️ 최근 환자 ID를 감지하지 못했습니다")
            return None
            
        except Exception as e:
            self.logger.error(f"최근 환자 ID 가져오기 실패: {str(e)}")
            return None
    
    def __del__(self):
        """소멸자"""
        self.close_browser() 

    def create_patient_record(self, patient_data=None):
        """선택된 환자의 새로운 레코드 생성"""
        try:
            self.logger.info("📋 환자 레코드 생성을 시작합니다...")
            
            # 레코드 생성 버튼 찾기 및 클릭
            record_button_patterns = [
                # WebCeph 실제 선택자
                (By.ID, "new_record_button"),
                (By.CSS_SELECTOR, "button[data-action='new-record']"),
                (By.CSS_SELECTOR, ".btn-new-record"),
                # 텍스트 기반 패턴
                (By.XPATH, "//button[contains(text(), '새 레코드') or contains(text(), 'New Record')]"),
                (By.XPATH, "//button[contains(text(), '레코드 생성') or contains(text(), 'Create Record')]"),
                (By.XPATH, "//button[contains(text(), '+ 레코드') or contains(text(), '+ Record')]"),
                (By.XPATH, "//a[contains(text(), '새 레코드') or contains(text(), 'New Record')]"),
                (By.XPATH, "//a[contains(text(), '레코드 생성') or contains(text(), 'Create Record')]"),
                # 아이콘 기반 패턴
                (By.CSS_SELECTOR, "button[title*='레코드'] i.fa-plus"),
                (By.CSS_SELECTOR, "button[title*='Record'] i.fa-plus"),
                (By.CSS_SELECTOR, ".btn[title*='새로운'] i.fa-plus"),
                # 범용 패턴
                (By.CSS_SELECTOR, ".btn-primary"),
                (By.CSS_SELECTOR, ".btn-success"),
                (By.XPATH, "//button[contains(@class, 'btn') and contains(@class, 'primary')]")
            ]
            
            for by, selector in record_button_patterns:
                try:
                    record_button = self.wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    record_button.click()
                    self.logger.info(f"✅ 레코드 생성 버튼 클릭 성공: {selector}")
                    time.sleep(1)  # 3초 → 1초로 단축  # 레코드 생성 페이지 로딩 대기
                    return True
                except:
                    continue
            
            # 대안: 환자 상세 페이지에서 새 분석 시작 버튼 찾기
            analysis_button_patterns = [
                (By.XPATH, "//button[contains(text(), '새 분석') or contains(text(), 'New Analysis')]"),
                (By.XPATH, "//button[contains(text(), '분석 시작') or contains(text(), 'Start Analysis')]"),
                (By.XPATH, "//a[contains(text(), '새 분석') or contains(text(), 'New Analysis')]"),
                (By.CSS_SELECTOR, "button[data-action='start-analysis']"),
                (By.CSS_SELECTOR, ".btn-start-analysis")
            ]
            
            for by, selector in analysis_button_patterns:
                try:
                    analysis_button = self.wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    analysis_button.click()
                    self.logger.info(f"✅ 분석 시작 버튼 클릭 성공: {selector}")
                    time.sleep(1)  # 3초 → 1초로 단축
                    return True
                except:
                    continue
            
            self.logger.warning("⚠️ 레코드 생성 버튼을 찾을 수 없습니다")
            return False
            
        except Exception as e:
            self.logger.error(f"레코드 생성 실패: {str(e)}")
            return False

    def setup_record_info(self, patient_data=None):
        """레코드 정보 설정 (날짜, 타입 등)"""
        try:
            self.logger.info("📝 레코드 정보를 설정합니다...")
            
            # 레코드 날짜 설정 (오늘 날짜)
            self._set_record_date()
            
            # 레코드 타입 설정 (일반적으로 초진/재진)
            self._set_record_type()
            
            # 레코드 제목/메모 설정
            if patient_data:
                self._set_record_title(patient_data)
            
            self.logger.info("✅ 레코드 정보 설정 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"레코드 정보 설정 실패: {str(e)}")
            return False

    def _set_record_date(self):
        """레코드 날짜 설정"""
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            
            date_field_patterns = [
                (By.ID, "record_date"),
                (By.ID, "analysis_date"),
                (By.CSS_SELECTOR, "input[type='date']"),
                (By.CSS_SELECTOR, "input[name*='date']"),
                (By.CSS_SELECTOR, "input[placeholder*='날짜']"),
                (By.CSS_SELECTOR, "input[placeholder*='Date']"),
                (By.XPATH, "//input[contains(@placeholder, '날짜') or contains(@placeholder, 'Date')]")
            ]
            
            for by, selector in date_field_patterns:
                try:
                    date_field = self.driver.find_element(by, selector)
                    date_field.clear()
                    date_field.send_keys(today)
                    self.logger.info(f"✅ 레코드 날짜 설정: {today}")
                    return
                except:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"레코드 날짜 설정 실패: {str(e)}")

    def _set_record_type(self, record_type="초진"):
        """레코드 타입 설정"""
        try:
            # 드롭다운 선택
            type_dropdown_patterns = [
                (By.ID, "record_type"),
                (By.ID, "visit_type"),
                (By.CSS_SELECTOR, "select[name*='type']"),
                (By.CSS_SELECTOR, "select[name*='visit']")
            ]
            
            for by, selector in type_dropdown_patterns:
                try:
                    dropdown = self.driver.find_element(by, selector)
                    from selenium.webdriver.support.ui import Select
                    select = Select(dropdown)
                    
                    # 초진/재진 옵션 찾기
                    for option in select.options:
                        if record_type in option.text or "초진" in option.text or "Initial" in option.text:
                            select.select_by_visible_text(option.text)
                            self.logger.info(f"✅ 레코드 타입 설정: {option.text}")
                            return
                except:
                    continue
                    
            # 라디오 버튼 선택
            radio_patterns = [
                (By.XPATH, f"//input[@type='radio' and contains(@value, '{record_type}')]"),
                (By.XPATH, "//input[@type='radio' and contains(@value, '초진')]"),
                (By.XPATH, "//input[@type='radio' and contains(@value, 'Initial')]")
            ]
            
            for by, selector in radio_patterns:
                try:
                    radio = self.driver.find_element(by, selector)
                    radio.click()
                    self.logger.info(f"✅ 레코드 타입 라디오 선택: {record_type}")
                    return
                except:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"레코드 타입 설정 실패: {str(e)}")

    def _set_record_title(self, patient_data):
        """레코드 제목/메모 설정"""
        try:
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")
            patient_name = patient_data.get('name', '환자')
            
            record_title = f"{patient_name} - 초진 ({today_str})"
            
            title_field_patterns = [
                (By.ID, "record_title"),
                (By.ID, "record_name"),
                (By.ID, "analysis_title"),
                (By.CSS_SELECTOR, "input[name*='title']"),
                (By.CSS_SELECTOR, "input[name*='name']"),
                (By.CSS_SELECTOR, "input[placeholder*='제목']"),
                (By.CSS_SELECTOR, "input[placeholder*='Title']")
            ]
            
            for by, selector in title_field_patterns:
                try:
                    title_field = self.driver.find_element(by, selector)
                    title_field.clear()
                    title_field.send_keys(record_title)
                    self.logger.info(f"✅ 레코드 제목 설정: {record_title}")
                    return
                except:
                    continue
                    
            # 메모/노트 필드
            memo_field_patterns = [
                (By.ID, "record_memo"),
                (By.ID, "record_notes"),
                (By.CSS_SELECTOR, "textarea[name*='memo']"),
                (By.CSS_SELECTOR, "textarea[name*='notes']"),
                (By.CSS_SELECTOR, "textarea[placeholder*='메모']")
            ]
            
            memo_text = f"환자: {patient_name}\n날짜: {today_str}\n타입: 초진"
            
            for by, selector in memo_field_patterns:
                try:
                    memo_field = self.driver.find_element(by, selector)
                    memo_field.clear()
                    memo_field.send_keys(memo_text)
                    self.logger.info("✅ 레코드 메모 설정 완료")
                    return
                except:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"레코드 제목/메모 설정 실패: {str(e)}")

    def confirm_record_creation(self):
        """레코드 생성 확인"""
        try:
            self.logger.info("✅ 레코드 생성을 확인합니다...")
            
            # 생성/확인 버튼 찾기
            confirm_button_patterns = [
                (By.ID, "create_record_button"),
                (By.ID, "confirm_button"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), '생성') or contains(text(), 'Create')]"),
                (By.XPATH, "//button[contains(text(), '확인') or contains(text(), 'Confirm')]"),
                (By.XPATH, "//button[contains(text(), '저장') or contains(text(), 'Save')]"),
                (By.XPATH, "//input[@type='submit' and contains(@value, '생성')]"),
                (By.XPATH, "//input[@type='submit' and contains(@value, 'Create')]")
            ]
            
            for by, selector in confirm_button_patterns:
                try:
                    confirm_button = self.driver.find_element(by, selector)
                    if confirm_button.is_enabled() and confirm_button.is_displayed():
                        confirm_button.click()
                        self.logger.info("✅ 레코드 생성 확인 버튼 클릭")
                        time.sleep(1)  # 3초 → 1초로 단축  # 생성 처리 대기
                        return True
                except:
                    continue
            
            self.logger.warning("⚠️ 레코드 생성 확인 버튼을 찾을 수 없습니다")
            return False
            
        except Exception as e:
            self.logger.error(f"레코드 생성 확인 실패: {str(e)}")
            return False

    def wait_for_record_ready(self):
        """레코드가 이미지 업로드 준비 상태가 될 때까지 대기"""
        try:
            self.logger.info("⏳ 레코드 준비 상태를 확인합니다...")
            
            # 이미지 업로드 영역이 나타날 때까지 대기
            upload_indicators = [
                (By.ID, "image_upload"),
                (By.ID, "file_upload"),
                (By.CSS_SELECTOR, "input[type='file']"),
                (By.CSS_SELECTOR, ".upload-area"),
                (By.CSS_SELECTOR, ".file-drop-zone"),
                (By.XPATH, "//div[contains(@class, 'upload') or contains(@class, 'drop')]"),
                (By.XPATH, "//button[contains(text(), '이미지 업로드') or contains(text(), 'Upload Image')]")
            ]
            
            max_wait_time = 10  # 10초 대기
            for attempt in range(max_wait_time):
                for by, selector in upload_indicators:
                    try:
                        element = self.driver.find_element(by, selector)
                        if element.is_displayed():
                            self.logger.info("✅ 레코드가 이미지 업로드 준비 상태입니다")
                            return True
                    except:
                        continue
                
                time.sleep(1)
            
            self.logger.warning("⚠️ 레코드 준비 상태 확인 실패")
            return False
            
        except Exception as e:
            self.logger.error(f"레코드 준비 상태 확인 오류: {str(e)}")
            return False

    def create_complete_patient_record(self, patient_data, images=None):
        """신규 환자 선택부터 레코드 생성까지 완전한 프로세스"""
        try:
            self.logger.info("🚀 완전한 환자 레코드 생성 프로세스를 시작합니다...")
            
            # 1. 신규 환자 감지 및 선택
            if not self.detect_and_select_new_patient(patient_data):
                self.logger.warning("⚠️ 신규 환자 선택 실패 - 첫 번째 환자를 선택합니다")
                self._select_first_patient_in_list()
            
            # 2. 레코드 생성
            if not self.create_patient_record(patient_data):
                raise Exception("레코드 생성에 실패했습니다")
            
            # 3. 레코드 정보 설정
            self.setup_record_info(patient_data)
            
            # 4. 레코드 생성 확인
            if not self.confirm_record_creation():
                raise Exception("레코드 생성 확인에 실패했습니다")
            
            # 5. 레코드 준비 상태 대기
            if not self.wait_for_record_ready():
                self.logger.warning("⚠️ 레코드 준비 상태 확인 실패 - 이미지 업로드를 시도합니다")
            
            self.logger.info("✅ 완전한 환자 레코드 생성이 완료되었습니다!")
            return True
            
        except Exception as e:
            self.logger.error(f"완전한 레코드 생성 프로세스 실패: {str(e)}")
            return False 