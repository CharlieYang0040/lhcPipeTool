"""프로젝트 모델"""
from .base_model import BaseModel
from ..utils.decorators import require_admin

class Project(BaseModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.require_admin = require_admin(db_connector)
        self.table_name = 'projects'
        self.item_type = 'project'
        
    @property
    def admin_required_methods(self):
        return [self.create, self.update, self.delete]
    
    def get_all(self):
        """모든 프로젝트 조회"""
        query = f"SELECT * FROM {self.table_name} ORDER BY name"
        return self._fetch_all(query)

    def get_by_id(self, project_id):
        """ID로 프로젝트 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        return self._fetch_one(query, (project_id,))

    def get_by_name(self, name):
        """이름으로 프로젝트 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE name = ?"
        return self._fetch_one(query, (name,))
        
    def get_full_project_structure(self):
        """프로젝트, 시퀀스, 샷, 그리고 최신 버전 정보를 모두 가져옵니다."""
        query = """
        WITH
        LatestProjectVersion AS (
            SELECT pv.project_id, pv.preview_path
            FROM project_versions pv
            WHERE pv.version_number = (
                SELECT MAX(version_number)
                FROM project_versions
                WHERE project_id = pv.project_id
            )
        ),
        LatestSequenceVersion AS (
            SELECT sv.sequence_id, sv.preview_path
            FROM sequence_versions sv
            WHERE sv.version_number = (
                SELECT MAX(version_number)
                FROM sequence_versions
                WHERE sequence_id = sv.sequence_id
            )
        ),
        LatestShotVersion AS (
            SELECT shv.shot_id, shv.preview_path
            FROM versions shv
            WHERE shv.version_number = (
                SELECT MAX(version_number)
                FROM versions
                WHERE shot_id = shv.shot_id
            )
        )
        SELECT
            p.id AS project_id,
            p.name AS project_name,
            s.id AS sequence_id,
            s.name AS sequence_name,
            sh.id AS shot_id,
            sh.name AS shot_name,
            lpv.preview_path AS project_preview,
            lsv.preview_path AS sequence_preview,
            lshv.preview_path AS shot_preview
        FROM projects p
        LEFT JOIN sequences s ON s.project_id = p.id
        LEFT JOIN shots sh ON sh.sequence_id = s.id
        LEFT JOIN LatestProjectVersion lpv ON lpv.project_id = p.id
        LEFT JOIN LatestSequenceVersion lsv ON lsv.sequence_id = s.id
        LEFT JOIN LatestShotVersion lshv ON lshv.shot_id = sh.id
        ORDER BY p.name, s.name, sh.name
        """
        return self._fetch_all(query)

    def create(self, name, path=None, description=None):
        """프로젝트 생성"""
        query = f"""
            INSERT INTO {self.table_name} (name, path, description, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            RETURNING ID
        """
        try:
            result = self.db_connector.fetch_one(query, (name, path, description))
            self.logger.debug(f"삽입된 프로젝트 ID: {result['id'] if result and 'id' in result else '없음'}")
            return result['id'] if result and 'id' in result else None
        except Exception as e:
            self.logger.error(f"프로젝트 생성 중 오류 발생: {str(e)}", exc_info=True)
            raise

    def update(self, project_id, name):
        """프로젝트 정보 수정"""
        query = f"UPDATE {self.table_name} SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        return self._execute(query, (name, project_id))

    def delete(self, project_id):
        """프로젝트 삭제"""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        return self._execute(query, (project_id,))