"""데이터베이스 관리 서비스"""
from PySide6.QtWidgets import QMessageBox, QTextEdit

class DatabaseService:
    def __init__(self, db_connector, logger):
        self.db_connector = db_connector
        self.logger = logger

    def create_sequences_and_triggers(self):
        """시퀀스 및 트리거 생성"""
        try:
            cursor = self.db_connector.cursor()
            
            # 시퀀스 생성
            sequences = [
                "CREATE SEQUENCE PROJECTS_ID_GEN",
                "CREATE SEQUENCE SEQUENCES_ID_GEN",
                "CREATE SEQUENCE SHOTS_ID_GEN",
                "CREATE SEQUENCE VERSIONS_ID_GEN"
            ]
            
            for seq in sequences:
                try:
                    # 시퀀스가 이미 존재하는지 확인
                    seq_name = seq.split()[2]
                    cursor.execute(f"SELECT RDB$GENERATOR_NAME FROM RDB$GENERATORS WHERE RDB$GENERATOR_NAME = '{seq_name}'")
                    if cursor.fetchone():
                        self.logger.info(f"시퀀스가 이미 존재함: {seq_name}")
                    else:
                        cursor.execute(seq)
                        self.logger.info(f"시퀀스 생성 완료: {seq}")
                except Exception as e:
                    self.logger.warning(f"시퀀스 생성 중 오류 (무시됨): {str(e)}")
            
            # 트리거 생성
            triggers = [
                """
                CREATE TRIGGER BI_PROJECTS_ID FOR PROJECTS
                ACTIVE BEFORE INSERT POSITION 0
                AS
                BEGIN
                  IF (NEW.ID IS NULL) THEN
                    NEW.ID = NEXT VALUE FOR PROJECTS_ID_GEN;
                END
                """,
                """
                CREATE TRIGGER BI_SEQUENCES_ID FOR SEQUENCES
                ACTIVE BEFORE INSERT POSITION 0
                AS
                BEGIN
                  IF (NEW.ID IS NULL) THEN
                    NEW.ID = NEXT VALUE FOR SEQUENCES_ID_GEN;
                END
                """,
                """
                CREATE TRIGGER BI_SHOTS_ID FOR SHOTS
                ACTIVE BEFORE INSERT POSITION 0
                AS
                BEGIN
                  IF (NEW.ID IS NULL) THEN
                    NEW.ID = NEXT VALUE FOR SHOTS_ID_GEN;
                END
                """,
                """
                CREATE TRIGGER BI_VERSIONS_ID FOR VERSIONS
                ACTIVE BEFORE INSERT POSITION 0
                AS
                BEGIN
                  IF (NEW.ID IS NULL) THEN
                    NEW.ID = NEXT VALUE FOR VERSIONS_ID_GEN;
                END
                """
            ]
            
            for trg in triggers:
                try:
                    cursor.execute(trg)
                    self.logger.info(f"트리거 생성 완료: {trg}")
                except Exception as e:
                    self.logger.warning(f"트리거 생성 중 오류 (무시됨): {str(e)}")
            
            self.db_connector.commit()
            self.logger.info("시퀀스 및 트리거 생성 완료")
            return True
        except Exception as e:
            self.logger.error(f"시퀀스 및 트리거 생성 실패: {str(e)}")
            self.db_connector.rollback()
            return False

    def show_database_contents(self, parent_widget):
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
            msg_box = QMessageBox(parent_widget)
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

    def recreate_tables_and_sequences(self, parent_widget):
        """테이블 재생성 및 시퀀스/트리거 생성"""
        try:
            # TableManager를 통해 테이블 재생성
            from ..database.table_manager import TableManager
            table_manager = TableManager(self.db_connector)
            
            if table_manager.create_all_tables():
                # 시퀀스 및 트리거 생성
                if self.create_sequences_and_triggers():
                    QMessageBox.information(
                        parent_widget, 
                        "성공", 
                        "데이터베이스 테이블을 성공적으로 재생성했습니다."
                    )
                    return True
            raise Exception("테이블 재생성 실패")
        except Exception as e:
            self.logger.error(f"테이블 재생성 실패: {str(e)}")
            raise

    def clear_database(self, parent_widget):
        """데이터베이스 초기화 (테이블 재생성)"""
        try:
            # 첫 번째 확인 메시지
            reply = QMessageBox.question(
                parent_widget, 
                "데이터베이스 초기화", 
                "정말로 모든 테이블을 삭제하고 재생성하시겠습니까?\n"
                "이 작업은 되돌릴 수 없습니다.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.db_connector.cursor()
                tables = ['VERSIONS', 'SHOTS', 'SEQUENCES', 'PROJECTS']
                
                try:
                    # 모든 테이블 삭제
                    for table in tables:
                        try:
                            cursor.execute(f"""
                                SELECT 1 FROM RDB$RELATIONS 
                                WHERE RDB$RELATION_NAME = '{table}'
                                AND RDB$SYSTEM_FLAG = 0
                            """)
                            
                            if cursor.fetchone():
                                self.logger.info(f"테이블 삭제 시도: {table}")
                                cursor.execute(f"DROP TABLE {table}")
                                self.logger.info(f"테이블 삭제 완료: {table}")
                        except Exception as e:
                            self.logger.warning(f"테이블 {table} 삭제 중 오류 (무시됨): {str(e)}")
                            continue
                    
                    self.db_connector.commit()
                    self.logger.info("모든 테이블 삭제 완료")

                    # 두 번째 확인 메시지
                    reply = QMessageBox.question(
                        parent_widget,
                        "테이블 재생성",
                        "모든 테이블이 삭제되었습니다.\n"
                        "새로운 테이블을 생성하시겠습니까?",
                        QMessageBox.Yes | QMessageBox.No
                    )

                    if reply == QMessageBox.Yes:
                        return self.recreate_tables_and_sequences(parent_widget)
                    return True
                        
                except Exception as e:
                    self.db_connector.rollback()
                    raise Exception(f"데이터베이스 초기화 중 오류 발생: {str(e)}")

            return False

        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {str(e)}")
            QMessageBox.critical(
                parent_widget, 
                "오류", 
                f"데이터베이스 초기화 실패: {str(e)}"
            )
            return False