"""작업자 모델"""
from .base_model import BaseModel

class Worker(BaseModel):
    def create(self, name, email=None, department=None):
        """작업자 생성"""
        query = """
            INSERT INTO workers (name, department)
            VALUES (?, ?)
        """
        return self._execute(query, (name, department))

    def get_all(self):
        """모든 작업자 조회"""
        query = "SELECT * FROM workers ORDER BY name"
        return self._fetch_all(query)

    def get_by_id(self, worker_id):
        """ID로 작업자 조회"""
        query = "SELECT * FROM workers WHERE id = ?"
        return self._fetch_one(query, (worker_id,))

    def get_by_name(self, name):
        """이름으로 작업자 조회"""
        query = "SELECT * FROM workers WHERE name = ?"
        return self._fetch_one(query, (name,))

    def update(self, worker_id, name=None, email=None, department=None):
        """작업자 정보 수정"""
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if email:
            updates.append("email = ?")
            params.append(email)
        if department:
            updates.append("department = ?")
            params.append(department)
            
        if not updates:
            return False
            
        params.append(worker_id)
        query = f"""
            UPDATE workers 
            SET {', '.join(updates)} 
            WHERE id = ?
        """
        return self._execute(query, tuple(params))