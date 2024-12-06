"""작업자 모델"""
from .base_model import BaseModel
import hashlib

class Worker(BaseModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.table_name = "workers"
        
    def verify_credentials(self, name, hashed_password):
        """사용자 인증"""
        query = """
            SELECT * FROM workers 
            WHERE name = ? AND password = ?
        """
        result = self._fetch_one(query, (name, hashed_password))
        return result is not None
        
    def is_admin(self, worker_name):
        """작업자가 관리자 인지 확인"""
        worker = self.get_by_name(worker_name)
        if worker and worker.get('role') == 'admin':
            return True
        return False
        
    def create(self, name, password, department=None, role='user'):
        """새 작업자 생성 (비밀번호 해시화 포함)"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = f"""
            INSERT INTO {self.table_name} (name, password, department, role)
            VALUES (?, ?, ?, ?)
            RETURNING ID
        """
        try:
            result = self.db_connector.fetch_one(query, (name, hashed_password, department, role))
            return result['id'] if result and 'id' in result else None
        except Exception as e:
            self.logger.error(f"작업자 생성 중 오류 발생: {str(e)}", exc_info=True)
            return None

    def get_all(self):
        """모든 작업자 조회"""
        query = f"SELECT * FROM {self.table_name} ORDER BY name"
        return self._fetch_all(query)

    def get_by_id(self, worker_id):
        """ID로 작업자 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        return self._fetch_one(query, (worker_id,))

    def get_by_name(self, name):
        """이름으로 작업자 조회"""
        try:
            # 입력된 이름이 한글일 경우를 대비해 적절한 인코딩 처리
            if isinstance(name, str):
                name = name.encode('utf-8').decode('utf-8')
            
            query = f"SELECT * FROM {self.table_name} WHERE name = ?"
            return self._fetch_one(query, (name,))
        except Exception as e:
            self.logger.error(f"작업자 조회 중 오류 발생: {str(e)}")
            return None

    def update(self, worker_id, name=None, department=None):
        """작업자 정보 수정"""
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if department:
            updates.append("department = ?")
            params.append(department)
            
        if not updates:
            return False
            
        params.append(worker_id)
        query = f"""
            UPDATE {self.table_name} 
            SET {', '.join(updates)} 
            WHERE id = ?
        """
        return self._execute(query, tuple(params))
    
    def delete(self, worker_id):
        """작업자 삭제"""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        return self._execute(query, (worker_id,))

    def reset_password(self, worker_id, new_password):
        """작업자 비밀번호 초기화"""
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        query = f"UPDATE {self.table_name} SET password = ? WHERE id = ?"
        return self._execute(query, (hashed_password, worker_id))
