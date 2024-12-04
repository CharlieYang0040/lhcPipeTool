"""데이터베이스 모델"""
from .base_model import BaseModel
from pathlib import Path

class Database(BaseModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        
    def get_all_tables(self):
        """모든 테이블 목록 조회"""
        query = """
            SELECT RDB$RELATION_NAME 
            FROM RDB$RELATIONS 
            WHERE RDB$SYSTEM_FLAG = 0 AND RDB$VIEW_SOURCE IS NULL
            ORDER BY RDB$RELATION_NAME
        """
        return [table[0].strip() for table in self._fetch_all(query)]

    def get_table_columns(self, table_name):
        """테이블의 컬럼 정보 조회"""
        query = """
            SELECT 
                RF.RDB$FIELD_NAME as COLUMN_NAME,
                F.RDB$FIELD_TYPE as DATA_TYPE,
                F.RDB$FIELD_LENGTH as FIELD_LENGTH,
                RF.RDB$NULL_FLAG as NOT_NULL,
                RF.RDB$DEFAULT_SOURCE as DEFAULT_VALUE
            FROM RDB$RELATION_FIELDS RF
            JOIN RDB$FIELDS F ON RF.RDB$FIELD_SOURCE = F.RDB$FIELD_NAME
            WHERE RF.RDB$RELATION_NAME = ?
            ORDER BY RF.RDB$FIELD_POSITION
        """
        return self._fetch_all(query, (table_name,))

    def get_table_data(self, table_name):
        """테이블 데이터 조회"""
        query = f"SELECT * FROM {table_name}"
        return self._fetch_all(query)

    def get_table_statistics(self, table_name):
        """테이블 통계 정보 조회"""
        query = """
            SELECT 
                COUNT(*) as row_count,
                MAX(created_at) as last_created,
                MAX(updated_at) as last_updated
            FROM {}
        """.format(table_name)
        return self._fetch_one(query)

    def get_foreign_keys(self, table_name):
        """테이블의 외래 키 정보 조회"""
        query = """
            SELECT 
                RC.RDB$CONSTRAINT_NAME as constraint_name,
                REFC.RDB$RELATION_NAME as referenced_table,
                I2.RDB$FIELD_NAME as referenced_field
            FROM RDB$RELATION_CONSTRAINTS RC
            JOIN RDB$REF_CONSTRAINTS REFC ON RC.RDB$CONSTRAINT_NAME = REFC.RDB$CONSTRAINT_NAME
            JOIN RDB$INDEX_SEGMENTS I2 ON REFC.RDB$CONST_NAME_UQ = I2.RDB$INDEX_NAME
            WHERE RC.RDB$RELATION_NAME = ?
            AND RC.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'
        """
        return self._fetch_all(query, (table_name,))

    def execute_custom_query(self, query, params=None):
        """사용자 정의 쿼리 실행"""
        try:
            return self._fetch_all(query, params)
        except Exception as e:
            self.logger.error(f"사용자 정의 쿼리 실행 실패: {str(e)}")
            raise

    def backup_database(self, backup_path):
        """데이터베이스 백업"""
        try:
            self.db_connector.backup(str(backup_path))
            return True
        except Exception as e:
            self.logger.error(f"데이터베이스 백업 실패: {str(e)}")
            raise
