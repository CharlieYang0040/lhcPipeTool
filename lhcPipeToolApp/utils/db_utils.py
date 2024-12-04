"""데이터베이스 유틸리티 함수"""
from ..utils.logger import setup_logger

def check_table_schema(db_connector, table_name):
    """테이블 스키마 확인"""
    logger = setup_logger(__name__)
    try:
        cursor = db_connector.cursor()
        cursor.execute(f"""
            SELECT r.RDB$FIELD_NAME, f.RDB$FIELD_TYPE, f.RDB$FIELD_LENGTH, 
                   r.RDB$NULL_FLAG, r.RDB$DEFAULT_SOURCE
            FROM RDB$RELATION_FIELDS r
            LEFT JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
            WHERE r.RDB$RELATION_NAME = '{table_name.upper()}'
            ORDER BY r.RDB$FIELD_POSITION
        """)
        columns = cursor.fetchall()
        logger.info(f"\n테이블 {table_name} 스키마:")
        for col in columns:
            logger.info(f"컬럼: {col[0].strip()}, 타입: {col[1]}, "
                       f"길이: {col[2]}, Nullable: {col[3] is None}, "
                       f"기본값: {col[4].strip() if col[4] else 'None'}")
        return columns
    except Exception as e:
        logger.error(f"스키마 확인 실패: {str(e)}", exc_info=True)
        return None

def check_table_exists(db_connector, table_name):
    """테이블 존재 여부 확인"""
    logger = setup_logger(__name__)
    try:
        cursor = db_connector.cursor()
        cursor.execute("""
            SELECT 1 FROM RDB$RELATIONS 
            WHERE RDB$RELATION_NAME = ?
        """, (table_name.upper(),))
        exists = cursor.fetchone() is not None
        logger.info(f"테이블 {table_name} 존재 여부: {exists}")
        return exists
    except Exception as e:
        logger.error(f"테이블 존재 여부 확인 실패: {str(e)}", exc_info=True)
        return False

def check_foreign_keys(db_connector, table_name):
    """외래 키 제약조건 확인"""
    logger = setup_logger(__name__)
    try:
        cursor = db_connector.cursor()
        cursor.execute("""
            SELECT rc.RDB$CONSTRAINT_NAME,
                   rc.RDB$RELATION_NAME,
                   rc.RDB$CONSTRAINT_TYPE,
                   i.RDB$FIELD_NAME,
                   refc.RDB$UPDATE_RULE,
                   refc.RDB$DELETE_RULE,
                   refc.RDB$CONST_NAME_UQ
            FROM RDB$RELATION_CONSTRAINTS rc
            JOIN RDB$INDEX_SEGMENTS i ON rc.RDB$INDEX_NAME = i.RDB$INDEX_NAME
            LEFT JOIN RDB$REF_CONSTRAINTS refc ON rc.RDB$CONSTRAINT_NAME = refc.RDB$CONSTRAINT_NAME
            WHERE rc.RDB$RELATION_NAME = ? AND rc.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'
        """, (table_name.upper(),))
        
        constraints = cursor.fetchall()
        logger.info(f"\n테이블 {table_name}의 외래 키 제약조건:")
        for const in constraints:
            logger.info(f"제약조건명: {const[0].strip()}, "
                       f"필드: {const[3].strip()}, "
                       f"참조테이블: {const[6].strip() if const[6] else 'None'}, "
                       f"갱신규칙: {const[4].strip() if const[4] else 'None'}, "
                       f"삭제규칙: {const[5].strip() if const[5] else 'None'}")
        return constraints
    except Exception as e:
        logger.error(f"외래 키 제약조건 확인 실패: {str(e)}", exc_info=True)
        return None

def get_table_total_rows(db_connector, table_name):
    """테이블의 레코드 수 조회"""
    logger = setup_logger(__name__)
    try:
        cursor = db_connector.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        logger.info(f"테이블 {table_name}의 레코드 수: {count}")
        return count
    except Exception as e:
        logger.error(f"레코드 수 조회 실패: {str(e)}", exc_info=True)
        return None

def check_database_connection(db_connector):
    """데이터베이스 연결 상태 확인"""
    logger = setup_logger(__name__)
    try:
        cursor = db_connector.cursor()
        cursor.execute("SELECT CURRENT_TIMESTAMP FROM RDB$DATABASE")
        result = cursor.fetchone()
        logger.info("데이터베이스 연결 상태: 정상")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 상태: 비정상 - {str(e)}", exc_info=True)
        return False
    
# 날짜 형식 변환
def convert_date_format(date):
    """날짜 형식 변환
    Args:
        date: 변환할 날짜 (datetime, int, str)
    Returns:
        str: YYYY-MM-DD HH:MM:SS 형식의 문자열
    """
    try:
        if isinstance(date, int):
            # Unix timestamp를 datetime으로 변환
            from datetime import datetime
            date = datetime.fromtimestamp(date)
        
        if isinstance(date, str):
            # 문자열을 datetime으로 변환
            from datetime import datetime
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            
        # datetime 객체의 경우 microsecond 제거
        if hasattr(date, 'replace'):
            date = date.replace(microsecond=0)
            
        return str(date)
        
    except Exception as e:
        logger = setup_logger(__name__)
        logger.error(f"날짜 변환 실패: {str(e)}", exc_info=True)
        return str(date)  # 변환 실패시 원본 반환