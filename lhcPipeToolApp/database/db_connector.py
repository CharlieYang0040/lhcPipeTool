"""데이터베이스 연결 관리"""
import fdb
from ..utils.logger import setup_logger

class DBConnector:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.logger = setup_logger(__name__)
    
    def connect(self):
        """데이터베이스 연결"""
        self.logger.info("데이터베이스 연결 시도")
        try:
            self.connection = fdb.connect(
                dsn=self.config.dsn,
                user=self.config.user,
                password=self.config.password,
                charset='UTF8'
            )
            self.logger.info("데이터베이스 연결 성공")
            return True
        except Exception as e:
            self.logger.error(f"데이터베이스 연결 실패: {str(e)}", exc_info=True)
            return False

    def execute(self, query, params=None):
        """쿼리 실행"""
        cursor = self.cursor()
        try:
            if params:
                # Firebird는 ? 대신 named parameters나 위치 기반 parameters를 사용
                if isinstance(params, (list, tuple)):
                    cursor.execute(query, parameters=params)  # 위치 기반 파라미터
                else:
                    cursor.execute(query, named_parameters=params)  # 이름 기반 파라미터
            else:
                cursor.execute(query)
            
            # SELECT 문인 경우 결과 반환
            if query.strip().upper().startswith('SELECT'):
                return cursor
            # INSERT, UPDATE, DELETE 등의 경우 영향받은 행 수 반환
            else:
                self.commit()
                return cursor.rowcount
        except Exception as e:
            self.rollback()
            self.logger.error(f"쿼리 실행 실패: {str(e)}\n쿼리: {query}\n파라미터: {params}", exc_info=True)
            raise

    def fetch_one(self, query, params=None):
        """단일 결과 조회"""
        cursor = self.execute(query, params)
        try:
            row = cursor.fetchone()
            if row and cursor.description:
                # 컬럼명과 값을 딕셔너리로 반환
                columns = [column[0].lower() for column in cursor.description]
                return dict(zip(columns, row))
            return None
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        """모든 결과 조회"""
        cursor = self.execute(query, params)
        try:
            rows = cursor.fetchall()
            if rows and cursor.description:
                # 컬럼명과 값을 딕셔너리로 반환
                columns = [column[0].lower() for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        finally:
            cursor.close()
    
    def cursor(self):
        """커서 반환"""
        if not self.connection:
            self.logger.warning("데이터베이스 연결이 없습니다. 재연결 시도...")
            if not self.connect():
                raise Exception("데이터베이스 연결 실패")
        return self.connection.cursor()

    def commit(self):
        """트랜잭션 커밋"""
        if self.connection:
            self.connection.commit()
            self.logger.debug("트랜잭션 커밋 완료")

    def rollback(self):
        """트랜잭션 롤백"""
        self.logger.info("트랜잭션 롤백 시도")
        try:
            if self.connection:
                self.connection.rollback()
                self.logger.info("트랜잭션 롤백 성공")
        except Exception as e:
            self.logger.error(f"트랜잭션 롤백 실패: {str(e)}", exc_info=True)

    def close(self):
        """데이터베이스 연결 종료"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                self.logger.info("데이터베이스 연결 종료")
            except Exception as e:
                self.logger.error(f"데이터베이스 연결 종료 실패: {str(e)}", exc_info=True)