"""커스텀 트리 아이템 위젯"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
import os

class CustomTreeItemWidget(QWidget):
    def __init__(self, name, item_type, preview_path=None, parent=None):
        super().__init__(parent)
        # 현재 파일의 디렉토리 경로를 가져옵니다
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.item_type = item_type  # 아이템 타입 저장
        self.setup_ui(name, preview_path)
        
    def load_svg_icon(self, icon_name, size=24):
        icon_path = os.path.join(self.base_path, 'lhcPipeToolApp', 'resources', 'icons', f'{icon_name}.svg')
        if not os.path.exists(icon_path):
            print(f"Icon not found: {icon_path}")
            return None
            
        renderer = QSvgRenderer(icon_path)
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap
        
    def setup_ui(self, name, preview_path):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 4)
        layout.setSpacing(12)
        
        # 아이콘 라벨
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setStyleSheet("QLabel { margin-top: 0px; }")
        
        # 타입에 따라 아이콘 설정
        if self.item_type == "sequence":
            icon_pixmap = self.load_svg_icon('sequence-icon')
        elif self.item_type == "shot":
            icon_pixmap = self.load_svg_icon('shot-icon')
        else:  # project
            icon_pixmap = self.load_svg_icon('project-icon')
            
        if icon_pixmap:
            self.icon_label.setPixmap(icon_pixmap)
        
        layout.addWidget(self.icon_label)
        
        # 이름 라벨
        self.name_label = QLabel(str(name))
        self.name_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: 500;
                color: #e0e0e0;
                padding: 2px 4px;
            }
        """)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name_label)
        
        # 스페이서 추가
        layout.addStretch()
        
        # 프리뷰 라벨
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(150, 85)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
                margin-top: -4px;
                margin-right: 0px;
            }
        """)
        self.preview_label.setAlignment(Qt.AlignCenter)
        
        if preview_path:
            pixmap = QPixmap(preview_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(150, 85, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("No Preview")
        else:
            self.preview_label.setText("No Preview")
            
        layout.addWidget(self.preview_label)

        # 선택 효과를 위한 스타일시트 수정
        self.setStyleSheet("""
            CustomTreeItemWidget {
                background: transparent;
                outline: none;
                border: none;
            }
            
            CustomTreeItemWidget:hover {
                background: #1f1f2c;  /* 호버 효과 */
            }
            
            CustomTreeItemWidget[selected="true"] {
                background: #2d2d3d;  /* 선택 시 배경색 */
                outline: none;
                border: none;
            }
            
            CustomTreeItemWidget[selected="true"]:hover {
                background: #363647;  /* 선택된 상태에서 호버 시 */
            }
        """)