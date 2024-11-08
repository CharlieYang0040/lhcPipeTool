"""버전 서비스 기본 클래스"""
from ..models.version_models import ShotVersion, SequenceVersion, ProjectVersion
from ..models.worker import Worker
from ..utils.logger import setup_logger
from ..utils.db_utils import convert_date_format

class BaseVersionService:
    def __init__(self, connector, logger):
        self.connector = connector
        self.logger = logger
        self.table_name = None  # 하위 클래스에서 정의
        self.version_models = {
            "shot_id": ShotVersion(connector),
            "sequence_id": SequenceVersion(connector),
            "project_id": ProjectVersion(connector)
        }
        self.worker_model = Worker(connector)

    def create_version(self, item_id, version_number=None, worker_name=None, 
                      file_path=None, preview_path=None, comment=None, status=None):
        """새 버전 생성"""
        try:
            self.logger.info(f"버전 생성 시작 - {self.get_foreign_key()}: {item_id}")
            
            # 작업자 처리
            worker_name = worker_name or 'system'
            worker = self._get_or_create_worker(worker_name)
            if not worker:
                return False

            # 버전 번호 처리
            if version_number is None:
                version_number = self._get_next_version_number(item_id)

            # 버전 이름 생성
            version_name = f"v{version_number:03d}"

            # 새 버전 생성
            create_data = {
                'item_id': item_id,
                'version_name': version_name,
                'version_number': version_number,
                'worker_id': worker[0],
                'file_path': file_path,
                'preview_path': preview_path,
                'comment': comment,
                'status': status
            }
            
            return self.version_models[self.get_foreign_key()].create(**create_data)
            
        except Exception as e:
            self.logger.error(f"버전 생성 중 예외 발생: {str(e)}", exc_info=True)
            return False

    def _get_or_create_worker(self, worker_name):
        """작업자 조회 또는 생성"""
        worker = self.worker_model.get_by_name(worker_name)
        if not worker:
            if not self.worker_model.create(worker_name):
                return None
            worker = self.worker_model.get_by_name(worker_name)
        return worker

    def _get_next_version_number(self, item_id):
        """다음 버전 번호 조회"""
        try:
            versions = self.get_all_versions(item_id)
            if not versions:
                return 1
                
            version_numbers = []
            for version in versions:
                try:
                    version_number = version[2]  # version_number column
                    if isinstance(version_number, int):
                        version_numbers.append(version_number)
                except (ValueError, IndexError):
                    continue
            
            return max(version_numbers) + 1 if version_numbers else 1
            
        except Exception as e:
            self.logger.error(f"다음 버전 번호 조회 실패: {str(e)}")
            return 1

    def get_all_versions(self, item_id):
        """모든 버전 조회"""
        try:
            cursor = self.connector.cursor()
            
            query = f"""
                SELECT 
                    v.id,
                    v.name,
                    v.version_number,
                    w.name as worker_name,
                    v.created_at,
                    v.status
                FROM {self.table_name} v
                LEFT JOIN workers w ON v.worker_id = w.id
                WHERE v.{self.get_foreign_key()} = ?
                ORDER BY v.version_number DESC
            """
            
            cursor.execute(query, (item_id,))
            return cursor.fetchall()
            
        except Exception as e:
            self.logger.error(f"버전 조회 중 오류 발생: {str(e)}", exc_info=True)
            return []

    def get_version_details(self, version_id):
        """버전 상세 정보 조회"""
        try:
            cursor = self.connector.cursor()
            
            query = f"""
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
                FROM {self.table_name} v
                LEFT JOIN workers w ON v.worker_id = w.id
                WHERE v.id = ?
            """
            
            cursor.execute(query, (version_id,))
            result = cursor.fetchone()
            
            if result:
                return {
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
            return None
            
        except Exception as e:
            self.logger.error(f"버전 상세 정보 조회 실패: {str(e)}", exc_info=True)
            return None

    def update_version(self, version_id, status=None, comment=None):
        """버전 정보 업데이트"""
        return self.version_models[self.get_foreign_key()].update(version_id, status=status, comment=comment)

    def delete_version(self, version_id):
        """버전 삭제"""
        try:
            version = self.get_version_details(version_id)
            if not version:
                return False
            return self.version_models[self.get_foreign_key()].delete(version_id)
            
        except Exception as e:
            self.logger.error(f"버전 삭제 중 예외 발생: {str(e)}", exc_info=True)
            return False

    def get_render_root(self):
        """렌더 파일 저장 루트 경로"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'render_root'")
            result = cursor.fetchone()
            return result[0] if result else "D:/WORKDATA/lhcPipeTool/TestSequence"
        except Exception as e:
            self.logger.error(f"렌더 경로 조회 실패: {str(e)}")
            return "D:/WORKDATA/lhcPipeTool/TestSequence"

    def get_foreign_key(self):
        """외래키 필드명 반환 - 하위 클래스에서 구현"""
        raise NotImplementedError
    
    def get_latest_version(self, item_id):
        """최신 버전 조회"""
        return self.version_models[self.get_foreign_key()].get_latest_version(item_id)
