"""데이터베이스 모델"""
from .base_model import BaseModel

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
        # 쿼리 실행 및 결과 가져오기
        tables = self._fetch_all(query)
        
        # 결과가 비어 있지 않은지 확인
        if not tables:
            return []
        
        # 컬럼명 확인
        first_table = tables[0]
        column_names = first_table.keys()
        self.logger.debug(f"테이블 컬럼명: {column_names}")
        
        # 컬럼명에 따른 키 설정
        if 'RDB$RELATION_NAME' in first_table:
            column_key = 'RDB$RELATION_NAME'
        elif 'rdb$relation_name' in first_table:
            column_key = 'rdb$relation_name'
        else:
            raise KeyError("컬럼명을 찾을 수 없습니다.")
        
        # 테이블 이름 목록 반환
        return [table[column_key].strip() for table in tables]
    
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
        # 1. 먼저 updated_at 컬럼 존재 여부 확인
        check_column_query = """
            SELECT 1
            FROM RDB$RELATION_FIELDS
            WHERE RDB$RELATION_NAME = ?
            AND RDB$FIELD_NAME = 'UPDATED_AT'
        """
        has_updated = self._fetch_one(check_column_query, (table_name.upper(),))

        # 2. 컬럼 존재 여부에 따라 다른 쿼리 실행
        if has_updated:
            query = """
                SELECT 
                    COUNT(*) as total_rows,
                    MAX(created_at) as last_created,
                    MAX(updated_at) as last_updated
                FROM {}
            """.format(table_name)
        else:
            query = """
                SELECT 
                    COUNT(*) as total_rows,
                    MAX(created_at) as last_created,
                    NULL as last_updated
                FROM {}
            """.format(table_name)

        result = self._fetch_one(query)
        
        if result:
            return {
                'total_rows': result['total_rows'] if result['total_rows'] is not None else 0,
                'last_created': result['last_created'],
                'last_updated': result['last_updated'] if has_updated else None
            }
        return {
            'total_rows': 0,
            'last_created': None,
            'last_updated': None
        }

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

    def drop_table(self, table_name):
        """테이블 삭제"""
        query = f"DROP TABLE {table_name}"
        return self._execute(query)