"""데이터베이스 마이그레이션"""
from ..utils.logger import setup_logger

class DatabaseMigration:
    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.logger = setup_logger(__name__)

    def add_column_if_not_exists(self, table_name, column_name, column_definition):
        """컬럼이 존재하지 않을 경우에만 추가"""
        try:
            # 먼저 컬럼 존재 여부 확인
            check_query = """
                SELECT 1 FROM RDB$RELATION_FIELDS 
                WHERE RDB$RELATION_NAME = ? 
                AND RDB$FIELD_NAME = ?
            """
            result = self.db_connector.fetch_one(check_query, (table_name, column_name))
            
            if not result:
                # 컬럼이 존재하지 않는 경우에만 추가
                alter_query = f'ALTER TABLE {table_name} ADD "{column_name}" {column_definition}'
                self.logger.debug(f"실행할 SQL: {alter_query}")
                self.db_connector.execute(alter_query)
                self.logger.info(f"{column_name} 컬럼 추가됨")
                return True
            else:
                self.logger.info(f"{column_name} 컬럼이 이미 존재함")
                return True
                
        except Exception as e:
            self.logger.error(f"컬럼 추가 중 오류 발생: {e}")
            return False

    def migrate_workers_table(self):
        """workers 테이블 마이그레이션"""
        migrations = [
            ("ROLE", "VARCHAR(20) DEFAULT 'user' NOT NULL"),
            ("PASSWORD", "VARCHAR(255)"),
            ("UPDATED_AT", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        success = True
        for column_name, definition in migrations:
            if not self.add_column_if_not_exists('WORKERS', column_name, definition):
                self.logger.error(f"{column_name} 컬럼 추가 실패")
                success = False
                break
        
        if success:
            try:
                # 기존 레코드에 기본값 설정
                default_password_hash = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
                update_sql = """
                    UPDATE WORKERS 
                    SET PASSWORD = ?, ROLE = 'user'
                    WHERE PASSWORD IS NULL
                """
                self.db_connector.execute(update_sql, (default_password_hash,))
                self.logger.info("기존 사용자 데이터 업데이트 완료")
            except Exception as e:
                self.logger.error(f"기존 데이터 업데이트 중 오류 발생: {e}")

def run_migrations(db_connector):
    """모든 마이그레이션 실행"""
    migration = DatabaseMigration(db_connector)
    migration.migrate_workers_table()