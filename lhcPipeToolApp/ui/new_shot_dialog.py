"""샷 생성/편집 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QTextEdit, QComboBox, QPushButton, 
                              QMessageBox, QFormLayout, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt

class NewShotDialog(QDialog):
    def __init__(self, project_service, sequence_id, project_tree, shot=None, parent=None):
        super().__init__(parent)
        self.project_service = project_service
        self.sequence_id = sequence_id
        self.shot = shot
        self.project_tree = project_tree
        self.setup_ui()
         
    def setup_ui(self):
        self.setWindowTitle("새 샷 생성" if not self.shot else "샷 편집")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 스타일 설정
        self.setStyleSheet("""
            QDialog {
                background-color: #15151e;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 5px;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QComboBox {
                padding-right: 20px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/ue-arrow-down.svg);
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                selection-background-color: #2d2d3d;
            }
            QPushButton {
                background-color: #2d2d3d;
                border: none;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 8px;
                font-family: 'Segoe UI';
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #363647;
            }
            QPushButton:pressed {
                background-color: #404052;
            }
        """)
        
        # 샷 이름 입력
        name_layout = QVBoxLayout()
        name_layout.setSpacing(5)
        name_label = QLabel("샷 이름:")
        self.name_input = QLineEdit()
        if self.shot:
            self.name_input.setText(self.shot[1])
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 상태 선택
        status_layout = QVBoxLayout()
        status_layout.setSpacing(5)
        status_label = QLabel("상태:")
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "pending", "in_progress", "review", 
            "approved", "hold", "omitted"
        ])
        if self.shot:
            self.status_combo.setCurrentText(self.shot[3])
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        layout.addLayout(status_layout)
        
        # 설명 입력
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(5)
        desc_label = QLabel("설명:")
        self.description_input = QTextEdit()
        self.description_input.setMinimumHeight(80)
        self.description_input.setMaximumHeight(120)
        if self.shot and self.shot[4]:
            self.description_input.setText(self.shot[4])
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.description_input)
        layout.addLayout(desc_layout)
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_shot)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def save_shot(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "샷 이름을 입력해주세요!")
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
            QMessageBox.critical(self, "오류", "샷 저장에 실패했습니다.")