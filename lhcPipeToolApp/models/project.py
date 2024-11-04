"""프로젝트 모델"""
from .base_model import BaseModel
from ..database.table_manager import TableManager

class Project(BaseModel):
    def create(self, name, path=None, description=None):
        """프로젝트 생성
        Args:
            name (str): 프로젝트 이름
            path (str, optional): 프로젝트 경로
            description (str, optional): 프로젝트 설명
        """
        query = """
            INSERT INTO projects (name, path, description) 
            VALUES (?, ?, ?)
        """

        # 테이블 구조 조회
        table_manager = TableManager(self.connector)
        table_structure = table_manager.get_table_structure("PROJECTS")
        self.logger.info(f"테이블 구조: {table_structure}")
        return self._execute(query, (name, path, description))

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