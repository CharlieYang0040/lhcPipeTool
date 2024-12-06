from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QPixmap
from ..styles.components import get_dialog_style, get_button_style
from ..config.app_state import AppState
from ..utils.logger import setup_logger
import random
import string
import hashlib

class AdminAuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("관리자 인증")
        self.setStyleSheet(get_dialog_style())
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("관리자 아이디")
        self.password = QLineEdit()
        self.password.setPlaceholderText("비밀번호")
        self.password.setEchoMode(QLineEdit.Password)
        
        confirm_btn = QPushButton("인증")
        confirm_btn.setStyleSheet(get_button_style())
        confirm_btn.clicked.connect(self.accept)
        
        layout.addWidget(QLabel("관리자 아이디:"))
        layout.addWidget(self.username)
        layout.addWidget(QLabel("비밀번호:"))
        layout.addWidget(self.password)
        layout.addWidget(confirm_btn)
        
        self.setLayout(layout)

class LoginDialog(QDialog):
    def __init__(self, worker_service, parent=None):
        super().__init__(parent)
        self.worker_service = worker_service
        self.logged_in_worker = None
        self.logger = setup_logger(__name__)
        self.settings = QSettings('LHC', 'PipeTool')
        
        self.setWindowTitle("로그인")
        self.setModal(True)
        self.setStyleSheet(get_dialog_style())
        self.setMinimumWidth(500)

        self.setup_ui()
        self.set_last_login_user()
        
    def setup_ui(self):
        main_layout = QHBoxLayout()
        
        # 로고 영역
        logo_layout = QVBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap("lhcPipeToolApp/resources/LIONHEART_LOGO.png")
        
        # QPixmap을 QImage로 변환하고 색상 반전
        image = logo_pixmap.toImage()
        image.invertPixels()
        
        # QImage를 다시 QPixmap으로 변환
        inverted_pixmap = QPixmap.fromImage(image)
        
        # 크기 조정
        scaled_pixmap = inverted_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        logo_layout.addStretch()
        main_layout.addLayout(logo_layout)
        
        # 로그인 폼 영역
        form_layout = QVBoxLayout()
        
        # 사용자명 입력
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("사용자명")
        form_layout.addWidget(QLabel("사용자명:"))
        form_layout.addWidget(self.name_input)
                
        # 비밀번호 입력
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("비밀번호")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(QLabel("비밀번호:"))
        form_layout.addWidget(self.password_input)


        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        # 로그인 버튼
        login_button = QPushButton("로그인")
        login_button.clicked.connect(self.try_login)
        login_button.setStyleSheet(get_button_style())
        
        # 비밀번호 초기화 버튼
        reset_button = QPushButton("비밀번호 초기화")
        reset_button.clicked.connect(self.reset_password_dialog)
        reset_button.setStyleSheet(get_button_style())
        
        # 비밀번호 변경 버튼 추가
        change_password_button = QPushButton("비밀번호 변경")
        change_password_button.clicked.connect(self.change_password)
        change_password_button.setStyleSheet(get_button_style())
        
        button_layout.addWidget(login_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(change_password_button)  # 비밀번호 변경 버튼 추가
        
        form_layout.addLayout(button_layout)
        form_layout.addStretch()
        
        main_layout.addLayout(form_layout)
        self.setLayout(main_layout)
        
    def try_login(self):
        name = self.name_input.text()
        password = self.password_input.text()
        
        # 비밀번호 해시화
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # 로그인 검증
        if self.worker_service.verify_credentials(name, hashed_password):
            self.logged_in_worker = self.worker_service.get_worker_by_name(name)
            if self.logged_in_worker:
                # 로그인 성공 시 사용자명 저장
                self.settings.setValue('last_login_user', name)
                
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

    def reset_password_dialog(self):
        """비밀번호 초기화 프로세스"""
        # 관리자 인증
        auth_dialog = AdminAuthDialog(self)
        if auth_dialog.exec() != QDialog.Accepted:
            return
            
        admin_name = auth_dialog.username.text()
        admin_password = auth_dialog.password.text()
        hashed_admin_password = hashlib.sha256(admin_password.encode()).hexdigest()
        
        # 관리자 권한 확인
        if not self.worker_service.verify_credentials(admin_name, hashed_admin_password):
            QMessageBox.warning(self, "인증 실패", "관리자 계정 정보가 올바르지 않습니다.")
            return
            
        if not self.worker_service.is_admin(admin_name):
            QMessageBox.warning(self, "권한 없음", "관리자 권한이 필요합니다.")
            return
        
        # 초기화할 사용자 선택
        target_username = self.name_input.text()
        if not target_username:
            target_username, ok = QInputDialog.getText(
                self, "사용자 선택", "초기화할 사용자의 이름을 입력하세요:")
            if not ok or not target_username:
                return
        
        worker_id = self.worker_service.get_worker_by_name(target_username)['id']
        if not worker_id:
            QMessageBox.warning(self, "오류", "존재하지 않는 사용자입니다.")
            return
        
        try:
            # 임시 비밀번호 생성 (실제 환경에서는 더 복잡한 비밀번호 생성 로직 사용)
            # temp_password = "".join(random.choices(string.ascii_letters + string.digits, k=8))
            temp_password = "lion"
            # 비밀번호 초기화
            self.worker_service.reset_password(worker_id, temp_password)
            
            # 성공 메시지 표시
            msg = (f"비밀번호가 성공적으로 초기화되었습니다.\n\n"
                f"사용자: {target_username}\n"
                f"임시 비밀번호: {temp_password}\n\n"
                "사용자에게 임시 비밀번호를 안전하게 전달해주세요.")
            
            QMessageBox.information(self, "비밀번호 초기화 완료", msg)
            
        except Exception as e:
            self.logger.error(f"비밀번호 초기화 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"비밀번호 초기화 중 오류가 발생했습니다.\n{str(e)}")

    def change_password(self):
        """비밀번호 변경"""
        name = self.name_input.text()
        if not name:
            QMessageBox.warning(self, "경고", "사용자명을 입력해주세요.")
            return
        
        worker = self.worker_service.get_worker_by_name(name)
        if not worker:
            QMessageBox.warning(self, "경고", "존재하지 않는 사용자입니다.")
            return
        
        # 현재 비밀번호 확인
        current_password, ok = QInputDialog.getText(
            self, "비밀번호 변경", 
            "현재 비밀번호를 입력하세요:", 
            QLineEdit.Password
        )
        if not ok:
            return
        
        # 현재 비밀번호 검증
        hashed_current_password = hashlib.sha256(current_password.encode()).hexdigest()
        if not self.worker_service.verify_credentials(name, hashed_current_password):
            QMessageBox.warning(self, "경고", "현재 비밀번호가 일치하지 않습니다.")
            return
        
        # 새 비밀번호 입력
        new_password, ok = QInputDialog.getText(
            self, "비밀번호 변경", 
            "새 비밀번호를 입력하세요:", 
            QLineEdit.Password
        )
        if not ok or not new_password:
            return
        
        # 새 비밀번호 확인
        confirm_password, ok = QInputDialog.getText(
            self, "비밀번호 변경", 
            "새 비밀번호를 다시 입력하세요:", 
            QLineEdit.Password
        )
        if not ok or new_password != confirm_password:
            QMessageBox.warning(self, "경고", "새 비밀번호가 일치하지 않습니다.")
            return
        
        try:
            self.worker_service.reset_password(worker['id'], new_password)
            QMessageBox.information(self, "알림", "비밀번호가 성공적으로 변경되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"비밀번호 변경 실패: {str(e)}")

    def set_last_login_user(self):
        last_user = self.settings.value('last_login_user', '')
        if last_user:
            self.name_input.setText(last_user)
            self.password_input.setFocus()  # 비밀번호 입력창으로 커서 이동