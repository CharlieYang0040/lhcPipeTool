"""프로젝트 모델"""
from .base_model import BaseModel

class Project(BaseModel):
    def create(self, name):
        """프로젝트 생성"""
        query = "INSERT INTO projects (name) VALUES (?)"
        return self._execute(query, (name,))

    def get_by_id(self, project_id):
        """ID로 프로젝트 조회"""
        query = "SELECT * FROM projects WHERE id = ?"
        return self._fetch_one(query, (project_id,))

    def get_all(self):
        """모든 프로젝트 조회"""
        query = "SELECT * FROM projects ORDER BY created_at DESC"
        return self._fetch_all(query)

    def update(self, project_id, name):
        """프로젝트 정보 수정"""
        query = """
            UPDATE projects 
            SET name = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """
        return self._execute(query, (name, project_id))

    def delete(self, project_id):
        """프로젝트 삭제"""
        query = "DELETE FROM projects WHERE id = ?"
        return self._execute(query, (project_id,))