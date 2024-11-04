"""데이터베이스 관리 서비스"""
from PySide6.QtWidgets import QMessageBox, QTextEdit

class DatabaseService:
    def __init__(self, db_connector, logger):
        self.db_connector = db_connector
        self.logger = logger

    def show_database_contents(self):
        """데이터베이스 내용 출력"""
        try:
            cursor = self.db_connector.cursor()
            output = []
            
            # 원하는 테이블 순서 정의
            ordered_tables = ['PROJECTS', 'SEQUENCES', 'SHOTS', 'VERSIONS', 'WORKERS', 'SETTINGS']
            
            # 실제 존재하는 테이블 확인
            cursor.execute("""
                SELECT RDB$RELATION_NAME 
                FROM RDB$RELATIONS 
                WHERE RDB$SYSTEM_FLAG = 0
            """)
            existing_tables = {table[0].strip() for table in cursor.fetchall()}
            
            # 존재하는 테이블만 순서대로 처리
            for table in ordered_tables:
                if table in existing_tables:
                    output.append(f"\n=== {table} 테이블 ===")
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    # 컬럼명 조회
                    cursor.execute(f"""
                        SELECT RDB$FIELD_NAME 
                        FROM RDB$RELATION_FIELDS 
                        WHERE RDB$RELATION_NAME = '{table}'
                        ORDER BY RDB$FIELD_POSITION
                    """)
                    columns = [col[0].strip() for col in cursor.fetchall()]
                    
                    output.append("컬럼: " + ", ".join(columns))
                    for row in rows:
                        output.append(str(row))
            
            # 결과 표시
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("데이터베이스 내용")
            msg_box.setIcon(QMessageBox.Information)
            
            # 텍스트 에디터 위젯 생성 및 설정
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setMinimumWidth(600)
            text_edit.setMinimumHeight(400)
            
            # 테이블 내용을 HTML 형식으로 포맷팅
            html_content = "<pre style='font-family: Consolas, monospace;'>"
            for line in output:
                if line.startswith("==="): # 테이블 제목
                    html_content += f"<h3 style='color: blue;'>{line}</h3>"
                elif line.startswith("컬럼:"): # 컬럼 헤더
                    html_content += f"<p style='color: green;'>{line}</p>"
                else: # 데이터 행
                    html_content += f"{line}<br>"
            html_content += "</pre>"
            
            text_edit.setHtml(html_content)
            
            # 메시지 박스에 텍스트 에디터 추가
            msg_box.layout().addWidget(text_edit, 0, 0, 1, msg_box.layout().columnCount())
            msg_box.exec()
            
        except Exception as e:
            self.logger.error(f"데이터베이스 내용 조회 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"데이터베이스 내용 조회 실패: {str(e)}")

    def clear_database(self, parent_widget):
        """데이터베이스 초기화"""
        try:
            reply = QMessageBox.question(
                parent_widget, 
                "데이터베이스 초기화", 
                "정말로 모든 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.db_connector.cursor()
                
                # 외래 키 제약 조건 때문에 순서대로 삭제
                tables = ['versions', 'shots', 'sequences', 'projects']
                
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                
                self.db_connector.commit()
                QMessageBox.information(parent_widget, "성공", "데이터베이스를 성공적으로 초기화했습니다.")
                return True

        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {str(e)}")
            QMessageBox.critical(parent_widget, "오류", f"데이터베이스 초기화 실패: {str(e)}")
            return False