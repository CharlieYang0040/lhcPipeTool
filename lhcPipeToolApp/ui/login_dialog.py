from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from ..config.app_state import AppState
from ..utils.logger import setup_logger
import hashlib

class LoginDialog(QDialog):
    def __init__(self, worker_model, parent=None):
        super().__init__(parent)
        self.worker_model = worker_model
        self.logged_in_worker = None
        self.logger = setup_logger(__name__)
        self.setWindowTitle("로그인")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # 사용자명 입력
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("사용자명")
        layout.addWidget(QLabel("사용자명:"))
        layout.addWidget(self.name_input)
        
        # 비밀번호 입력
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("비밀번호")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("비밀번호:"))
        layout.addWidget(self.password_input)
        
        # 로그인 버튼
        login_button = QPushButton("로그인")
        login_button.clicked.connect(self.try_login)
        layout.addWidget(login_button)
        
        self.setLayout(layout)
        
    def try_login(self):
        name = self.name_input.text()
        password = self.password_input.text()
        
        # 비밀번호 해시화
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # 로그인 검증
        if self.worker_model.verify_credentials(name, hashed_password):
            self.logged_in_worker = self.worker_model.get_by_name(name)
            if self.logged_in_worker:
                app_state = AppState()
                try:
                    app_state.current_worker = self.logged_in_worker
                    self.accept()
                except ValueError as e:
                    self.logger.error(f"로그인 정보 오류: {e}")
                    QMessageBox.critical(self, "로그인 실패", str(e))
            else:
                QMessageBox.warning(self, "로그인 실패", "사용자 정보를 찾을 수 없습니다.")
        else:
            QMessageBox.warning(self, "로그인 실패", 
                                "사용자명 또는 비밀번호가 잘못되었습니다.")