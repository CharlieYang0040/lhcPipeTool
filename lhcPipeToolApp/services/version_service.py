"""버전 관리 서비스"""
from ..models.version import Version
from ..models.worker import Worker
from ..utils.logger import setup_logger

class VersionService:
    def __init__(self, connector):
        self.connector = connector
        self.logger = setup_logger(__name__)
        self.version_model = Version(connector)
        self.worker_model = Worker(connector)

    def create_version(self, shot_id, version_number=None, worker_name=None, 
                      file_path=None, preview_path=None, comment=None):
        """새 버전 생성"""
        try:
            # worker_name이 없으면 'system'으로 설정
            if not worker_name:
                worker_name = 'system'
                
            # 작업자 확인 또는 생성
            worker = self.worker_model.get_by_name(worker_name)
            if not worker:
                if not self.worker_model.create(worker_name):
                    return False
                worker = self.worker_model.get_by_name(worker_name)

            # 버전 번호가 지정되지 않은 경우 자동 생성
            if version_number is None:
                versions = self.version_model.get_all_versions(shot_id)
                if not versions:
                    version_number = 1
                else:
                    # 'v001' 형식에서 숫자만 추출
                    latest_version = versions[0][2]  # version_number 컬럼
                    if isinstance(latest_version, str) and latest_version.startswith('v'):
                        version_number = int(latest_version[1:]) + 1
                    else:
                        version_number = int(latest_version) + 1

            # 새 버전 생성
            return self.version_model.create(
                shot_id=shot_id,
                version_number=version_number,  # 이미 정수형으로 처리됨
                worker_id=worker[0],
                file_path=file_path,
                preview_path=preview_path,
                comment=comment
            )
        except Exception as e:
            self.logger.error(f"버전 생성 실패: {str(e)}")
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
        """렌더 파일 저장 루트 경로 ��환"""
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

    def get_next_version_number(self, shot_id):
        """다음 버전 번호 반환"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("""
                SELECT MAX(version_number) 
                FROM versions 
                WHERE shot_id = ?
            """, (shot_id,))
            result = cursor.fetchone()
            if result[0] is None:
                return 1
            return result[0] + 1
        except Exception as e:
            self.logger.error(f"다음 버전 번호 조회 실패: {str(e)}")
            raise

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