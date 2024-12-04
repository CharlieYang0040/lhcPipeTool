"""샷 모델"""
from .base_model import BaseModel
from ..utils.decorators import require_admin

class Shot(BaseModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.require_admin = require_admin(db_connector)
        self.table_name = 'shots'
        self.item_type = 'shot'

    def get_all(self):
        """모든 샷 조회"""
        query = f"SELECT * FROM {self.table_name} ORDER BY name"
        return self._fetch_all(query)

    def get_by_id(self, shot_id):
        """ID로 샷 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        return self._fetch_one(query, (shot_id,))

    def get_by_name(self, name):
        """이름으로 샷 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE name = ?"
        return self._fetch_one(query, (name,))

    def get_by_sequence(self, sequence_id):
        """시퀀스별 샷 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE sequence_id = ? ORDER BY name"
        return self._fetch_all(query, (sequence_id,))
    
    @require_admin
    def create(self, name, sequence_id, status="pending", description=None):
        """샷 생성"""
        query = f"""
            INSERT INTO {self.table_name} (name, sequence_id, status, description, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            RETURNING ID
        """
        try:
            result = self.db_connector.fetch_one(query, (name, sequence_id, status, description))
            self.logger.debug(f"삽입된 샷 ID: {result['id'] if result and 'id' in result else '없음'}")
            return result['id'] if result and 'id' in result else None
        except Exception as e:
            self.logger.error(f"샷 생성 중 오류 발생: {str(e)}", exc_info=True)
            raise

    def update_status(self, shot_id, status):
        """샷 상태 업데이트"""
        query = f"UPDATE {self.table_name} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        return self._execute(query, (status, shot_id))

    @require_admin
    def delete(self, shot_id):
        """샷 삭제"""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        return self._execute(query, (shot_id,))

    @require_admin
    def update(self, shot_id, name=None, description=None, status=None):
        """샷 정보 수정"""
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if description:
            updates.append("description = ?")
            params.append(description)
        if status:
            updates.append("status = ?")
            params.append(status)
            
        if not updates:
            return False
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(shot_id)
        
        query = f"UPDATE {self.table_name} SET {', '.join(updates)} WHERE id = ?"
        return self._execute(query, tuple(params))