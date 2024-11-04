"""커스텀 트리 아이템 위젯"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class CustomTreeItemWidget(QWidget):
    def __init__(self, name, preview_path=None, parent=None):
        super().__init__(parent)
        self.setup_ui(name, preview_path)
        
    def setup_ui(self, name, preview_path):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 이름 라벨
        self.name_label = QLabel(str(name))
        self.name_label.setStyleSheet("""
            font-size: 16px;
            padding-left: 5px;
            color: #e0e0e0;
        """)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name_label)
        
        # 프리뷰 라벨
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(120, 68)  # 16:9 비율
        self.preview_label.setStyleSheet("background-color: #2a2a2a; border: 1px solid #3a3a3a;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        
        if preview_path:
            pixmap = QPixmap(preview_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(120, 68, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("No Preview")
        else:
            self.preview_label.setText("No Preview")
            
        layout.addWidget(self.preview_label)