"""새 버전 생성 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QPushButton, QLabel, QTextEdit, 
                              QFileDialog, QMessageBox)

class NewVersionDialog(QDialog):
    def __init__(self, version_service, shot_id, parent=None):
        super().__init__(parent)
        self.version_service = version_service
        self.shot_id = shot_id
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("New Version")
        layout = QVBoxLayout(self)
        
        # 작업자 이름
        self.worker_input = QLineEdit()
        layout.addWidget(QLabel("Worker Name:"))
        layout.addWidget(self.worker_input)
        
        # 파일 선택
        self.file_path_input = QLineEdit()
        self.file_browse_btn = QPushButton("Browse...")
        self.file_browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(QLabel("File:"))
        layout.addWidget(self.file_path_input)
        layout.addWidget(self.file_browse_btn)
        
        # 프리뷰 파일 선택
        self.preview_path_input = QLineEdit()
        self.preview_browse_btn = QPushButton("Browse Preview...")
        self.preview_browse_btn.clicked.connect(self.browse_preview)
        layout.addWidget(QLabel("Preview File:"))
        layout.addWidget(self.preview_path_input)
        layout.addWidget(self.preview_browse_btn)
        
        # 코멘트
        self.comment_input = QTextEdit()
        layout.addWidget(QLabel("Comment:"))
        layout.addWidget(self.comment_input)
        
        # 확인/취소 버튼
        self.create_button = QPushButton("Create Version")
        self.create_button.clicked.connect(self.create_version)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        layout.addWidget(self.create_button)
        layout.addWidget(self.cancel_button)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "All Files (*.*)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            
    def browse_preview(self):
        preview_path, _ = QFileDialog.getOpenFileName(
            self, "Select Preview File", "", "Image Files (*.jpg *.png);;Video Files (*.mp4 *.mov)"
        )
        if preview_path:
            self.preview_path_input.setText(preview_path)
            
    def create_version(self):
        worker_name = self.worker_input.text().strip()
        if not worker_name:
            QMessageBox.warning(self, "Warning", "Worker name is required!")
            return
            
        success = self.version_service.create_version(
            shot_id=self.shot_id,
            worker_name=worker_name,
            file_path=self.file_path_input.text(),
            preview_path=self.preview_path_input.text(),
            comment=self.comment_input.toPlainText()
        )
        
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to create version!")