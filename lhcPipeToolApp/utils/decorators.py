from functools import wraps
from PySide6.QtWidgets import QMessageBox
from ..config.app_state import AppState
from ..models.worker import Worker

def require_admin(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        db_connector = self.db_connector  # self에서 db_connector를 가져옴
        app_state = AppState()
        if not app_state.current_worker:
            QMessageBox.warning(None, "권한 없음", 
                                "현재 작업자가 설정되지 않았습니다.")
            return None
        
        if 'id' not in app_state.current_worker:
            QMessageBox.warning(None, "권한 없음", 
                                "작업자 정보가 올바르지 않습니다.")
            return None

        if not Worker(db_connector).is_admin(app_state.current_worker['name']):
            QMessageBox.warning(None, "권한 없음", 
                                "이 작업을 수행할 권한이 없습니다.")
            return None
        
        return func(self, *args, **kwargs)
    return wrapper