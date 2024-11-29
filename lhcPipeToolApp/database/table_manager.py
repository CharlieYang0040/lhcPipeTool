"""테이블 생성 및 관리"""
from ..utils.logger import setup_logger
from ..schemas.table_schemas import TABLES

class TableManager:
    def __init__(self, connector):
        self.connector = connector
        self.logger = setup_logger(__name__)
    
    def create_table(self, table_name, columns=None):
        """단일 테이블 생성"""
        if table_name not in TABLES:
            self.logger.error(f"Unknown table: {table_name}")
            raise ValueError(f"Unknown table: {table_name}")
            
        try:
            cursor = self.connector.cursor()
            sql = TABLES[table_name]
            self.logger.debug(f"실행할 SQL:\n{sql}")
            
            cursor.execute(sql)
            self.connector.commit()
            self.logger.info(f"테이블 생성 성공: {table_name}")
            return True
        except Exception as e:
            if 'already exists' not in str(e):
                self.logger.error(
                    f"테이블 생성 오류: {str(e)}\n"
                    f"테이블: {table_name}\n"
                    f"SQL: {TABLES[table_name]}", 
                    exc_info=True
                )
                return False
            self.logger.info(f"테이블이 이미 존재함: {table_name}")
            return True
    
    def create_all_tables(self):
        """모든 테이블 생성"""
        self.logger.info("모든 테이블 생성 시작")
        
        # 테이블 생성 순서 정의 (외래 키 참조를 고려)
        table_order = [
            'projects',
            'sequences',
            'shots',
            'workers',
            'project_versions',
            'sequence_versions',
            'versions'
        ]
        
        for table_name in table_order:
            if not self.create_table(table_name):
                self.logger.error(f"테이블 생성 실패: {table_name}")
                return False
                
        self.logger.info("모든 테이블 생성 완료")
        return True
    
    def recreate_table(self, table_name):
        """테이블 재생성"""
        try:
            cursor = self.connector.cursor()
            self.logger.info(f"테이블 삭제 시도: {table_name}")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.logger.info(f"테이블 삭제 완료: {table_name}")
            
            self.logger.info(f"테이블 생성 시도: {table_name}")
            self.logger.info(f"실행할 SQL: {TABLES[table_name]}")
            cursor.execute(TABLES[table_name])
            self.connector.commit()
            self.logger.info(f"테이블 생성 완료: {table_name}")
            return True
        except Exception as e:
            self.logger.error(f"테이블 재생성 실패: {str(e)}", exc_info=True)
            return False
        
    def initialize_settings(self):
        """기본 설정값 초기화"""
        try:
            cursor = self.connector.cursor()
            # 먼저 설정이 이미 존재하는지 확인
            cursor.execute("""
                SELECT 1 FROM settings 
                WHERE setting_key = 'render_root'
            """)
            
            if not cursor.fetchone():
                # 설정이 없을 때만 삽입
                cursor.execute("""
                    INSERT INTO settings (setting_key, setting_value, description)
                    VALUES ('render_root', 'D:/WORKDATA/lhcPipeTool/TestSequence', '렌더 파일 저장 경로')
                """)
                self.connector.commit()
                self.logger.info("기본 설정값 초기화 완료")
            else:
                self.logger.info("설정값이 이미 존재함")
            return True
        except Exception as e:
            self.logger.error(f"설정 초기화 실패: {str(e)}")
            return False

    def get_table_structure(self, table_name):
        """테이블 구조 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("""
                SELECT RDB$FIELD_NAME 
                FROM RDB$RELATION_FIELDS 
                WHERE RDB$RELATION_NAME = ?
                ORDER BY RDB$FIELD_POSITION
            """, (table_name.upper(),))
            
            # 컬럼명에서 공백 제거하고 리스트로 변환
            columns = [col[0].strip() for col in cursor.fetchall()]
            
            # 로그 출력을 위한 포맷팅
            max_length = max(len(col) for col in columns)
            formatted_columns = [f"{col:<{max_length}}" for col in columns]
            columns_per_line = 3  # 한 줄에 표시할 컬럼 수
            
            # 컬럼을 그룹으로 나누어 출력
            column_groups = [formatted_columns[i:i + columns_per_line] 
                           for i in range(0, len(formatted_columns), columns_per_line)]
            
            for group in column_groups:
                self.logger.info("    " + " | ".join(group))
                
            return columns
            
        except Exception as e:
            self.logger.error(f"테이블 구조 조회 실패: {str(e)}")
            return None
        
    def check_all_table_exists(self):
        """모든 테이블 존재 여부 확인"""
        self.logger.info("모든 테이블 존재 여부 확인 시작")
        TABLES = [
            'projects',
            'sequences',
            'shots',
            'workers',
            'projects_versions',
            'sequences_versions',
            'versions'
        ]
        
        for table_name in TABLES:
            cursor = self.connector.cursor()
            cursor.execute(f"""
                SELECT 1 FROM RDB$RELATIONS 
                WHERE RDB$RELATION_NAME = '{table_name.upper()}'
            """)
            result = cursor.fetchone()
            
            if result:
                self.logger.info(f"테이블 존재함: {table_name}")
            else:
                self.logger.error(f"테이블 존재하지 않음: {table_name}")
                return False
        self.logger.info("모든 테이블 존재 여부 확인 완료")
        return True

        