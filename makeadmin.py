import fdb
import hashlib

# 데이터베이스 연결 설정
con = fdb.connect(
    dsn='PROJECT_MANAGEMENT.FDB',
    user='sysdba',
    password='lion'
)

# 커서 생성
cur = con.cursor()

# 'lion'의 SHA-256 해시 값 생성
password = 'lion'
hashed_password = hashlib.sha256(password.encode()).hexdigest()
print(f"'lion'의 SHA-256 해시 값: {hashed_password}")

try:
    # 업데이트 명령 실행 (이름으로)
    update_query = """
        UPDATE workers
        SET ROLE = 'admin', PASSWORD = ?
        WHERE NAME = ?
    """
    cur.execute(update_query, (hashed_password, 'system'))
    
    # 변경 사항 커밋
    con.commit()
    print("작업자 역할이 성공적으로 업데이트되었습니다.")
    
except Exception as e:
    # 오류 발생 시 롤백
    con.rollback()
    print(f"오류 발생: {e}")
    
finally:
    # 커서와 연결 종료
    cur.close()
    con.close()
