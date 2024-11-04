import sys
from PySide6.QtWidgets import QApplication
from .config.db_config import DBConfig
from .database.db_connector import DBConnector
from .database.table_manager import TableManager
from .ui.main_window import MainWindow
from .utils.db_utils import check_table_schema, check_table_exists

def initialize_database():
    """데이터베이스 초기화"""
    config = DBConfig()
    connector = DBConnector(config)
    
    if not connector.connect():
        return None
        
    table_manager = TableManager(connector)
    
    return connector

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 데이터베이스 초기화
    db_connector = initialize_database()
    if not db_connector:
        sys.exit(1)
        
    # UI 생성 및 실행
    window = MainWindow(db_connector)
    window.show()
    
    # 종료 시 데이터베이스 연결 해제
    app.aboutToQuit.connect(db_connector.close)
    
    sys.exit(app.exec())