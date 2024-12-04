"""프로젝트 구조 새로고침 서비스"""
from PySide6.QtWidgets import QMessageBox
from ..utils.logger import setup_logger

class RefreshService:
    def __init__(self, refresh_model, project_service, version_service, worker_id):
        self.refresh_model = refresh_model
        self.project_service = project_service
        self.version_service = version_service
        self.worker_id = worker_id
        self.logger = setup_logger(__name__)

    def refresh_project_structure(self, parent_widget):
        """프로젝트 구조 새로고침"""
        try:
            self.logger.info("프로젝트 구조 새로고침 시작")
            
            root_path = self.refresh_model.get_project_root()
            if not root_path:
                error_msg = "프로젝트 루트 경로가 설정되지 않았습니다."
                self.refresh_model.log_refresh(
                    self.worker_id,
                    "실패",
                    error_msg
                )
                QMessageBox.warning(parent_widget, "경고", error_msg)
                return False
                
            self.logger.info(f"프로젝트 루트 경로: {root_path}")
                
            # ProjectService의 동기화 메서드 사용
            self.project_service.sync_project_structure(root_path)
            
            # 성공 로그 기록
            self.refresh_model.log_refresh(
                self.worker_id,
                "성공",
                "프로젝트 구조를 성공적으로 동기화했습니다.",
                root_path
            )
            
            QMessageBox.information(parent_widget, "성공", "프로젝트 구조를 성공적으로 동기화했습니다.")
            self.logger.info("프로젝트 구조 새로고침 완료")
            return True
            
        except Exception as e:
            error_msg = f"프로젝트 구조 동기화 실패: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            # 실패 로그 기록
            self.refresh_model.log_refresh(
                self.worker_id,
                "실패",
                error_msg,
                root_path if 'root_path' in locals() else None
            )
            
            QMessageBox.critical(parent_widget, "오류", error_msg)
            return False

    def get_refresh_history(self, limit=100):
        """새로고침 히스토리 조회"""
        return self.refresh_model.get_refresh_history(limit)

    def get_last_refresh(self):
        """마지막 새로고침 정보 조회"""
        return self.refresh_model.get_last_refresh()