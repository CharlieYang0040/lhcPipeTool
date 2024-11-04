"""시퀀스 모델"""
from .base_model import BaseModel
from ..database.table_manager import TableManager

class Sequence(BaseModel):
    def create(self, name, project_id, description=None):
        """시퀀스 생성
        Args:
            name (str): 시퀀스 이름
            project_id (int): 프로젝트 ID
            description (str, optional): 시퀀스 설명
        """
        query = """
            INSERT INTO sequences (name, project_id, description) 
            VALUES (?, ?, ?)
        """

        # 테이블 구조 조회
        table_manager = TableManager(self.connector)
        table_structure = table_manager.get_table_structure("SEQUENCES")
        self.logger.info(f"테이블 구조: {table_structure}")
        return self._execute(query, (name, project_id, description))

    def get_by_project(self, project_id):
        """프로젝트별 시퀀스 조회"""
        query = """
            SELECT * FROM sequences 
            WHERE project_id = ? 
            ORDER BY name
        """
        return self._fetch_all(query, (project_id,))

    def update(self, sequence_id, name):
        """시퀀스 정보 수정"""
        query = """
            UPDATE sequences 
            SET name = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """
        return self._execute(query, (name, sequence_id))

    def delete(self, sequence_id):
        """시퀀스 삭제"""
        query = "DELETE FROM sequences WHERE id = ?"
        return self._execute(query, (sequence_id,))

    def get_by_id(self, sequence_id):
        """ID로 시퀀스 조회"""
        query = "SELECT * FROM sequences WHERE id = ?"
        return self._fetch_one(query, (sequence_id,))