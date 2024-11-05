import sys
from PySide6.QtWidgets import QApplication
from .config.db_config import DBConfig
from .database.db_connector import DBConnector
from .database.table_manager import TableManager
from .services.database_service import DatabaseService
from .ui.main_window import MainWindow
from .utils.logger import setup_logger

def initialize_database():
    """데이터베이스 초기화"""
    config = DBConfig()
    connector = DBConnector(config)
    
    if not connector.connect():
        return None

    return connector

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 로거 초기화
    logger = setup_logger(__name__)

    # 데이터베이스 초기화
    db_connector = initialize_database()
    if not db_connector:
        sys.exit(1)
        
    # UI 생성 및 실행
    window = MainWindow(db_connector)
    window.show()
    
    # 테이블 생성 확인
    if not TableManager.check_all_table_exists:
        service = DatabaseService(db_connector, logger)
        service.recreate_tables_and_sequences(window)

    # 종료 시 데이터베이스 연결 해제
    app.aboutToQuit.connect(db_connector.close)
    
    sys.exit(app.exec())