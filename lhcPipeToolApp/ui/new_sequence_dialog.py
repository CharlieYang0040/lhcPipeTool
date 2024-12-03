"""시퀀스 생성/편집 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QPushButton, QLabel, QMessageBox,
                              QHBoxLayout, QTextEdit)
from PySide6.QtCore import Qt, QTimer
from ..styles.components import get_dialog_style, get_button_style

class NewSequenceDialog(QDialog):
    def __init__(self, project_service, project_id, project_tree, sequence=None, parent=None):
        super().__init__(parent)
        self.project_service = project_service
        self.project_id = project_id
        self.sequence = sequence
        self.project_tree = project_tree
        self.setup_ui()
        self.setup_tab_order()
        
    def setup_ui(self):
        self.setWindowTitle("새 시퀀스 생성" if not self.sequence else "시퀀스 편집")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 스타일 설정
        self.setStyleSheet(get_dialog_style())
        
        # 시퀀스 이름 입력
        name_layout = QVBoxLayout()
        name_layout.setSpacing(5)
        name_label = QLabel("시퀀스 이름:")
        self.name_input = QLineEdit()
        if self.sequence:
            self.name_input.setText(self.sequence[1])
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 레벨 경로 입력
        level_layout = QVBoxLayout()
        level_layout.setSpacing(5)
        level_label = QLabel("레벨 경로:")
        self.level_input = QLineEdit()
        if self.sequence:
            self.level_input.setText(self.sequence[2])
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_input)
        layout.addLayout(level_layout)
        
        # 설명 입력
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(5)
        desc_label = QLabel("설명:")
        self.description_input = QTextEdit()
        self.description_input.setMinimumHeight(80)
        self.description_input.setMaximumHeight(120)
        if self.sequence:
            self.description_input.setText(self.sequence[3])
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.description_input)
        layout.addLayout(desc_layout)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_button = QPushButton("저장")
        self.save_button.setStyleSheet(get_button_style())
        self.save_button.clicked.connect(self.save_sequence)
        
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
        self.level_input.setFocusPolicy(Qt.StrongFocus)
        self.description_input.setFocusPolicy(Qt.StrongFocus)
        self.save_button.setFocusPolicy(Qt.StrongFocus)
        self.cancel_button.setFocusPolicy(Qt.StrongFocus)
        
        self.setTabOrder(self.name_input, self.level_input)
        self.setTabOrder(self.level_input, self.description_input)
        self.setTabOrder(self.description_input, self.save_button)
        self.setTabOrder(self.save_button, self.cancel_button)
        
    def save_sequence(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "시퀀스 이름을 입력해주세요!")
            return
            
        if self.sequence:
            success = self.project_service.update_sequence(
                self.sequence[0],
                name,
                self.level_input.text().strip(),
                self.description_input.toPlainText().strip()
            )
        else:
            success = self.project_service.create_sequence(
                name, 
                self.project_id,
                self.level_input.text().strip(),
                self.description_input.toPlainText().strip()
            )
            
        if success:
            self.project_tree.load_projects()
            self.accept()
        else:
            QMessageBox.critical(self, "오류", "시퀀스 저장에 실패했습니다!")