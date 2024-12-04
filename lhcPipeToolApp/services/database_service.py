"""데이터베이스 관리 서비스"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QMessageBox, QFileDialog
from datetime import datetime
import json
import csv
from ..utils.logger import setup_logger

class DatabaseService:
    def __init__(self, database_model):
        self.database_model = database_model
        self.logger = setup_logger(__name__)

    def show_database_contents(self, parent_widget):
        """데이터베이스 내용 출력"""
        try:
            output = []
            # 테이블 순서 지정
            table_order = ['PROJECTS', 'PROJECT_VERSIONS', 'SEQUENCES', 
                          'SEQUENCE_VERSIONS', 'SHOTS', 'VERSIONS', 
                          'WORKERS', 'SETTINGS']
            
            # 모든 테이블 목록 조회
            available_tables = self.database_model.get_all_tables()
            if not available_tables:
                output.append("데이터베이스에 테이블이 없습니다.")
                self._show_data_in_gui(output, parent_widget)
                return

            # 지정된 순서대로 테이블 처리
            tables = [table for table in table_order 
                     if table in [t.strip() for t in available_tables]]
            
            for table in tables:
                output.append(f"\n### {table.strip()} 테이블 ###")
                # 테이블의 컬럼 정보 조회
                columns_info = self.database_model.get_table_columns(table)
                if columns_info:
                    # 대소문자를 고려하여 키 검색
                    column_key = next((key for key in columns_info[0].keys() 
                                    if key.upper() == 'COLUMN_NAME'), None)
                    if column_key:
                        columns = [col[column_key].strip() for col in columns_info]
                        output.append("컬럼: " + ", ".join(columns))
                    else:
                        output.append("컬럼 정보를 가져올 수 없습니다.")

                # 테이블의 데이터 조회
                table_data = self.database_model.get_table_data(table)
                if table_data:
                    for row in table_data:
                        # 각 행의 데이터를 문자열로 변환하여 출력
                        row_data = ', '.join([f"{key}={value}" for key, value in row.items()])
                        output.append(row_data)
                else:
                    output.append("데이터가 없습니다.")

            # 결과를 GUI에 표시
            self._show_data_in_gui(output, parent_widget)

        except Exception as e:
            self.logger.error(f"데이터베이스 내용 조회 실패: {str(e)}", exc_info=True)
            QMessageBox.warning(parent_widget, "오류", "데이터베이스 내용 조회 중 오류가 발생했습니다.")

    def _show_data_in_gui(self, output, parent_widget):
        """GUI에 데이터 표시"""
        dialog = QDialog(parent_widget)
        dialog.setWindowTitle("데이터베이스 내용")
        dialog.setMinimumWidth(1200)
        dialog.setMinimumHeight(800)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        html_content = """
        <pre style='font-family: "Consolas", monospace; font-size: 12px; 
                    line-height: 1.4; background-color: #2d2d2d; padding: 10px; color: #ffffff;'>
        """
        
        def truncate_path(value, max_length=50):
            """긴 경로를 줄여서 표시"""
            if len(value) <= max_length:
                return value
            return f"...{value[-max_length:]}"
        
        for line in output:
            if line.startswith("==="):
                html_content += f"<h3 style='color: #ffffff; margin: 15px 0; padding: 5px; background-color: #383838;'>{line}</h3>"
            elif line.startswith("컬럼:"):
                html_content += f"<p style='color: #27ae60; margin: 5px 0;'>{line}</p>"
            elif "=" in line and not line.startswith("==="):
                parts = line.split(", ")
                formatted_parts = []
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        # 경로인 경우 처리
                        if any(path_indicator in value.lower() for path_indicator in 
                              ["/", "\\", ".jpg", ".png", ".mov", ".mp4", ":\\", ".fbk"]):
                            truncated_value = truncate_path(value)
                            formatted_parts.append(
                                f"<span style='color: #2980b9;'>{key}</span>="
                                f"<span style='color: #8e44ad;' title='{value}'>{truncated_value}</span>"
                            )
                        else:
                            formatted_parts.append(
                                f"<span style='color: #2980b9;'>{key}</span>="
                                f"<span style='color: #c0392b;'>{value}</span>"
                            )
                html_content += f"<div style='margin: 3px 0; padding-left: 20px;'>{', '.join(formatted_parts)}</div>"
            else:
                html_content += f"<div style='margin: 3px 0; color: #ffffff;'>{line}</div>"

        html_content += "</pre>"

        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
            }
        """)
        
        text_edit.setHtml(html_content)
        
        layout.addWidget(text_edit)
        dialog.resize(1300, 900)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
        """)
        
        dialog.exec()

    def export_database(self, parent_widget):
        """데이터베이스 내보내기 (JSON 또는 CSV)"""
        try:
            # 데이터베이스의 모든 테이블과 데이터를 가져옴
            database_content = {}
            tables = self.database_model.get_all_tables()
            for table in tables:
                table_data = self.database_model.get_table_data(table)
                database_content[table.strip()] = table_data

            # 파일 저장 다이얼로그 표시
            file_dialog = QFileDialog(parent_widget)
            file_path, _ = file_dialog.getSaveFileName(
                parent_widget,
                "데이터베이스 내보내기",
                f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "JSON Files (*.json);;CSV Files (*.csv)"
            )

            if not file_path:
                return False

            # 파일 확장자에 따라 내보내기 형식 결정
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(database_content, f, ensure_ascii=False, indent=2)
            elif file_path.endswith('.csv'):
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for table_name, rows in database_content.items():
                        writer.writerow([f"=== {table_name} 테이블 ==="])
                        if rows:
                            # 컬럼명 작성
                            columns = rows[0].keys()
                            writer.writerow(columns)
                            # 데이터 작성
                            for row in rows:
                                writer.writerow(row.values())
                        else:
                            writer.writerow(['데이터가 없습니다.'])
            else:
                QMessageBox.warning(parent_widget, "오류", "지원하지 않는 파일 형식입니다.")
                return False

            QMessageBox.information(parent_widget, "성공", "데이터베이스 내보내기가 완료되었습니다.")
            return True

        except Exception as e:
            self.logger.error(f"데이터베이스 내보내기 실패: {str(e)}")
            QMessageBox.warning(parent_widget, "오류", "데이터베이스 내보내기 중 오류가 발생했습니다.")
            return False

    def backup_database(self, parent_widget):
        """데이터베이스 백업"""
        try:
            backup_path = QFileDialog.getSaveFileName(
                parent_widget,
                "데이터베이스 백업",
                f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.fbk",
                "Firebird Backup (*.fbk)"
            )[0]

            if backup_path:
                self.database_model.backup_database(backup_path)
                QMessageBox.information(parent_widget, "성공", "데이터베이스 백업이 완료되었습니다.")
                return True
            return False

        except Exception as e:
            self.logger.error(f"데이터베이스 백업 실패: {str(e)}")
            QMessageBox.critical(parent_widget, "오류", f"데이터베이스 백업 실패: {str(e)}")
            return False

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
                # 외래 키 제약 조건 때문에 테이블 삭제 순서 지정
                tables = ['VERSIONS', 'SEQUENCE_VERSIONS', 'PROJECT_VERSIONS', 'SHOTS', 'SEQUENCES', 'PROJECTS']

                for table in tables:
                    self.database_model.clear_table(table)

                self.database_model._commit()
                QMessageBox.information(parent_widget, "성공", "데이터베이스를 성공적으로 초기화했습니다.")
                return True

        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {str(e)}")
            QMessageBox.critical(parent_widget, "오류", f"데이터베이스 초기화 실패: {str(e)}")
            return False

    def show_table_statistics(self, parent_widget):
        """테이블 통계 정보 표시"""
        try:
            output = []
            tables = self.database_model.get_all_tables()
            if not tables:
                output.append("데이터베이스에 테이블이 없습니다.")
                self._show_data_in_gui(output, parent_widget)
                return

            output.append("데이터베이스 통계:")

            for table in tables:
                stats = self.database_model.get_table_statistics(table)
                if stats is None:
                    stats = {
                        'total_rows': 0,
                        'last_created': None,
                        'last_updated': None
                    }

                output.append(f"\n{table.strip()}:")
                output.append(f"행 수: {stats['total_rows']}")
                if stats['last_created']:
                    output.append(f"마지막 생성: {stats['last_created']}")
                if stats['last_updated']:
                    output.append(f"마지막 수정: {stats['last_updated']}")

            # 결과를 GUI에 표시
            self._show_data_in_gui(output, parent_widget)

        except Exception as e:
            self.logger.error(f"테이블 통계 조회 실패: {str(e)}", exc_info=True)
            QMessageBox.warning(parent_widget, "오류", "테이블 통계 조회 중 오류가 발생했습니다.")

