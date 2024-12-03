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
        
    @require_admin
    def create(self, name, path=None, description=None):
        """프로젝트 생성"""
        query = f"""
            INSERT INTO {self.table_name} (name, path, description, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """
        cursor = self._execute(query, (name, path, description))
        return cursor.lastrowid if cursor else None

    @require_admin
    def update(self, project_id, name):
        """프로젝트 정보 수정"""
        query = f"UPDATE {self.table_name} SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        return self._execute(query, (name, project_id))

    @require_admin
    def delete(self, project_id):
        """프로젝트 삭제"""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        return self._execute(query, (project_id,))