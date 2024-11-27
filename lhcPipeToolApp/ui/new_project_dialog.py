"""새 프로젝트 생성 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QPushButton, QLabel, QMessageBox,
                              QHBoxLayout, QTextEdit)
from PySide6.QtCore import Qt, QTimer
from ..styles.components import get_dialog_style, get_button_style

class NewProjectDialog(QDialog):
    def __init__(self, project_service, project_tree, project=None, parent=None):
        super().__init__(parent)
        self.project_service = project_service
        self.project_tree = project_tree
        self.project = project
        self.setup_ui()
        self.setup_tab_order()
        
    def setup_ui(self):
        self.setWindowTitle("새 프로젝트 생성" if not self.project else "프로젝트 편집")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 스타일 설정
        self.setStyleSheet(get_dialog_style())
        
        # 프로젝트 이름 입력
        name_layout = QVBoxLayout()
        name_layout.setSpacing(5)
        name_label = QLabel("프로젝트 이름:")
        self.name_input = QLineEdit()
        if self.project:
            self.name_input.setText(self.project[1])
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 설명 입력
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(5)
        desc_label = QLabel("설명:")
        self.description_input = QTextEdit()
        self.description_input.setMinimumHeight(80)
        self.description_input.setMaximumHeight(120)
        if self.project:
            self.description_input.setText(self.project[2])
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.description_input)
        layout.addLayout(desc_layout)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_button = QPushButton("저장")
        self.save_button.setStyleSheet(get_button_style())
        self.save_button.clicked.connect(self.save_project)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setStyleSheet(get_button_style())
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def setup_tab_order(self):
        """탭 순서 설정"""
        QTimer.singleShot(100, self._set_tab_order)

    def _set_tab_order(self):
        """실제 탭 순서 설정"""
        self.name_input.setFocusPolicy(Qt.StrongFocus)
        self.description_input.setFocusPolicy(Qt.StrongFocus)
        self.save_button.setFocusPolicy(Qt.StrongFocus)
        self.cancel_button.setFocusPolicy(Qt.StrongFocus)
        
        self.setTabOrder(self.name_input, self.description_input)
        self.setTabOrder(self.description_input, self.save_button)
        self.setTabOrder(self.save_button, self.cancel_button)
        
    def save_project(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "프로젝트 이름을 입력해주세요!")
            return
            
        if self.project:
            success = self.project_service.update_project(
                self.project[0],
                name,
                self.description_input.toPlainText().strip()
            )
        else:
            success = self.project_service.create_project(
                name, 
                self.description_input.toPlainText().strip()
            )
            
        if success:
            self.project_tree.refresh()
            self.accept()
        else:
            QMessageBox.critical(self, "오류", "프로젝트 저장에 실패했습니다!")