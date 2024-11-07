"""버전 관리 서비스"""
from ..models.sequence_version import SequenceVersion
from ..models.worker import Worker
from ..utils.logger import setup_logger
from ..utils.db_utils import convert_date_format

class SequenceVersionService:
    def __init__(self, connector):
        self.connector = connector
        self.logger = setup_logger(__name__)
        self.version_model = SequenceVersion(connector)
        self.worker_model = Worker(connector)

    def create_version(self, sequence_id, version_number=None, worker_name=None, 
                      file_path=None, preview_path=None, comment=None, status=None):
        """새 시퀀스 버전 생성"""
        try:
            self.logger.info(f"시퀀스 버전 생성 시작 - sequence_id: {sequence_id}")
            self.logger.debug(f"입력 파라미터 - version_number: {version_number}, worker_name: {worker_name}")
            self.logger.debug(f"파일 경로 - file_path: {file_path}, preview_path: {preview_path}")

            # 작업자 처리
            worker_name = worker_name or 'system'
            self.logger.debug(f"작업자 이름: {worker_name}")
            
            worker = self._get_or_create_worker(worker_name)
            if not worker:
                return False

            # 버전 번호 처리
            if version_number is None:
                version_number = self._get_next_version_number(sequence_id)
                self.logger.debug(f"자동 생성된 버전 번호: {version_number}")

            # 버전 이름 생성 (v001 형식)
            version_name = f"v{version_number:03d}"
            self.logger.debug(f"생성된 버전 이름: {version_name}")

            # 새 버전 생성
            self.logger.info(f"새 시퀀스 버전 생성 시도 - version_name: {version_name}, version_number: {version_number}")
            result = self.version_model.create(
                sequence_id=sequence_id,
                version_name=version_name,
                version_number=version_number,
                worker_id=worker[0],
                file_path=file_path,
                preview_path=preview_path,
                comment=comment,
                status=status
            )
            
            if result:
                self.logger.info("시퀀스 버전 생성 성공")
            else:
                self.logger.error("시퀀스 버전 생성 실패")
            
            return result
            
        except Exception as e:
            self.logger.error(f"시퀀스 버전 생성 중 예외 발생: {str(e)}", exc_info=True)
            return False

    def _get_or_create_worker(self, worker_name):
        """작업자 조회 또는 생성"""
        worker = self.worker_model.get_by_name(worker_name)
        if not worker:
            self.logger.info(f"작업자 '{worker_name}'가 존재하지 않아 새로 생성")
            if not self.worker_model.create(worker_name):
                self.logger.error(f"작업자 '{worker_name}' 생성 실패")
                return None
            worker = self.worker_model.get_by_name(worker_name)
            self.logger.debug(f"생성된 작업자 정보: {worker}")
        return worker

    def _get_next_version_number(self, sequence_id):
        """다음 시퀀스 버전 번호 조회"""
        try:
            self.logger.debug(f"다음 시퀀스 버전 번호 조회 시작 - sequence_id: {sequence_id}")
            versions = self.version_model.get_all_versions(sequence_id)
            self.logger.debug(f"기존 시퀀스 버전 목록: {versions}")
            
            if not versions:
                self.logger.debug("기존 시퀀스 버전 없음, 버전 1 반환")
                return 1
                
            # 모든 버전 번호 추출
            version_numbers = []
            for version in versions:
                try:
                    version_number = version[3]  # 인덱스 수정
                    if isinstance(version_number, int):
                        version_numbers.append(version_number)
                    else:
                        self.logger.warning(f"잘못된 버전 번호 형식: {version_number}")
                except (ValueError, IndexError) as e:
                    self.logger.error(f"버전 번호 파싱 실패: {e}")
                    continue
            
            if not version_numbers:
                self.logger.debug("파싱 가능한 버전 번호 없음, 버전 1 반환")
                return 1
                
            # 가장 큰 버전 번호 + 1 반환
            next_version = max(version_numbers) + 1
            self.logger.debug(f"다음 시퀀스 버전 번호: {next_version}")
            return next_version
            
        except Exception as e:
            self.logger.error(f"다음 시퀀스 버전 번호 조회 실패: {str(e)}")
            return 1

    def update_version(self, version_id, status=None, comment=None):
        """버전 정보 업데이트"""
        return self.version_model.update(version_id, status=status, comment=comment)

    def get_version_by_id(self, version_id):
        """ID로 버전 정보 조회"""
        return self.version_model.get_by_id(version_id)

    def get_all_versions(self, sequence_id):
        """시퀀스의 모든 버전 조회"""
        try:
            self.logger.debug(f"시퀀스 ID {sequence_id}의 모든 버전 조회 시작")
            cursor = self.connector.cursor()
            
            query = """
                SELECT 
                    v.id,
                    v.name,
                    v.version_number,
                    w.name as worker_name,
                    v.created_at,
                    v.status
                FROM sequence_versions v
                LEFT JOIN workers w ON v.worker_id = w.id
                WHERE v.sequence_id = ?
                ORDER BY v.version_number DESC
            """
            
            self.logger.debug(f"실행 쿼리: {query}")
            cursor.execute(query, (sequence_id,))
            
            versions = cursor.fetchall()
            self.logger.debug(f"조회된 버전 수: {len(versions)}")
            if versions:
                self.logger.debug(f"첫 번째 버전 데이터: {versions[0]}")
                
            return versions
            
        except Exception as e:
            self.logger.error(f"버전 조회 중 오류 발생: {str(e)}", exc_info=True)
            return []

    def get_shot_info(self, sequence_id):
        """샷 정보 조회"""
        try:
            cursor = self.connector.cursor()
            query = """
                SELECT shots.*, 
                       (SELECT version_number 
                        FROM versions 
                        WHERE versions.sequence_id = shots.id 
                        AND versions.is_latest = TRUE) as latest_version
                FROM shots
                WHERE shots.id = ?
            """
            cursor.execute(query, (sequence_id,))
            shot = cursor.fetchone()
            if shot:
                return {
                    'name': shot[2],
                    'status': shot[3],
                    'latest_version': shot[-1] or 'None'
                }
            return None
        except Exception as e:
            self.logger.error(f"샷 정보 조회 실패: {str(e)}")
            return None

    def get_render_root(self):
        """렌더 파일 저장 루트 경로 환"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'render_root'")
            result = cursor.fetchone()
            if result:
                return result[0]
            return "D:/WORKDATA/lhcPipeTool/TestSequence"  # 기본값
        except Exception as e:
            self.logger.error(f"렌더 경로 조회 실패: {str(e)}")
            return "D:/WORKDATA/lhcPipeTool/TestSequence"  # 기본값

    def get_version(self, sequence_id, version_number):
        """특정 샷의 특정 버전 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("""
                SELECT * FROM versions 
                WHERE sequence_id = ? AND version_number = ?
            """, (sequence_id, version_number))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"버전 조회 실패: sequence_id={sequence_id}, version_number={version_number}, error={str(e)}")
            return None

    def get_version_details(self, version_id):
        """버전 상세 정보 조회"""
        try:
            self.logger.debug(f"버전 상세 정보 조회 시작 - version_id: {version_id}")
            cursor = self.connector.cursor()
            
            query = """
                SELECT 
                    v.id,
                    v.name,
                    v.version_number,
                    w.name as worker_name,
                    v.status,
                    v.file_path,
                    v.preview_path,
                    v.render_path,
                    v.comment,
                    v.created_at
                FROM sequence_versions v
                LEFT JOIN workers w ON v.worker_id = w.id
                WHERE v.id = ?
            """
            
            self.logger.debug(f"실행 쿼리: {query}")
            cursor.execute(query, (version_id,))
            
            result = cursor.fetchone()
            self.logger.debug(f"조회 결과: {result}")
            
            if result:
                version_details = {
                    'id': result[0],
                    'name': result[1],
                    'version_number': result[2],
                    'worker_name': result[3],
                    'status': result[4],
                    'file_path': result[5],
                    'preview_path': result[6],
                    'render_path': result[7],
                    'comment': result[8],
                    'created_at': convert_date_format(result[9])
                }
                self.logger.debug(f"변환된 버전 정보: {version_details}")
                return version_details
                
            self.logger.warning(f"버전 정보를 찾을 수 없음 - version_id: {version_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"버전 상세 정보 조회 실패: {str(e)}", exc_info=True)
            return None

    def delete_version(self, version_id):
        """버전 삭제"""
        try:
            self.logger.info(f"버전 삭제 시도 - version_id: {version_id}")
            
            # 버전 정보 조회
            version = self.get_version_details(version_id)
            if not version:
                self.logger.error("삭제할 버전을 찾을 수 없음")
                return False
                
            # 버전 삭제
            result = self.version_model.delete(version_id)
            
            if result:
                self.logger.info("버전 삭제 성공")
            else:
                self.logger.error("버전 삭제 실패")
                
            return result
            
        except Exception as e:
            self.logger.error(f"버전 삭제 중 예외 발생: {str(e)}", exc_info=True)
            return False
        
    def get_latest_version(self, sequence_id):
        """시퀀스의 최신 버전 조회"""
        return self.version_model.get_latest_version(sequence_id)
    