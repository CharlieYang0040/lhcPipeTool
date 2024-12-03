"""버전 서비스 기본 클래스"""
from ..models.version_models import ShotVersion, SequenceVersion, ProjectVersion
from ..models.worker import Worker
from ..utils.db_utils import convert_date_format
from ..utils.event_system import EventSystem
class BaseVersionService:
    def __init__(self, db_connector, logger):
        self.db_connector = db_connector
        self.logger = logger
        self.table_name = None  # 하위 클래스에서 정의
        self.version_models = {
            "shot_id": ShotVersion(db_connector),
            "sequence_id": SequenceVersion(db_connector),
            "project_id": ProjectVersion(db_connector)
        }
        self.worker_model = Worker(db_connector)

    def create_version(self, item_id, version_number=None, worker_name=None, 
                      file_path=None, render_path=None, preview_path=None, comment=None, status=None):
        """새 버전 생성"""
        try:
            self.logger.info(f"""버전 생성 시도: 
                            {self.get_foreign_key()}: {item_id}
                            worker_name: {worker_name}
                            file_path: {file_path}
                            render_path: {render_path}
                            preview_path: {preview_path}
                            comment: {comment}
                            status: {status}
                        """)

            # 버전 번호 처리
            if version_number is None:
                version_number = self._get_next_version_number(item_id)

            # 버전 이름 생성
            version_name = f"v{version_number:03d}"

            # 작업자 처리
            worker = self._get_worker(worker_name)
            if not worker:
                raise Exception("작업자 조회 실패")

            # 새 버전 생성
            create_data = {
                'item_id': item_id,
                'version_name': version_name,
                'version_number': version_number,
                'worker_id': worker['id'],
                'file_path': file_path,
                'render_path': render_path,
                'preview_path': preview_path,
                'comment': comment,
                'status': status
            }
            result = self.version_models[self.get_foreign_key()].create(**create_data)
            if result:
                self.db_connector.commit()
                EventSystem.notify('version_updated')  # 이벤트 발생
                return result
            else:
                raise Exception("버전 생성 실패")
            
        except Exception as e:
            self.logger.error(f"버전 생성 중 예외 발생: {str(e)}", exc_info=True)
            return False

    def _get_worker(self, worker_name):
        """작업자 조회"""
        worker = self.worker_model.get_by_name(worker_name)
        if not worker:
            return None
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
            cursor = self.db_connector.cursor()
            
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

    def get_project_details(self, project_id):
        """프로젝트 상세 정보 조회"""
        try:
            cursor = self.db_connector.cursor()
            
            query = """
                SELECT p.*,
                       (SELECT COUNT(*) FROM PROJECT_VERSIONS 
                        WHERE project_id = p.id) as version_count,
                       (SELECT FIRST 1 preview_path FROM PROJECT_VERSIONS 
                        WHERE project_id = p.id 
                        ORDER BY created_at DESC) as latest_preview
                FROM PROJECTS p
                WHERE p.id = ?
            """
            cursor.execute(query, (project_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
                
            return {
                'id': result[0],
                'name': result[1],
                'path': result[2],
                'description': result[3],
                'created_at': convert_date_format(result[4]),
                'version_count': result[5],
                'preview_path': result[6]
            }
            
        except Exception as e:
            self.logger.error(f"프로젝트 상세 정보 조회 실패: {str(e)}", exc_info=True)
            return None

    def get_sequence_details(self, sequence_id):
        """시퀀스 상세 정보 조회"""
        try:
            cursor = self.db_connector.cursor()
            
            query = """
                SELECT s.id, s.name, s.project_id, s.level_path, s.description, s.created_at,
                    p.name as project_name,
                    (SELECT COUNT(*) FROM SHOTS 
                        WHERE sequence_id = s.id) as shot_count,
                    (SELECT FIRST 1 preview_path FROM SEQUENCE_VERSIONS 
                        WHERE sequence_id = s.id 
                        ORDER BY created_at DESC) as latest_preview
                FROM SEQUENCES s
                JOIN PROJECTS p ON s.project_id = p.id
                WHERE s.id = ?
            """
            cursor.execute(query, (sequence_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
                
            return {
                'id': result[0],
                'name': result[1],
                'project_id': result[2],
                'level_path': result[3],
                'description': result[4],
                'created_at': convert_date_format(result[5]),
                'project_name': result[6],
                'shot_count': result[7],
                'preview_path': result[8]
            }
            
        except Exception as e:
            self.logger.error(f"시퀀스 상세 정보 조회 실패: {str(e)}", exc_info=True)
            return None


    def get_shot_details(self, shot_id):
        """샷 상세 정보 조회"""
        try:
            cursor = self.db_connector.cursor()
            
            query = """
                SELECT sh.*,
                       s.name as sequence_name,
                       p.name as project_name,
                       (SELECT COUNT(*) FROM VERSIONS 
                        WHERE shot_id = sh.id) as version_count,
                       (SELECT FIRST 1 preview_path FROM VERSIONS 
                        WHERE shot_id = sh.id 
                        ORDER BY created_at DESC) as latest_preview
                FROM SHOTS sh
                JOIN SEQUENCES s ON sh.sequence_id = s.id
                JOIN PROJECTS p ON s.project_id = p.id
                WHERE sh.id = ?
            """
            cursor.execute(query, (shot_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
                
            return {
                'id': result[0],
                'name': result[1],
                'sequence_id': result[2],
                'status': result[3],
                'description': result[4],
                'created_at': convert_date_format(result[5]),
                'sequence_name': result[6],
                'project_name': result[7],
                'version_count': result[8],
                'preview_path': result[9]
            }
            
        except Exception as e:
            self.logger.error(f"샷 상세 정보 조회 실패: {str(e)}", exc_info=True)
            return None

    def get_version_details(self, version_id):
        """버전 상세 정보 조회"""
        try:
            cursor = self.db_connector.cursor()
            
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
            cursor = self.db_connector.cursor()
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
