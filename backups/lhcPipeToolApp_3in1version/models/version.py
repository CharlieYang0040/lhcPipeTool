"""버전 모델"""
from .base_model import BaseModel
from ..utils.logger import setup_logger

class Version(BaseModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.logger = setup_logger(__name__)

    def create(self, version_type, version_number, worker_id, file_path=None, 
              preview_path=None, render_path=None, comment=None, 
              project_id=None, sequence_id=None, shot_id=None):
        """새 버전 생성"""
        self.logger.info(f"""버전 생성 시도:
            version_type: {version_type}
            version_number: {version_number}
            worker_id: {worker_id}
            project_id: {project_id}
            sequence_id: {sequence_id}
            shot_id: {shot_id}
        """)
        
        # 버전 타입에 따라 이전 버전 업데이트
        if version_type == 'project':
            self._update_previous_versions(project_id=project_id)
        elif version_type == 'sequence':
            self._update_previous_versions(sequence_id=sequence_id)
        elif version_type == 'shot':
            self._update_previous_versions(shot_id=shot_id)
        
        version_name = f"v{version_number:03d}"
        
        query = """
            INSERT INTO versions 
            (id, version_type, name, project_id, sequence_id, shot_id, 
             version_number, worker_id, file_path, preview_path, 
             render_path, comment, is_latest) 
            VALUES (
                (SELECT COALESCE(MAX(id), 0) + 1 FROM versions),
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE
            )
        """
        
        try:
            result = self._execute(query, (
                version_type, version_name, project_id, sequence_id, shot_id,
                version_number, worker_id, file_path, preview_path, 
                render_path, comment
            ))
            return result
        except Exception as e:
            self.logger.error(f"버전 생성 중 오류 발생: {str(e)}", exc_info=True)
            return False

    def _update_previous_versions(self, project_id=None, sequence_id=None, shot_id=None):
        """이전 버전들의 is_latest 상태 업데이트"""
        conditions = []
        params = []
        
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if sequence_id:
            conditions.append("sequence_id = ?")
            params.append(sequence_id)
        if shot_id:
            conditions.append("shot_id = ?")
            params.append(shot_id)
            
        where_clause = " AND ".join(conditions)
        query = f"""
            UPDATE versions 
            SET is_latest = FALSE 
            WHERE {where_clause}
        """
        return self._execute(query, tuple(params))

    def get_versions(self, version_type, id_value):
        """특정 타입의 모든 버전 조회"""
        id_column = f"{version_type}_id"
        query = f"""
            SELECT v.*, w.name as worker_name 
            FROM versions v
            LEFT JOIN workers w ON v.worker_id = w.id
            WHERE v.{id_column} = ?
            ORDER BY v.version_number DESC
        """
        return self._fetch_all(query, (id_value,))

    def get_latest_version(self, shot_id):
        """샷의 최신 버전 조회"""
        query = """
            SELECT v.*, w.name as worker_name 
            FROM versions v
            JOIN workers w ON v.worker_id = w.id
            WHERE v.shot_id = ? AND v.is_latest = TRUE
        """
        return self._fetch_one(query, (shot_id,))

    def get_all_versions(self, shot_id):
        """샷의 모든 버전 조회"""
        query = """
            SELECT v.*, w.name as worker_name 
            FROM versions v
            JOIN workers w ON v.worker_id = w.id
            WHERE v.shot_id = ?
            ORDER BY v.version_number DESC
        """
        return self._fetch_all(query, (shot_id,))

    def update_status(self, version_id, status):
        """버전 상태 업데이트"""
        query = """
            UPDATE versions 
            SET status = ? 
            WHERE id = ?
        """
        return self._execute(query, (status, version_id))
    
    def get_by_id(self, version_id):
        """ID로 버전 조회"""
        query = "SELECT * FROM versions WHERE id = ?"
        return self._fetch_one(query, (version_id,))

    def get_versions_by_type(self, version_type, id_value):
        """특정 타입의 모든 버전 조회"""
        query = f"""
            SELECT v.*, w.name as worker_name 
            FROM versions v
            LEFT JOIN workers w ON v.worker_id = w.id
            WHERE v.version_type = ? 
            AND v.{version_type}_id = ?
            ORDER BY v.version_number DESC
        """
        return self._fetch_all(query, (version_type, id_value))

    def get_latest_version_by_type(self, version_type, id_value):
        """특정 타입의 최신 버전 조회"""
        query = f"""
            SELECT v.*, w.name as worker_name 
            FROM versions v
            LEFT JOIN workers w ON v.worker_id = w.id
            WHERE v.version_type = ? 
            AND v.{version_type}_id = ?
            AND v.is_latest = TRUE
        """
        return self._fetch_one(query, (version_type, id_value))

    def update_version_path(self, version_id, new_path):
        """버전 경로 업데이트"""
        query = """
            UPDATE versions 
            SET path = ? 
            WHERE id = ?
        """
        return self._execute(query, (new_path, version_id))
