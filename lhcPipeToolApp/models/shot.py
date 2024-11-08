"""샷 모델"""
from .base_model import BaseModel
from ..database.table_manager import TableManager

class Shot(BaseModel):
    def create(self, name, sequence_id, description=None, status="pending"):
        """샷 생성
        Args:
            name (str): 샷 이름
            sequence_id (int): 시퀀스 ID
            description (str, optional): 샷 설명
            status (str, optional): 샷 상태 (기본값: "pending")
        """
        query = """
            INSERT INTO shots (name, sequence_id, description, status) 
            VALUES (?, ?, ?, ?)
        """
        # 테이블 구조 조회
        table_manager = TableManager(self.connector)
        table_structure = table_manager.get_table_structure("SHOTS")
        self.logger.info(f"테이블 구조: {table_structure}")
        
        return self._execute(query, (str(name), sequence_id, description, status))

    def get_by_sequence(self, sequence_id):
        """시퀀스별 샷 조회"""
        query = """
            SELECT * FROM shots 
            WHERE sequence_id = ? 
            ORDER BY name
        """
        return self._fetch_all(query, (sequence_id,))

    def update_status(self, shot_id, status):
        """샷 상태 업데이트"""
        query = """
            UPDATE shots 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """
        return self._execute(query, (status, shot_id))

    def get_by_id(self, shot_id):
        """ID로 샷 조회"""
        query = "SELECT * FROM shots WHERE id = ?"
        return self._fetch_one(query, (shot_id,))

    def delete(self, shot_id):
        """샷 삭제"""
        query = "DELETE FROM shots WHERE id = ?"
        return self._execute(query, (shot_id,))

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
        
        query = f"""
            UPDATE shots 
            SET {', '.join(updates)} 
            WHERE id = ?
        """
        return self._execute(query, tuple(params))