"""새로고침 모델"""
from .base_model import BaseModel
from pathlib import Path

class Refresh(BaseModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.table_name = 'refresh_logs'
        
    def get_project_root(self):
        """프로젝트 루트 경로 가져오기"""
        query = "SELECT setting_value FROM settings WHERE setting_key = 'project_root'"
        result = self._fetch_one(query)
        
        if not result:
            self.logger.warning("프로젝트 루트 경로가 설정되지 않음")
            return None
            
        root_path = Path(result['setting_value'])
        if not root_path.exists():
            self.logger.error(f"프로젝트 루트 경로가 존재하지 않음: {root_path}")
            return None
            
        return root_path
        
    def log_refresh(self, worker_id, status, message=None, root_path=None):
        """새로고침 작업 로그 기록"""
        query = """
            INSERT INTO refresh_logs 
            (worker_id, status, message, root_path, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            RETURNING id
        """
        try:
            result = self._fetch_one(
                query, 
                (worker_id, status, message, str(root_path) if root_path else None)
            )
            return result['id'] if result and 'id' in result else None
        except Exception as e:
            self.logger.error(f"새로고침 로그 생성 중 오류 발생: {str(e)}", exc_info=True)
            raise

    def get_last_refresh(self):
        """마지막 새로고침 기록 조회"""
        query = """
            SELECT rl.*, w.name as worker_name
            FROM refresh_logs rl
            LEFT JOIN workers w ON w.id = rl.worker_id
            ORDER BY rl.created_at DESC
            LIMIT 1
        """
        return self._fetch_one(query)

    def get_refresh_history(self, limit=100):
        """새로고침 히스토리 조회"""
        query = """
            SELECT rl.*, w.name as worker_name
            FROM refresh_logs rl
            LEFT JOIN workers w ON w.id = rl.worker_id
            ORDER BY rl.created_at DESC
            LIMIT ?
        """
        return self._fetch_all(query, (limit,))