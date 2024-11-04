"""프로젝트 구조 새로고침 서비스"""
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

class RefreshService:
    def __init__(self, db_connector, project_service, version_service, logger):
        self.db_connector = db_connector
        self.project_service = project_service
        self.version_service = version_service
        self.logger = logger

    def refresh_project_structure(self, parent_widget):
        """프로젝트 구조 새로고침"""
        try:
            self.logger.info("프로젝트 구조 새로고침 시작")
            
            root_path = self._get_project_root()
            if not root_path:
                QMessageBox.warning(parent_widget, "경고", "프로젝트 루트 경로가 설정되지 않았습니다.")
                return False
                
            self.logger.info(f"프로젝트 루트 경로: {root_path}")
                
            # ProjectService의 동기화 메서드 사용
            self.project_service.sync_project_structure(root_path)
            
            QMessageBox.information(parent_widget, "성공", "프로젝트 구조를 성공적으로 동기화했습니다.")
            self.logger.info("프로젝트 구조 새로고침 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"프로젝트 구조 동기화 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(parent_widget, "오류", f"프로젝트 구조 동기화 실패: {str(e)}")
            return False

    def _get_project_root(self):
        """프로젝트 루트 경로 가져오기"""
        cursor = self.db_connector.cursor()
        cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'project_root'")
        result = cursor.fetchone()
        
        if not result:
            self.logger.warning("프로젝트 루트 경로가 설정되지 않음")
            return None
            
        root_path = Path(result[0])
        if not root_path.exists():
            self.logger.error(f"프로젝트 루트 경로가 존재하지 않음: {root_path}")
            return None
            
        return root_path