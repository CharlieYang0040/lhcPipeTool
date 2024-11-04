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
            'workers'
        ]
        
        # 기본 테이블 생성
        for table_name in table_order:
            if not self.create_table(table_name):
                self.logger.error(f"테이블 생성 실패: {table_name}")
                return False
        
        # versions 테이블 별도 생성 (시퀀스 포함)
        if not self.create_versions_table():
            self.logger.error("versions 테이블 생성 실패")
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
    
    def add_column(self, table_name, column_name, column_type):
        """테이블에 새 컬럼 추가"""
        try:
            cursor = self.connector.cursor()
            # 컬럼 존재 여부 확인
            cursor.execute(f"""
                SELECT 1 FROM RDB$RELATION_FIELDS 
                WHERE RDB$RELATION_NAME = '{table_name.upper()}' 
                AND RDB$FIELD_NAME = '{column_name.upper()}'
            """)
            
            if not cursor.fetchone():
                # 컬럼이 없으면 추가
                cursor.execute(f"ALTER TABLE {table_name} ADD {column_name} {column_type}")
                self.connector.commit()
                self.logger.info(f"컬럼 추가 성공: {table_name}.{column_name}")
                return True
            else:
                self.logger.info(f"컬럼이 이미 존재함: {table_name}.{column_name}")
                return True
        except Exception as e:
            self.logger.error(f"컬럼 추가 실패: {str(e)}")
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
    
    def add_path_columns(self):
        """경로 관련 컬럼 추가"""
        try:
            cursor = self.connector.cursor()
            
            # projects 테이블에 path 컬럼 추가
            cursor.execute("""
                SELECT 1 FROM RDB$RELATION_FIELDS 
                WHERE RDB$RELATION_NAME = 'PROJECTS' 
                AND RDB$FIELD_NAME = 'PATH'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE projects 
                    ADD path VARCHAR(500)
                """)
                self.logger.info("projects 테이블에 path 컬럼 추가됨")
            else:
                self.logger.info("projects 테이블에 이미 path 컬럼이 존재함")
                
            # versions 테이블에 path 컬럼 추가
            cursor.execute("""
                SELECT 1 FROM RDB$RELATION_FIELDS 
                WHERE RDB$RELATION_NAME = 'VERSIONS' 
                AND RDB$FIELD_NAME = 'PATH'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE versions 
                    ADD path VARCHAR(500)
                """)
                self.logger.info("versions 테이블에 path 컬럼 추가됨")
            else:
                self.logger.info("versions 테이블에 이미 path 컬럼이 존재함")
            
            self.connector.commit()
            return True
        except Exception as e:
            self.logger.error(f"경로 컬럼 추가 실패: {str(e)}")
            return False
    
    def add_description_columns(self):
        """설명 컬럼 추가"""
        try:
            cursor = self.connector.cursor()
            
            # projects 테이블에 description 컬럼 추가
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN description BLOB SUB_TYPE TEXT
            """)
            
            self.connector.commit()
            self.logger.info("설명 컬럼 추가 완료")
            return True
        except Exception as e:
            self.logger.error(f"설명 컬럼 추가 실패: {str(e)}")
            return False
    
    def recreate_versions_table(self):
        """versions 테이블 재생성"""
        try:
            cursor = self.connector.cursor()
            
            # 기존 테이블 삭제 시도 (예외 처리로 테이블이 없는 경우도 처리)
            try:
                cursor.execute("""
                    EXECUTE BLOCK AS BEGIN
                        IF (EXISTS (SELECT 1 FROM rdb$relations WHERE rdb$relation_name = 'VERSIONS')) THEN
                            EXECUTE STATEMENT 'DROP TABLE versions';
                    END
                """)
            except Exception as e:
                self.logger.info("기존 versions 테이블 삭제 시도 중 오류 (무시 가능): %s", str(e))
            
            # 새 테이블 생성
            cursor.execute("""
                CREATE TABLE versions (
                    id INTEGER NOT NULL PRIMARY KEY,
                    version_type VARCHAR(20) NOT NULL,
                    version_number INTEGER NOT NULL,
                    worker_id INTEGER,
                    project_id INTEGER,
                    sequence_id INTEGER,
                    shot_id INTEGER,
                    file_path VARCHAR(500),
                    preview_path VARCHAR(500),
                    render_path VARCHAR(500),
                    comment BLOB SUB_TYPE TEXT,
                    is_latest BOOLEAN DEFAULT TRUE,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (worker_id) REFERENCES workers(id),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE,
                    FOREIGN KEY (shot_id) REFERENCES shots(id) ON DELETE CASCADE
                )
            """)
            
            self.connector.commit()
            self.logger.info("versions 테이블 재생성 완료")
            return True
        except Exception as e:
            self.logger.error(f"versions 테이블 재생성 실패: {str(e)}")
            self.connector.rollback()
            return False

    def create_versions_table(self):
        """versions 테이블 생성"""
        try:
            cursor = self.connector.cursor()
            
            # 시퀀스 생성 시도
            try:
                cursor.execute("DROP SEQUENCE versions_id_seq")
            except:
                pass  # 시퀀스가 없으면 무시
                
            cursor.execute("""
                CREATE SEQUENCE versions_id_seq
            """)
            
            # 테이블 생성
            cursor.execute("""
                CREATE TABLE versions (
                    id INTEGER NOT NULL PRIMARY KEY,
                    version_type VARCHAR(20) NOT NULL,
                    version_number INTEGER NOT NULL,
                    worker_id INTEGER,
                    project_id INTEGER,
                    sequence_id INTEGER,
                    shot_id INTEGER,
                    file_path VARCHAR(500),
                    preview_path VARCHAR(500),
                    render_path VARCHAR(500),
                    comment BLOB SUB_TYPE TEXT,
                    is_latest BOOLEAN DEFAULT TRUE,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (worker_id) REFERENCES workers(id),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE,
                    FOREIGN KEY (shot_id) REFERENCES shots(id) ON DELETE CASCADE
                )
            """)
            
            self.connector.commit()
            self.logger.info("versions 테이블 생성 완료")
            return True
        except Exception as e:
            self.logger.error(f"versions 테이블 생성 실패: {str(e)}")
            self.connector.rollback()
            return False

    def _drop_table_if_exists(self, table_name):
        """테이블이 존재하면 삭제"""
        try:
            cursor = self.connector.cursor()
            cursor.execute(f"""
                SELECT 1 FROM rdb$relations 
                WHERE rdb$relation_name = '{table_name.upper()}'
            """)
            if cursor.fetchone():
                cursor.execute(f"DROP TABLE {table_name}")
                self.logger.info(f"{table_name} 테이블 삭제 완료")
            return True
        except Exception as e:
            self.logger.error(f"테이블 삭제 실패: {str(e)}")
            return False