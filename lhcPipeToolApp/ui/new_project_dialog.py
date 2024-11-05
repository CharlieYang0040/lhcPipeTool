"""새 프로젝트 생성 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QPushButton, QLabel, QMessageBox)

class NewProjectDialog(QDialog):
    def __init__(self, project_service, project_tree, parent=None):
        super().__init__(parent)
        self.project_service = project_service
        self.project_tree = project_tree
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("New Project")
        layout = QVBoxLayout(self)
        
        # 프로젝트 이름 입력
        self.name_input = QLineEdit()
        layout.addWidget(QLabel("Project Name:"))
        layout.addWidget(self.name_input)
        
        # 확인/취소 버튼
        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.create_project)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        layout.addWidget(self.create_button)
        layout.addWidget(self.cancel_button)
        
    def create_project(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Project name is required!")
            return
            
        if self.project_service.create_project(name):
            self.project_tree.refresh()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to create project!")