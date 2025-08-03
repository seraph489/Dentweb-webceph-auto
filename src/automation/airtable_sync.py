"""
Airtable 연동 모듈
ERD 문서의 데이터 구조를 기반으로 환자 정보와 분석 결과를 Airtable에 저장
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import config

class AirtableSync:
    """Airtable 동기화 클래스"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.config = config
        
        # Airtable 설정
        self.api_key = self.config.get_airtable_api_key()
        self.base_id = self.config.get('airtable', 'base_id', '')
        self.table_name = self.config.get('airtable', 'table_name', 'Patients')
        
        # API 기본 설정
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # HTTP 세션 설정 (재시도 로직 포함)
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 로컬 캐시 설정
        self.cache_dir = Path.home() / "AppData" / "Local" / "WebCephAuto" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_queue_file = self.cache_dir / "offline_queue.json"
    
    def _setup_logger(self):
        """로거 설정"""
        logger = logging.getLogger('AirtableSync')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 파일 핸들러
            log_dir = Path.home() / "AppData" / "Local" / "WebCephAuto" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"airtable_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 포맷터
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def test_connection(self) -> Dict[str, Any]:
        """Airtable 연결 테스트"""
        try:
            self.logger.info("Airtable 연결을 테스트합니다...")
            
            if not self.api_key or not self.base_id:
                return {
                    'success': False,
                    'message': 'API 키 또는 Base ID가 설정되지 않았습니다'
                }
            
            # 테이블 정보 조회 (첫 번째 레코드만)
            url = f"{self.base_url}/{self.table_name}"
            params = {'maxRecords': 1}
            
            response = self.session.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Airtable 연결 테스트 성공")
                return {
                    'success': True,
                    'message': 'Airtable 연결이 성공적으로 확인되었습니다'
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': 'API 키가 올바르지 않습니다'
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'message': 'Base ID 또는 테이블명을 확인해주세요'
                }
            else:
                return {
                    'success': False,
                    'message': f'연결 실패: HTTP {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': '연결 시간 초과: 네트워크 상태를 확인해주세요'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': '네트워크 연결 오류: 인터넷 연결을 확인해주세요'
            }
        except Exception as e:
            self.logger.error(f"Airtable 연결 테스트 실패: {str(e)}")
            return {
                'success': False,
                'message': f'연결 테스트 실패: {str(e)}'
            }
    
    def create_patient_record(self, patient_data: Dict[str, Any], 
                            session_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """환자 레코드 생성"""
        try:
            self.logger.info(f"환자 '{patient_data['name']}' 레코드를 생성합니다...")
            
            # ERD 구조에 따른 데이터 매핑
            record_data = self._map_patient_data(patient_data, session_data)
            
            # Airtable API 호출
            url = f"{self.base_url}/{self.table_name}"
            payload = {
                "fields": record_data
            }
            
            response = self.session.post(
                url, 
                headers=self.headers, 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                record_id = result['id']
                
                self.logger.info(f"환자 레코드가 성공적으로 생성되었습니다: {record_id}")
                return {
                    'success': True,
                    'record_id': record_id,
                    'message': '환자 정보가 성공적으로 저장되었습니다'
                }
            else:
                error_msg = f"레코드 생성 실패: HTTP {response.status_code}"
                if response.content:
                    try:
                        error_detail = response.json()
                        error_msg += f" - {error_detail.get('error', {}).get('message', '')}"
                    except:
                        pass
                
                self.logger.error(error_msg)
                
                # 오프라인 큐에 저장
                self._add_to_offline_queue('create_patient', payload)
                
                return {
                    'success': False,
                    'message': error_msg + " (오프라인 큐에 저장됨)"
                }
                
        except Exception as e:
            self.logger.error(f"환자 레코드 생성 실패: {str(e)}")
            
            # 오프라인 큐에 저장
            try:
                record_data = self._map_patient_data(patient_data, session_data)
                payload = {"fields": record_data}
                self._add_to_offline_queue('create_patient', payload)
            except:
                pass
            
            return {
                'success': False,
                'message': f'레코드 생성 실패: {str(e)} (오프라인 큐에 저장됨)'
            }
    
    def update_analysis_result(self, record_id: str, 
                             analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과 업데이트"""
        try:
            self.logger.info(f"분석 결과를 업데이트합니다: {record_id}")
            
            # 분석 결과 데이터 매핑
            update_data = self._map_analysis_result(analysis_result)
            
            # Airtable API 호출
            url = f"{self.base_url}/{self.table_name}/{record_id}"
            payload = {
                "fields": update_data
            }
            
            response = self.session.patch(
                url, 
                headers=self.headers, 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info("분석 결과가 성공적으로 업데이트되었습니다")
                return {
                    'success': True,
                    'message': '분석 결과가 성공적으로 업데이트되었습니다'
                }
            else:
                error_msg = f"업데이트 실패: HTTP {response.status_code}"
                self.logger.error(error_msg)
                
                # 오프라인 큐에 저장
                self._add_to_offline_queue('update_result', {
                    'record_id': record_id,
                    'data': payload
                })
                
                return {
                    'success': False,
                    'message': error_msg + " (오프라인 큐에 저장됨)"
                }
                
        except Exception as e:
            self.logger.error(f"분석 결과 업데이트 실패: {str(e)}")
            
            # 오프라인 큐에 저장
            try:
                update_data = self._map_analysis_result(analysis_result)
                payload = {"fields": update_data}
                self._add_to_offline_queue('update_result', {
                    'record_id': record_id,
                    'data': payload
                })
            except:
                pass
            
            return {
                'success': False,
                'message': f'업데이트 실패: {str(e)} (오프라인 큐에 저장됨)'
            }
    
    def _map_patient_data(self, patient_data: Dict[str, Any], 
                         session_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """환자 데이터를 Airtable 필드에 매핑"""
        # 환자 ID 생성 (PAT_YYYYNNNN 형식)
        today = datetime.now()
        patient_id = f"PAT_{today.strftime('%Y')}{today.strftime('%m%d')}{today.strftime('%H%M')}"
        
        # 세션 ID 생성
        session_id = f"SES_{patient_id.split('_')[1]}_{today.strftime('%H%M')}"
        
        mapped_data = {
            # PATIENT 테이블 필드들
            'patient_id': patient_id,
            'name': patient_data['name'],
            'birth_date': patient_data['birth_date'].strftime('%Y-%m-%d'),
            'registration_number': patient_data['registration_number'],
            'gender': patient_data['gender'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            
            # SESSION 정보
            'session_id': session_id,
            'session_date': today.strftime('%Y-%m-%d'),
            'session_type': 'INITIAL',
            'operator_name': self.config.get('general', 'operator_name', '시스템'),
            'status': 'IN_PROGRESS',
            'started_at': datetime.now().isoformat()
        }
        
        # 선택적 필드들
        if patient_data.get('phone'):
            mapped_data['phone_number'] = patient_data['phone']
        
        if patient_data.get('email'):
            mapped_data['email'] = patient_data['email']
        
        if patient_data.get('notes'):
            mapped_data['notes'] = patient_data['notes']
        
        # 세션 데이터가 있는 경우
        if session_data:
            mapped_data['total_images'] = session_data.get('image_count', 0)
            mapped_data['operator_name'] = session_data.get('operator', '시스템')
        
        return mapped_data
    
    def _map_analysis_result(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과를 Airtable 필드에 매핑"""
        result_id = f"RES_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        mapped_data = {
            # ANALYSIS_RESULT 필드들
            'result_id': result_id,
            'analyzed_at': datetime.now().isoformat(),
            'status': 'COMPLETED',
            'completed_at': datetime.now().isoformat()
        }
        
        # PDF 정보
        if analysis_result.get('pdf_path'):
            pdf_path = Path(analysis_result['pdf_path'])
            mapped_data['pdf_file_name'] = pdf_path.name
            mapped_data['pdf_file_path'] = str(pdf_path.parent)
            mapped_data['pdf_size_kb'] = pdf_path.stat().st_size // 1024 if pdf_path.exists() else 0
        
        # 분석 데이터
        if analysis_result.get('analysis_data'):
            mapped_data['analysis_data'] = json.dumps(analysis_result['analysis_data'], ensure_ascii=False)
        
        # 분석 유형
        mapped_data['analysis_type'] = analysis_result.get('analysis_type', 'CEPHALOMETRIC')
        
        # Web Ceph ID
        if analysis_result.get('web_ceph_id'):
            mapped_data['web_ceph_id'] = analysis_result['web_ceph_id']
        
        # 요약
        if analysis_result.get('summary'):
            mapped_data['summary'] = analysis_result['summary']
        
        return mapped_data
    
    def _add_to_offline_queue(self, action_type: str, data: Dict[str, Any]):
        """오프라인 큐에 작업 추가"""
        try:
            queue_item = {
                'id': f"{action_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'action_type': action_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'retry_count': 0
            }
            
            # 기존 큐 로드
            offline_queue = []
            if self.offline_queue_file.exists():
                with open(self.offline_queue_file, 'r', encoding='utf-8') as f:
                    offline_queue = json.load(f)
            
            # 새 항목 추가
            offline_queue.append(queue_item)
            
            # 큐 저장
            with open(self.offline_queue_file, 'w', encoding='utf-8') as f:
                json.dump(offline_queue, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"오프라인 큐에 작업이 추가되었습니다: {action_type}")
            
        except Exception as e:
            self.logger.error(f"오프라인 큐 저장 실패: {str(e)}")
    
    def process_offline_queue(self) -> Dict[str, Any]:
        """오프라인 큐 처리"""
        try:
            if not self.offline_queue_file.exists():
                return {
                    'success': True,
                    'processed': 0,
                    'failed': 0,
                    'message': '처리할 오프라인 작업이 없습니다'
                }
            
            with open(self.offline_queue_file, 'r', encoding='utf-8') as f:
                offline_queue = json.load(f)
            
            if not offline_queue:
                return {
                    'success': True,
                    'processed': 0,
                    'failed': 0,
                    'message': '처리할 오프라인 작업이 없습니다'
                }
            
            self.logger.info(f"오프라인 큐 처리를 시작합니다: {len(offline_queue)}개 작업")
            
            processed = 0
            failed = 0
            remaining_queue = []
            
            for item in offline_queue:
                try:
                    action_type = item['action_type']
                    data = item['data']
                    
                    if action_type == 'create_patient':
                        # 환자 레코드 생성 재시도
                        url = f"{self.base_url}/{self.table_name}"
                        response = self.session.post(
                            url, 
                            headers=self.headers, 
                            json=data, 
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            processed += 1
                            self.logger.info(f"오프라인 작업 성공: {item['id']}")
                        else:
                            raise Exception(f"HTTP {response.status_code}")
                    
                    elif action_type == 'update_result':
                        # 분석 결과 업데이트 재시도
                        record_id = data['record_id']
                        update_data = data['data']
                        
                        url = f"{self.base_url}/{self.table_name}/{record_id}"
                        response = self.session.patch(
                            url, 
                            headers=self.headers, 
                            json=update_data, 
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            processed += 1
                            self.logger.info(f"오프라인 업데이트 성공: {item['id']}")
                        else:
                            raise Exception(f"HTTP {response.status_code}")
                    
                except Exception as e:
                    item['retry_count'] += 1
                    item['last_error'] = str(e)
                    
                    # 최대 3회 재시도
                    if item['retry_count'] < 3:
                        remaining_queue.append(item)
                        self.logger.warning(f"오프라인 작업 재시도 ({item['retry_count']}/3): {item['id']} - {str(e)}")
                    else:
                        failed += 1
                        self.logger.error(f"오프라인 작업 최종 실패: {item['id']} - {str(e)}")
            
            # 남은 큐 저장
            with open(self.offline_queue_file, 'w', encoding='utf-8') as f:
                json.dump(remaining_queue, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"오프라인 큐 처리 완료: 성공 {processed}개, 실패 {failed}개, 남은 작업 {len(remaining_queue)}개")
            
            return {
                'success': True,
                'processed': processed,
                'failed': failed,
                'remaining': len(remaining_queue),
                'message': f'오프라인 작업 처리 완료: {processed}개 성공, {failed}개 실패'
            }
            
        except Exception as e:
            self.logger.error(f"오프라인 큐 처리 실패: {str(e)}")
            return {
                'success': False,
                'message': f'오프라인 큐 처리 실패: {str(e)}'
            }
    
    def get_patient_records(self, filter_formula: str = None, 
                          max_records: int = 100) -> List[Dict[str, Any]]:
        """환자 레코드 조회"""
        try:
            url = f"{self.base_url}/{self.table_name}"
            params = {'maxRecords': max_records}
            
            if filter_formula:
                params['filterByFormula'] = filter_formula
            
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                records = result.get('records', [])
                
                self.logger.info(f"{len(records)}개의 레코드를 조회했습니다")
                return records
            else:
                self.logger.error(f"레코드 조회 실패: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"레코드 조회 실패: {str(e)}")
            return []
    
    def get_today_statistics(self) -> Dict[str, Any]:
        """오늘의 통계 조회"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            filter_formula = f"{{session_date}} = '{today}'"
            
            records = self.get_patient_records(filter_formula)
            
            # 통계 계산
            total_patients = len(records)
            completed = sum(1 for r in records if r['fields'].get('status') == 'COMPLETED')
            in_progress = sum(1 for r in records if r['fields'].get('status') == 'IN_PROGRESS')
            failed = sum(1 for r in records if r['fields'].get('status') == 'FAILED')
            
            return {
                'date': today,
                'total_patients': total_patients,
                'completed': completed,
                'in_progress': in_progress,
                'failed': failed,
                'success_rate': (completed / total_patients * 100) if total_patients > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"통계 조회 실패: {str(e)}")
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_patients': 0,
                'completed': 0,
                'in_progress': 0,
                'failed': 0,
                'success_rate': 0
            }
    
    def backup_data(self, backup_path: str = None) -> Dict[str, Any]:
        """데이터 백업"""
        try:
            if not backup_path:
                backup_dir = Path(self.config.get('paths', 'backup_folder'))
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / f"airtable_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # 모든 레코드 조회
            all_records = []
            offset = None
            
            while True:
                url = f"{self.base_url}/{self.table_name}"
                params = {'maxRecords': 100}
                if offset:
                    params['offset'] = offset
                
                response = self.session.get(url, headers=self.headers, params=params, timeout=60)
                
                if response.status_code != 200:
                    raise Exception(f"백업 조회 실패: HTTP {response.status_code}")
                
                result = response.json()
                records = result.get('records', [])
                all_records.extend(records)
                
                offset = result.get('offset')
                if not offset:
                    break
            
            # 백업 파일 저장
            backup_data = {
                'backup_date': datetime.now().isoformat(),
                'total_records': len(all_records),
                'records': all_records
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"데이터 백업 완료: {len(all_records)}개 레코드, 파일: {backup_path}")
            
            return {
                'success': True,
                'backup_path': str(backup_path),
                'record_count': len(all_records),
                'message': f'{len(all_records)}개 레코드가 성공적으로 백업되었습니다'
            }
            
        except Exception as e:
            self.logger.error(f"데이터 백업 실패: {str(e)}")
            return {
                'success': False,
                'message': f'데이터 백업 실패: {str(e)}'
            } 