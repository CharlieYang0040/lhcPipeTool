"""커스텀 트리 아이템 위젯"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
import os
from PySide6.QtWidgets import QApplication

class CustomTreeItemWidget(QWidget):
    def __init__(self, name, item_type, preview_path=None, parent=None):
        super().__init__(parent)
        # 현재 파일의 디렉토리 경로를 가져옵니다
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.item_type = item_type  # 아이템 타입 저장
        
        # 화면 해상도에 따른 크기 계산
        self.scale_factor = self.calculate_scale_factor()
        self.setup_ui(name, preview_path)
        
    def calculate_scale_factor(self):
        """화면 해상도에 따른 스케일 팩터 계산"""
        screen = QApplication.primaryScreen()
        dpi = screen.logicalDotsPerInch()
        
        # 기준 DPI (96은 일반적인 FHD 해상도의 DPI)
        base_dpi = 96
        return dpi / base_dpi

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
        
        # 스케일 팩터에 따른 여백 조정
        margin_size = int(8 * self.scale_factor)
        layout.setContentsMargins(margin_size, 2, margin_size, 4)
        layout.setSpacing(int(12 * self.scale_factor))
        
        # 아이콘 크기 조정
        icon_size = int(24 * self.scale_factor)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(icon_size, icon_size)
        self.icon_label.setStyleSheet("QLabel { margin-top: 0px; }")
        
        # 아이콘 로드 시 크기 적용
        if self.item_type == "sequence":
            icon_pixmap = self.load_svg_icon('sequence-icon', icon_size)
        elif self.item_type == "shot":
            icon_pixmap = self.load_svg_icon('shot-icon', icon_size)
        else:  # project
            icon_pixmap = self.load_svg_icon('project-icon', icon_size)
            
        if icon_pixmap:
            self.icon_label.setPixmap(icon_pixmap)
        
        layout.addWidget(self.icon_label)
        
        # 이름 라벨 폰트 크기 조정
        self.name_label = QLabel(str(name))
        font_size = int(14 * self.scale_factor)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                font-family: 'Segoe UI';
                font-size: {font_size}px;
                font-weight: 500;
                color: #e0e0e0;
                padding: 2px 4px;
            }}
        """)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        # 프리뷰 크기 조정
        preview_width = int(150 * self.scale_factor)
        preview_height = int(85 * self.scale_factor)
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(preview_width, preview_height)
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
        
        # 프리뷰 이미지 로드 및 크기 조정
        if preview_path:
            pixmap = QPixmap(preview_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    preview_width, 
                    preview_height,
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
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