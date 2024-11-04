"""디테일 패널"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, 
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from ..services.version_service import VersionService
from ..utils.logger import setup_logger

class DetailPanel(QWidget):
    def __init__(self, db_connector):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.version_service = VersionService(db_connector)
        self.setup_ui()

    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 버전 타입 표시 라벨 추가
        self.type_label = QLabel()
        self.type_label.setStyleSheet("""
            QLabel {
                color: #4A90E2;
                font-weight: bold;
                font-size: 14px;
                padding: 5px;
                background-color: #252525;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.type_label)

        # 프리뷰 영역
        self.preview_label = QLabel()
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
            }
        """)
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_label)

        # 상태 표시
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                font-weight: bold;
                color: #ffffff;
                background-color: #2d2d2d;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.status_label)

        # 코멘트 영역
        self.comment_edit = QTextEdit()
        self.comment_edit.setReadOnly(True)
        self.comment_edit.setMaximumHeight(80)  # 3줄 정도의 높이
        self.comment_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                color: #ffffff;
                padding: 5px;
            }
        """)
        layout.addWidget(self.comment_edit)

        # 스크롤 가능한 정보 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
        """)

        # 정보 표시 위젯
        info_widget = QWidget()
        self.info_layout = QGridLayout(info_widget)
        self.info_layout.setColumnStretch(1, 1)
        
        # 스타일 정의
        label_style = """
            QLabel {
                color: #888888;
                padding: 5px;
            }
        """
        value_style = """
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                color: #ffffff;
                padding: 5px;
            }
        """
        
        # 정보 필드 수정
        self.info_fields = {}
        fields = [
            '버전', '작업자', '생성일', 
            '소스 경로', '렌더 경로', '프리뷰 경로',
            '프로젝트', '시퀀스', '샷'  # 계층 구조 정보 추가
        ]
        
        for i, field in enumerate(fields):
            label = QLabel(f"{field}:")
            label.setStyleSheet(label_style)
            value = QTextEdit()
            value.setReadOnly(True)
            value.setMaximumHeight(30)
            value.setStyleSheet(value_style)
            self.info_layout.addWidget(label, i, 0)
            self.info_layout.addWidget(value, i, 1)
            self.info_fields[field] = value

        scroll_area.setWidget(info_widget)
        layout.addWidget(scroll_area)

    def show_version_details(self, version_id):
        """버전 상세 정보 표시"""
        try:
            if version_id == -1:
                self.clear_details()
                return

            version = self.version_service.get_version_details(version_id)
            if not version:
                self.clear_details()
                return

            # 버전 타입 표시
            type_text = {
                'project': '프로젝트 버전',
                'sequence': '시퀀스 버전',
                'shot': '샷 버전'
            }.get(version.get('version_type'), '알 수 없는 타입')
            self.type_label.setText(type_text)

            # 프리뷰 이미지 표시
            if version.get('preview_path'):
                pixmap = QPixmap(version['preview_path'])
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.preview_label.width(),
                        self.preview_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled_pixmap)
                else:
                    self.preview_label.setText("프리뷰 이미지를 불러올 수 없습니다.")
            else:
                self.preview_label.setText("프리뷰 없음")

            # 상태 표시
            status_text = version.get('status', 'Unknown')
            status_color = {
                'pending': '#FFA500',
                'in_progress': '#4A90E2',
                'completed': '#50C878',
                'error': '#FF6B6B'
            }.get(status_text.lower(), '#FFFFFF')
            
            self.status_label.setText(f"상태: {status_text}")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    padding: 5px;
                    font-weight: bold;
                    color: {status_color};
                    background-color: #2d2d2d;
                    border-radius: 3px;
                }}
            """)

            # 코멘트 표시
            self.comment_edit.setText(version.get('comment', ''))

            # 계층 구조 정보 표시
            hierarchy_info = self.version_service.get_version_hierarchy(version_id)
            
            # 정보 필드 업데이트
            self.info_fields['버전'].setText(version.get('name', ''))
            self.info_fields['작업자'].setText(version.get('worker_name', ''))
            self.info_fields['생성일'].setText(str(version.get('created_at', '')))
            self.info_fields['소스 경로'].setText(version.get('file_path', ''))
            self.info_fields['렌더 경로'].setText(version.get('render_path', ''))
            self.info_fields['프리뷰 경로'].setText(version.get('preview_path', ''))
            
            # 계층 구조 정보 업데이트
            if hierarchy_info:
                self.info_fields['프로젝트'].setText(hierarchy_info.get('project_name', ''))
                self.info_fields['시퀀스'].setText(hierarchy_info.get('sequence_name', ''))
                self.info_fields['샷'].setText(hierarchy_info.get('shot_name', ''))

        except Exception as e:
            self.logger.error(f"버전 상세 정보 표시 실패: {str(e)}", exc_info=True)

    def clear_details(self):
        """상세 정보 초기화"""
        self.type_label.clear()
        self.preview_label.clear()
        self.preview_label.setText("버전을 선택하세요")
        self.status_label.clear()
        self.comment_edit.clear()
        for field in self.info_fields.values():
            field.clear()