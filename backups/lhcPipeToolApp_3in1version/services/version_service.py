"""버전 관리 서비스"""
from ..models.version import Version
from ..models.worker import Worker
from ..services.project_service import ProjectService
from ..services.worker_service import WorkerService
from ..utils.logger import setup_logger
import os

class VersionService:
    def __init__(self, db_connector):
        self.connector = db_connector
        self.logger = setup_logger(__name__)
        self.version_model = Version(db_connector)
        self.worker_model = Worker(db_connector)
        self.project_service = ProjectService(db_connector)
        self.worker_service = WorkerService(db_connector)

    def get_version_by_id(self, id_value):
        """ID로 버전 조회"""
        try:
            cursor = self.connector.cursor()
            query = """
                SELECT * FROM versions 
                WHERE id = ?
            """
            cursor.execute(query, (id_value,))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"버전 조회 실패: {str(e)}")
            return None

    def create_version(self, version_type, id_value, worker_name, file_path=None, 
                      preview_path=None, comment=None, render_path=None):
        """새 버전 생성"""
        try:
            # 작업자 ID 가져오기 또는 생성
            worker = self.worker_service.get_worker_by_name(worker_name)
            if not worker:
                return False
            
            # worker 튜플에서 ID 추출 (첫 번째 요소가 ID)
            worker_id = worker[0]

            # 다음 버전 번호 가져오기
            version_number = self.get_next_version_number(version_type, id_value)
            
            # 버전 타입에 따른 ID 설정
            project_id = id_value if version_type == 'project' else None
            sequence_id = id_value if version_type == 'sequence' else None
            shot_id = id_value if version_type == 'shot' else None
            
            # 이전 버전들의 is_latest 상태 업데이트
            self._update_previous_versions(version_type, id_value)
            
            # 새 버전 생성
            cursor = self.connector.cursor()
            query = """
                INSERT INTO versions (
                    id, version_type, version_number, worker_id,
                    project_id, sequence_id, shot_id,
                    file_path, preview_path, render_path,
                    comment, is_latest, status
                ) VALUES (
                    NEXT VALUE FOR versions_id_seq, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE, 'pending'
                )
            """
            
            cursor.execute(query, (
                version_type, version_number, worker_id,
                project_id, sequence_id, shot_id,
                file_path, preview_path, render_path,
                comment
            ))
            
            self.connector.commit()
            self.logger.info(f"새 버전 생성 완료: {version_type} - {version_number}")
            return True
            
        except Exception as e:
            self.logger.error(f"버전 생성 실패: {str(e)}")
            self.connector.rollback()
            return False

    def _update_previous_versions(self, version_type, id_value):
        """이전 버전들의 is_latest 상태 업데이트"""
        try:
            cursor = self.connector.cursor()
            query = """
                UPDATE versions 
                SET is_latest = FALSE
                WHERE version_type = ?
                AND (
                    (version_type = 'project' AND project_id = ?) OR
                    (version_type = 'sequence' AND sequence_id = ?) OR
                    (version_type = 'shot' AND shot_id = ?)
                )
            """
            cursor.execute(query, (version_type, id_value, id_value, id_value))
            self.connector.commit()
            return True
        except Exception as e:
            self.logger.error(f"이전 버전 상태 업데이트 실패: {str(e)}")
            self.connector.rollback()
            return False

    def update_version(self, version_id, status=None, comment=None):
        """버전 정보 업데이트"""
        return self.version_model.update(version_id, status=status, comment=comment)

    def get_version_by_id(self, version_id):
        """ID로 버전 정보 조회"""
        return self.version_model.get_by_id(version_id)

    def get_all_versions(self, shot_id):
        """샷의 모든 버전 조회"""
        self.logger.info(f"버전 목록 조회 시도: shot_id={shot_id}")
        try:
            cursor = self.connector.cursor()
            query = """
                SELECT versions.*, workers.name as worker_name
                FROM versions
                LEFT JOIN workers ON versions.worker_id = workers.id
                WHERE versions.shot_id = ?
                ORDER BY versions.version_number DESC
            """
            self.logger.info(f"실행할 SQL: {query}")
            self.logger.info(f"파라미터: shot_id={shot_id}")
            cursor.execute(query, (shot_id,))
            versions = cursor.fetchall()
            self.logger.info(f"조회된 버전 수: {len(versions)}")
            return versions
        except Exception as e:
            self.logger.error(f"버전 목록 조회 실패: {str(e)}", exc_info=True)
            return []

    def get_shot_info(self, shot_id):
        """샷 정보 조회"""
        try:
            cursor = self.connector.cursor()
            query = """
                SELECT shots.*, 
                       (SELECT version_number 
                        FROM versions 
                        WHERE versions.shot_id = shots.id 
                        AND versions.is_latest = TRUE) as latest_version
                FROM shots
                WHERE shots.id = ?
            """
            cursor.execute(query, (shot_id,))
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

    def get_next_version_number(self, version_type, id_value):
        """다음 버전 번호 조회"""
        try:
            cursor = self.connector.cursor()
            query = """
                SELECT COALESCE(MAX(version_number), 0) + 1
                FROM versions
                WHERE version_type = ?
                AND (
                    (version_type = 'project' AND project_id = ?) OR
                    (version_type = 'sequence' AND sequence_id = ?) OR
                    (version_type = 'shot' AND shot_id = ?)
                )
            """
            cursor.execute(query, (version_type, id_value, id_value, id_value))
            result = cursor.fetchone()
            return result[0] if result else 1
        except Exception as e:
            self.logger.error(f"다음 버전 번호 조회 실패: {str(e)}")
            return 1

    def get_version(self, shot_id, version_number):
        """특정 샷의 특정 버전 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("""
                SELECT * FROM versions 
                WHERE shot_id = ? AND version_number = ?
            """, (shot_id, version_number))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"버전 조회 실패: shot_id={shot_id}, version_number={version_number}, error={str(e)}")
            return None

    def get_version_details(self, version_id):
        """버전 상세 정보 조회"""
        try:
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
                FROM versions v
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
                    'created_at': result[9]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"버전 상세 정보 조회 실패: {str(e)}", exc_info=True)
            return None

    def get_version_path(self, version_type, project_name, sequence_name=None, shot_name=None, version_number=None):
        """버전 경로 생성"""
        try:
            # 기본 경로 가져오기 (settings 테이블에서)
            base_path = self.get_base_path()
            if not base_path:
                self.logger.error("기본 경로 설정을 찾을 수 없습니다.")
                return None

            version_str = f"v{version_number:03d}" if version_number else ""
            
            # 버전 타입에 따른 경로 생성
            if version_type == 'project':
                return os.path.join(base_path, 'image', project_name, version_str)
            elif version_type == 'sequence':
                if not sequence_name:
                    return None
                return os.path.join(base_path, 'image', project_name, sequence_name, version_str)
            elif version_type == 'shot':
                if not (sequence_name and shot_name):
                    return None
                return os.path.join(base_path, 'image', project_name, sequence_name, shot_name, version_str)
            
            return None
        except Exception as e:
            self.logger.error(f"버전 경로 생성 실패: {str(e)}")
            return None

    def get_base_path(self):
        """기본 경로 설정 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("""
                SELECT setting_value 
                FROM settings 
                WHERE setting_key = 'base_path'
            """)
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"기본 경로 설정 조회 실패: {str(e)}")
            return None

    def get_versions_by_type(self, version_type, id_value):
        """특정 타입의 버전 목록 조회"""
        self.logger.info(f"버전 목록 조회: type={version_type}, id={id_value}")
        try:
            cursor = self.connector.cursor()
            query = """
                SELECT v.*, w.name as worker_name
                FROM versions v
                LEFT JOIN workers w ON v.worker_id = w.id
                WHERE v.version_type = ? AND v.{}_id = ?
                ORDER BY v.version_number DESC
            """.format(version_type)
            
            cursor.execute(query, (version_type, id_value))
            versions = cursor.fetchall()
            self.logger.info(f"조회된 버전 수: {len(versions)}")
            return versions
        except Exception as e:
            self.logger.error(f"버전 목록 조회 실패: {str(e)}", exc_info=True)
            return []

    def get_latest_version_by_type(self, version_type, id_value):
        """특정 타입의 최신 버전 조회"""
        try:
            cursor = self.connector.cursor()
            query = """
                SELECT v.*, w.name as worker_name
                FROM versions v
                LEFT JOIN workers w ON v.worker_id = w.id
                WHERE v.version_type = ? 
                AND v.{}_id = ?
                AND v.is_latest = TRUE
            """.format(version_type)
            
            cursor.execute(query, (version_type, id_value))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"최신 버전 조회 실패: {str(e)}")
            return None

    def get_version_info(self, version_type, id_value):
        """버전 정보 조회 (프로젝트/시퀀스/샷)"""
        try:
            cursor = self.connector.cursor()
            table_name = f"{version_type}s"
            query = f"""
                SELECT t.*, 
                       (SELECT version_number 
                        FROM versions 
                        WHERE versions.{version_type}_id = t.id 
                        AND versions.is_latest = TRUE
                        AND versions.version_type = ?) as latest_version
                FROM {table_name} t
                WHERE t.id = ?
            """
            cursor.execute(query, (version_type, id_value))
            result = cursor.fetchone()
            if result:
                return {
                    'name': result[1] if version_type == 'project' else result[2],
                    'status': result[3] if version_type != 'project' else None,
                    'latest_version': result[-1] or 'None'
                }
            return None
        except Exception as e:
            self.logger.error(f"정보 조회 실패: {str(e)}")
            return None

    def get_version_hierarchy(self, version_id):
        """버전의 계층 구조 정보 조회"""
        try:
            cursor = self.connector.cursor()
            query = """
                SELECT 
                    v.version_type,
                    p.name as project_name,
                    s.name as sequence_name,
                    sh.name as shot_name
                FROM versions v
                LEFT JOIN projects p ON v.project_id = p.id
                LEFT JOIN sequences s ON v.sequence_id = s.id
                LEFT JOIN shots sh ON v.shot_id = sh.id
                WHERE v.id = ?
            """
            cursor.execute(query, (version_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'version_type': result[0],
                    'project_name': result[1],
                    'sequence_name': result[2],
                    'shot_name': result[3]
                }
            return None
        except Exception as e:
            self.logger.error(f"계층 구조 정보 조회 실패: {str(e)}")
            return None