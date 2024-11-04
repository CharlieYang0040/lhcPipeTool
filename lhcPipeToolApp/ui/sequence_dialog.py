"""시퀀스 생성/편집 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QPushButton, QLabel, QMessageBox)

class SequenceDialog(QDialog):
    def __init__(self, project_service, project_id, sequence=None, parent=None):
        super().__init__(parent)
        self.project_service = project_service
        self.project_id = project_id
        self.sequence = sequence  # 편집 모드일 경우 기존 시퀀스 정보
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("New Sequence" if not self.sequence else "Edit Sequence")
        layout = QVBoxLayout(self)
        
        # 시퀀스 이름 입력
        self.name_input = QLineEdit()
        if self.sequence:
            self.name_input.setText(self.sequence[1])  # sequence name
        layout.addWidget(QLabel("Sequence Name:"))
        layout.addWidget(self.name_input)
        
        # 확인/취소 버튼
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_sequence)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        layout.addWidget(self.save_button)
        layout.addWidget(self.cancel_button)
        
    def save_sequence(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Sequence name is required!")
            return
            
        if self.sequence:
            # 편집 모드
            success = self.project_service.update_sequence(
                self.sequence[0], name
            )
        else:
            # 새로 생성
            success = self.project_service.create_sequence(
                self.project_id, name
            )
            
        if success:
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error", 
                "Failed to save sequence!"
            )