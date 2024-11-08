"""기본 버전 모델"""
from .base_model import BaseModel
from ..utils.logger import setup_logger

class BaseVersionModel(BaseModel):
    def __init__(self, connector):
        super().__init__(connector)
        self.logger = setup_logger(__name__)
        self.table_name = None  # 하위 클래스에서 정의
        self.item_type = None   # 하위 클래스에서 정의 (shot, sequence, project)

    def create(self, version_name, item_id, version_number, worker_id, file_path=None, 
              preview_path=None, render_path=None, comment=None, status='pending'):
        """새 버전 생성"""
        self.logger.info(f"""{self.item_type} 버전 생성 시도:
            name: {version_name}
            {self.get_foreign_key()}: {item_id}
            version_number: {version_number}
            worker_id: {worker_id}
            file_path: {file_path}
            preview_path: {preview_path}
            render_path: {render_path}
            comment: {comment}
            status: {status}
        """)

        # 이전 버전들의 is_latest를 False로 설정
        self._update_previous_versions(item_id)
        
        query = f"""
            INSERT INTO {self.table_name}
            (NAME, {self.get_foreign_key()}, VERSION_NUMBER, WORKER_ID, STATUS, FILE_PATH, 
             PREVIEW_PATH, RENDER_PATH, COMMENT, IS_LATEST) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            result = self._execute(query, (
                version_name,
                item_id,
                version_number,
                worker_id,
                status,
                file_path,
                preview_path,
                render_path,
                comment,
                True  # is_latest
            ))
            if result:
                self.logger.info(f"{self.item_type} 버전 생성 성공")
            else:
                self.logger.error(f"{self.item_type} 버전 생성 실패")
            return result
        except Exception as e:
            self.logger.error(f"{self.item_type} 버전 생성 중 오류 발생: {str(e)}", exc_info=True)
            return False

    def _update_previous_versions(self, item_id):
        """이전 버전들의 is_latest 상태 업데이트"""
        query = f"""
            UPDATE {self.table_name}
            SET is_latest = FALSE 
            WHERE {self.get_foreign_key()} = ?
        """
        return self._execute(query, (item_id,))

    def get_latest_version(self, item_id):
        """최신 버전 조회"""
        query = f"""
            SELECT v.*, w.name as worker_name 
            FROM {self.table_name} v
            JOIN workers w ON v.worker_id = w.id
            WHERE v.{self.get_foreign_key()} = ? AND v.is_latest = TRUE
        """
        return self._fetch_one(query, (item_id,))

    def get_all_versions(self, item_id):
        """모든 버전 조회"""
        query = f"""
            SELECT v.*, w.name as worker_name 
            FROM {self.table_name} v
            JOIN workers w ON v.worker_id = w.id
            WHERE v.{self.get_foreign_key()} = ?
            ORDER BY v.version_number DESC
        """
        return self._fetch_all(query, (item_id,))

    def update_status(self, version_id, status):
        """버전 상태 업데이트"""
        query = f"""
            UPDATE {self.table_name}
            SET status = ? 
            WHERE id = ?
        """
        return self._execute(query, (status, version_id))
    
    def get_by_id(self, version_id):
        """ID로 버전 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        return self._fetch_one(query, (version_id,))

    def delete(self, version_id):
        """버전 삭제"""
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = ?"
            return self._execute(query, (version_id,))
        except Exception as e:
            self.logger.error(f"버전 삭제 중 오류 발생: {str(e)}", exc_info=True)
            return False

    def get_foreign_key(self):
        """외래키 필드명 반환"""
        return f"{self.item_type}_id"