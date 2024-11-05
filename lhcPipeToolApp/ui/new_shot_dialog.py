"""샷 생성/편집 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QTextEdit, QComboBox, QPushButton, 
                              QMessageBox, QFormLayout)

class NewShotDialog(QDialog):
    def __init__(self, project_service, sequence_id, project_tree, shot=None, parent=None):
        super().__init__(parent)
        self.project_service = project_service
        self.sequence_id = sequence_id
        self.shot = shot
        self.project_tree = project_tree
        self.setup_ui()
         
    def setup_ui(self):
        self.setWindowTitle("New Shot" if not self.shot else "Edit Shot")
        layout = QFormLayout(self)
        
        # 샷 이름 입력
        self.name_input = QLineEdit()
        if self.shot:
            self.name_input.setText(self.shot[1])  # shot name
        layout.addRow("Shot Name:", self.name_input)
        
        # 상태 선택
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "pending", "in_progress", "review", 
            "approved", "final", "on_hold"
        ])
        if self.shot:
            self.status_combo.setCurrentText(self.shot[3])  # status
        layout.addRow("Status:", self.status_combo)
        
        # 설명 입력
        self.description_input = QTextEdit()
        if self.shot and self.shot[4]:  # description
            self.description_input.setText(self.shot[4])
        layout.addRow("Description:", self.description_input)
        
        # 버튼
        button_layout = QVBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_shot)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow("", button_layout)
        
    def save_shot(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Shot name is required!")
            return
            
        status = self.status_combo.currentText()
        description = self.description_input.toPlainText()
        
        if self.shot:
            success = self.project_service.update_shot(
                self.shot[0], name, status, description
            )
        else:
            success = self.project_service.create_shot(
                self.sequence_id, name, status, description
            )
            
        if success:
            self.project_tree.refresh()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save shot!")