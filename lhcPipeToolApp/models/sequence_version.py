"""버전 모델"""
from .base_model import BaseModel
from ..utils.logger import setup_logger
from ..database.table_manager import TableManager

class SequenceVersion(BaseModel):
    def __init__(self, connector):
        super().__init__(connector)
        self.logger = setup_logger(__name__)

    def create(self, version_name, sequence_id, version_number, worker_id, file_path=None, 
              preview_path=None, render_path=None, comment=None, status='pending'):
        """새 시퀀스 버전 생성"""
        self.logger.info(f"""시퀀스 버전 생성 시도:
            name: {version_name}
            sequence_id: {sequence_id}
            version_number: {version_number}
            worker_id: {worker_id}
            file_path: {file_path}
            preview_path: {preview_path}
            render_path: {render_path}
            comment: {comment}
            status: {status}
        """)

        # 이전 버전들의 is_latest를 False로 설정
        self._update_previous_versions(sequence_id)
        
        query = """
            INSERT INTO SEQUENCE_VERSIONS 
            (NAME, SEQUENCE_ID, VERSION_NUMBER, WORKER_ID, STATUS, FILE_PATH, 
             PREVIEW_PATH, RENDER_PATH, COMMENT, IS_LATEST) 
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """
        
        try:
            result = self._execute(query, (
                version_name,
                sequence_id,
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
                self.logger.info("시퀀스 버전 생성 성공")
            else:
                self.logger.error("시퀀스 버전 생성 실패")
            return result
        except Exception as e:
            self.logger.error(f"시퀀스 버전 생성 중 오류 발생: {str(e)}", exc_info=True)
            return False

    def _update_previous_versions(self, sequence_id):
        """이전 시퀀스 버전들의 is_latest 상태 업데이트"""
        query = """
            UPDATE sequence_versions 
            SET is_latest = FALSE 
            WHERE sequence_id = ?
        """
        return self._execute(query, (sequence_id,))

    def get_latest_version(self, sequence_id):
        """시퀀스의 최신 버전 조회"""
        query = """
            SELECT v.*, w.name as worker_name 
            FROM sequence_versions v
            JOIN workers w ON v.worker_id = w.id
            WHERE v.sequence_id = ? AND v.is_latest = TRUE
        """
        return self._fetch_one(query, (sequence_id,))

    def get_all_versions(self, sequence_id):
        """샷의 모든 버전 조회"""
        query = """
            SELECT v.*, w.name as worker_name 
            FROM versions v
            JOIN workers w ON v.worker_id = w.id
            WHERE v.sequence_id = ?
            ORDER BY v.version_number DESC
        """
        return self._fetch_all(query, (sequence_id,))

    def update_status(self, version_id, status):
        """버전 상태 업데이트"""
        query = """
            UPDATE versions 
            SET status = ? 
            WHERE id = ?
        """
        return self._execute(query, (status, version_id))
    
    def get_by_id(self, version_id):
        """ID로 버전 조회"""
        query = "SELECT * FROM versions WHERE id = ?"
        return self._fetch_one(query, (version_id,))

    def delete(self, version_id):
        """버전 삭제"""
        try:
            query = "DELETE FROM versions WHERE id = ?"
            return self._execute(query, (version_id,))
        except Exception as e:
            self.logger.error(f"버전 삭제 중 오류 발생: {str(e)}", exc_info=True)
            return False
