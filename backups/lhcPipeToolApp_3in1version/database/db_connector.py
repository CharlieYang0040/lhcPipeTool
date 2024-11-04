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
            self.logger.info("트랜잭션 커밋 완료")

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
            self.connection.close()
            self.connection = None
            self.logger.info("데이터베이스 연결 종료")