"""시퀀스 모델"""
from .base_model import BaseModel
from ..utils.decorators import require_admin

class Sequence(BaseModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.require_admin = require_admin(db_connector)
        self.table_name = 'sequences'
        self.item_type = 'sequence'
        
    @property
    def admin_required_methods(self):
        return [self.create, self.update, self.delete]
    
    def get_all(self):
        """모든 시퀀스 조회"""
        query = f"SELECT * FROM {self.table_name} ORDER BY name"
        return self._fetch_all(query)

    def get_by_id(self, sequence_id):
        """ID로 시퀀스 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        return self._fetch_one(query, (sequence_id,))

    def get_by_name(self, name):
        """이름으로 시퀀스 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE name = ?"
        return self._fetch_one(query, (name,))
        
    def get_by_project(self, project_id):
        """프로젝트별 시퀀스 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE project_id = ? ORDER BY name"
        return self._fetch_all(query, (project_id,))
    
    def create(self, name, project_id, level_path=None, description=None):
        """시퀀스 생성"""
        query = f"""
            INSERT INTO {self.table_name} (name, project_id, level_path, description, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            RETURNING ID
        """
        try:
            result = self.db_connector.fetch_one(query, (name, project_id, level_path, description))
            self.logger.debug(f"삽입된 시퀀스 ID: {result['id'] if result and 'id' in result else '없음'}")
            return result['id'] if result and 'id' in result else None
        except Exception as e:
            self.logger.error(f"시퀀스 생성 중 오류 발생: {str(e)}", exc_info=True)
            raise

    def update(self, sequence_id, name):
        """시퀀스 정보 수정"""
        query = f"UPDATE {self.table_name} SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        return self._execute(query, (name, sequence_id))

    def delete(self, sequence_id):
        """시퀀스 삭제"""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        return self._execute(query, (sequence_id,))
