"""데이터베이스 관리 서비스"""
from PySide6.QtWidgets import QMessageBox, QTextEdit, QFileDialog
from datetime import datetime
import json
import csv
from ..utils.logger import setup_logger

class DatabaseService:
    def __init__(self, database_model):
        self.database_model = database_model
        self.logger = setup_logger(__name__)

    def show_database_contents(self, parent_widget, export_format=None):
        """데이터베이스 내용 출력 및 선택적 내보내기"""
        try:
            output = []
            tables = self.database_model.get_all_tables()
            
            for table in tables:
                output.append(f"\n=== {table} 테이블 ===")
                columns = self.database_model.get_table_columns(table)
                stats = self.database_model.get_table_statistics(table)
                data = self.database_model.get_table_data(table)
                
                # 테이블 정보 추가
                output.append(f"행 수: {stats['row_count']}")
                output.append("컬럼: " + ", ".join([col['COLUMN_NAME'].strip() for col in columns]))
                
                # 데이터 추가
                for row in data:
                    output.append(str(row))
                    
            if export_format:
                return self._export_data(output, export_format, parent_widget)
                
            # GUI 표시
            self._show_data_in_gui(output, parent_widget)
            
        except Exception as e:
            self.logger.error(f"데이터베이스 내용 조회 실패: {str(e)}")
            QMessageBox.critical(parent_widget, "오류", f"데이터베이스 내용 조회 실패: {str(e)}")

    def _export_data(self, data, format_type, parent_widget):
        """데이터 내보내기"""
        try:
            file_dialog = QFileDialog(parent_widget)
            file_path, _ = file_dialog.getSaveFileName(
                parent_widget,
                "데이터 내보내기",
                f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if not file_path:
                return False
                
            if format_type == 'json':
                with open(f"{file_path}.json", 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format_type == 'csv':
                with open(f"{file_path}.csv", 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for line in data:
                        writer.writerow([line])
            elif format_type == 'sql':
                # SQL 덤프 파일 생성
                pass
                
            return True
                
        except Exception as e:
            self.logger.error(f"데이터 내보내기 실패: {str(e)}")
            raise

    def _show_data_in_gui(self, output, parent_widget):
        """GUI에 데이터 표시"""
        msg_box = QMessageBox(parent_widget)
        msg_box.setWindowTitle("데이터베이스 내용")
        msg_box.setIcon(QMessageBox.Information)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMinimumWidth(800)
        text_edit.setMinimumHeight(600)
        
        html_content = "<pre style='font-family: Consolas, monospace;'>"
        for line in output:
            if line.startswith("==="): 
                html_content += f"<h3 style='color: blue;'>{line}</h3>"
            elif line.startswith("컬럼:"):
                html_content += f"<p style='color: green;'>{line}</p>"
            elif line.startswith("행 수:"):
                html_content += f"<p style='color: purple;'>{line}</p>"
            else:
                html_content += f"{line}<br>"
        html_content += "</pre>"
        
        text_edit.setHtml(html_content)
        msg_box.layout().addWidget(text_edit, 0, 0, 1, msg_box.layout().columnCount())
        msg_box.exec()

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