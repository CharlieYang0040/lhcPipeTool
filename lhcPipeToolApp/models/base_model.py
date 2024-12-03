"""기본 모델 클래스"""
from ..utils.logger import setup_logger

class BaseModel:
    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.logger = setup_logger(__name__)
        
    def _execute(self, query, params=None):
        """모델 레벨의 쿼리 실행"""
        try:
            # 쿼리 로깅
            formatted_query = query
            if params:
                try:
                    formatted_query = query % params
                except:
                    formatted_query = f"Query: {query}, Params: {params}"
            self.logger.info(f"실행할 쿼리:\n{formatted_query}")

            # DBConnector를 통한 쿼리 실행
            cursor = self.db_connector.execute(query, params)

            # SELECT 문이 아닌 경우에만 커밋
            if not query.strip().upper().startswith('SELECT'):
                self.db_connector.commit()
                self.logger.info("쿼리 실행 성공")

            return cursor
        except Exception as e:
            self.logger.error(f"쿼리 실행 실패: {str(e)}", exc_info=True)
            self.db_connector.rollback()
            raise

    def _fetch_one(self, query, params=None):
        """단일 결과 조회"""
        try:
            result = self.db_connector.fetch_one(query, params)
            self.logger.info("쿼리 실행 성공")
            return result
        except Exception as e:
            self.logger.error(f"데이터 조회 오류: {e}")
            self.db_connector.rollback()
            return None

    def _fetch_all(self, query, params=None):
        """모든 결과 조회"""
        try:
            results = self.db_connector.fetch_all(query, params)
            self.logger.info("쿼리 실행 성공")
            return results
        except Exception as e:
            self.logger.error(f"데이터 조회 오류: {e}")
            self.db_connector.rollback()
            return []

    def get_last_insert_id(self):
        """마지막으로 삽입된 ID 반환"""
        try:
            result = self.db_connector.fetch_one("SELECT LAST_INSERT_ID()")
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"ID 조회 오류: {e}")
            return None