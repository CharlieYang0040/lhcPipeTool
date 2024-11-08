"""기본 모델 클래스"""
from ..utils.logger import setup_logger

class BaseModel:
    def __init__(self, connector):
        self.connector = connector
        self.cursor = connector.connection.cursor()
        self.logger = setup_logger(__name__)

    def _execute(self, query, params=None):
        """쿼리 실행"""
        try:
            cursor = self.connector.cursor()
            # 쿼리와 파라미터 로깅 전에 실제 값 확인
            formatted_query = query
            if params:
                try:
                    formatted_query = query % params
                except:
                    formatted_query = f"Query: {query}, Params: {params}"
            
            self.logger.info(f"실행할 쿼리:\n{formatted_query}")
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            self.connector.commit()
            self.logger.info("쿼리 실행 성공")
            return True
        except Exception as e:
            self.logger.error(f"쿼리 실행 실패: {str(e)}", exc_info=True)
            self.connector.rollback()
            return False

    def _fetch_one(self, query, params=None):
        """단일 결과 조회"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"데이터 조회 오류: {e}")
            return None

    def _fetch_all(self, query, params=None):
        """모든 결과 조회"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"데이터 조회 오류: {e}")
            return []

    def get_last_insert_id(self):
        """마지막으로 삽입된 ID 반환"""
        try:
            self.cursor.execute("SELECT LAST_INSERT_ID()")
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"ID 조회 오류: {e}")
            return None