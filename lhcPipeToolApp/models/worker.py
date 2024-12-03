"""작업자 모델"""
from .base_model import BaseModel
import hashlib

class Worker(BaseModel):
    def verify_credentials(self, name, hashed_password):
        """사용자 인증"""
        query = """
            SELECT * FROM workers 
            WHERE name = ? AND password = ?
        """
        result = self._fetch_one(query, (name, hashed_password))
        return result is not None
        
    def is_admin(self, worker_id):
        """작업자가 관리자 인지 확인"""
        worker = self.get_by_id(worker_id)
        if worker and worker.get('role') == 'admin':
            return True
        return False
        
    def create_worker(self, name, password, department=None, role='user'):
        """새 작업자 생성 (비밀번호 해시화 포함)"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = """
            INSERT INTO workers (name, password, department, role)
            VALUES (?, ?, ?, ?)
        """
        return self._execute(query, (name, hashed_password, department, role))

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