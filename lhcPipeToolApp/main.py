import sys
from PySide6.QtWidgets import QApplication, QDialog
from .config.db_config import DBConfig
from .database.db_connector import DBConnector
from .database.table_manager import TableManager
from .services.database_service import DatabaseService
from .ui.main_window import MainWindow
from .utils.logger import setup_logger
from .ui.login_dialog import LoginDialog
from .models.worker import Worker
from .config.app_state import AppState
from .utils.db_migration import run_migrations

def initialize_database():
    """데이터베이스 초기화"""
    config = DBConfig()
    db_connector = DBConnector(config)
    
    if not db_connector.connect():
        return None

    return db_connector

def main():
    app = QApplication(sys.argv)
    
    # 로거 초기화
    logger = setup_logger(__name__)
    
    # 데이터베이스 초기화
    db_connector = initialize_database()
    if not db_connector:
        sys.exit(1)
    
    # 데이터베이스 마이그레이션 실행
    run_migrations(db_connector)
    
    # 로그인 처리
    worker_model = Worker(db_connector)
    login_dialog = LoginDialog(worker_model)
    
    if login_dialog.exec() != QDialog.Accepted:
        sys.exit(1)
    
    # 로그인 성공 시 AppState에 사용자 정보 저장
    app_state = AppState()
    app_state.current_worker = login_dialog.logged_in_worker
    logger.info(f"로그인 성공: {app_state.current_worker}")
    
    # UI 생성 및 실행
    window = MainWindow(db_connector)
    window.show()

    # 종료 시 데이터베이스 연결 해제
    app.aboutToQuit.connect(db_connector.close)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()