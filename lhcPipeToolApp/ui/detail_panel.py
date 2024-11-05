"""디테일 패널"""
import os, subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QMessageBox, QHBoxLayout,
    QScrollArea, QFrame, QGridLayout, QLineEdit, QPushButton, QApplication, QSizePolicy
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

        # 프리뷰 프레임
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.StyledPanel)
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
            }
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # 프리뷰 레이블
        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(300)  # 고정 높이 설정
        self.preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)  # 수평 확장, 수직 고정
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #15151e;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_frame)

        # 구분선 추가
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
            QFrame {
                border: none;
                background-color: #2d2d3d;
                height: 1px;
            }
        """)
        layout.addWidget(line)

        # 정보 영역 프레임
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(10)

        # 상태 표시
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: 500;
                color: #e0e0e0;
                background-color: #15151e;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
            }
        """)
        info_layout.addWidget(self.status_label)

        # 코멘트 영역
        self.comment_edit = QTextEdit()
        self.comment_edit.setReadOnly(True)
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setStyleSheet("""
            QTextEdit {
                background-color: #15151e;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 14px;
                padding: 5px;
            }
        """)
        info_layout.addWidget(self.comment_edit)

        # 상세 정보 필드들
        fields_widget = QWidget()
        fields_layout = QVBoxLayout(fields_widget)
        fields_layout.setSpacing(5)
        fields_layout.setContentsMargins(0, 0, 0, 0)

        # 정보 필드 생성
        self.info_fields = {}
        fields = ['버전', '작업자', '생성일', '경로', '렌더 경로', '프리뷰 경로']
        for field in fields:
            # 각 필드를 위한 수평 레이아웃
            field_container = QHBoxLayout()
            field_container.setSpacing(5)
            
            # 레이블
            label = QLabel(f"{field}:")
            label.setStyleSheet("""
                QLabel {
                    color: #e0e0e0;
                    font-family: 'Segoe UI';
                    font-size: 14px;
                    font-weight: 500;
                    background-color: transparent;
                    padding: 4px;
                }
            """)
            label.setFixedWidth(80)  # 레이블 너비 고정
            field_container.addWidget(label)
            
            # 텍스트 필드
            value = QLineEdit()
            value.setReadOnly(True)
            value.setStyleSheet("""
                QLineEdit {
                    background-color: #1a1a24;
                    border: 1px solid #2d2d3d;
                    border-radius: 4px;
                    color: #e0e0e0;
                    font-family: 'Segoe UI';
                    font-size: 14px;
                    padding: 5px;
                }
                
                QLineEdit:disabled {
                    background-color: #1a1a24;
                    color: #a0a0a0;
                }
            """)
            self.info_fields[field] = value
            
            if field in ['경로', '렌더 경로', '프리뷰 경로']:
                # 텍스트박스와 버튼을 위한 컨테이너
                input_container = QHBoxLayout()
                input_container.setSpacing(2)  # 버튼 간격을 더 좁게
                input_container.addWidget(value)
                
                # 버튼 추가
                copy_button = QPushButton("📋")
                copy_button.setFixedSize(24, 24)  # 버튼 크기를 더 작게
                copy_button.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1a24;
                        border: 1px solid #2d2d3d;
                        border-radius: 4px;
                        color: #e0e0e0;
                        padding: 4px;
                        font-family: 'Segoe UI';
                        font-size: 12px;
                    }
                    
                    QPushButton:hover {
                        background-color: #2d2d3d;
                    }
                    
                    QPushButton:pressed {
                        background-color: #363647;
                    }
                    
                    QPushButton:disabled {
                        background-color: #1a1a24;
                        color: #a0a0a0;
                        border: 1px solid #252532;
                    }
                """)
                copy_button.clicked.connect(lambda _, f=field: self.copy_to_clipboard(self.info_fields[f].text()))
                
                open_button = QPushButton("📁")
                open_button.setFixedSize(24, 24)  # 버튼 크기를 더 작게
                open_button.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1a24;
                        border: 1px solid #2d2d3d;
                        border-radius: 4px;
                        color: #e0e0e0;
                        padding: 4px;
                        font-family: 'Segoe UI';
                        font-size: 12px;
                    }
                    
                    QPushButton:hover {
                        background-color: #2d2d3d;
                    }
                    
                    QPushButton:pressed {
                        background-color: #363647;
                    }
                    
                    QPushButton:disabled {
                        background-color: #1a1a24;
                        color: #a0a0a0;
                        border: 1px solid #252532;
                    }
                """)
                open_button.clicked.connect(lambda _, f=field: self.open_folder(self.info_fields[f].text()))
                
                input_container.addWidget(copy_button)
                input_container.addWidget(open_button)
                field_container.addLayout(input_container)
            else:
                field_container.addWidget(value)
            
            fields_layout.addLayout(field_container)

        info_layout.addWidget(fields_widget)
        layout.addWidget(info_frame)

    def show_version_details(self, version_id):
        """버전 상세 정보 표시"""
        try:
            if version_id == -1:
                self.clear_details()
                return

            version = self.version_service.get_version_details(version_id)
            self.logger.debug(f"조회된 버전 정보: {version}")
            
            if not version:
                self.logger.warning(f"버전 정보를 찾을 수 없음 - version_id: {version_id}")
                self.clear_details()
                return

            # 프리뷰 이미지 표시
            if version.get('preview_path'):
                self.logger.debug(f"프리뷰 이미지 로드 시도: {version['preview_path']}")
                pixmap = QPixmap(version['preview_path'])
                if not pixmap.isNull():
                    # 프리뷰 레이블의 크기에 맞게 조정
                    label_size = self.preview_label.size()
                    scaled_pixmap = pixmap.scaled(
                        label_size.width(),
                        label_size.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled_pixmap)
                    self.logger.debug(f"프리뷰 이미지 크기 조정: {scaled_pixmap.size()}")
                else:
                    self.logger.warning("프리뷰 이미지 로드 실패")
                    self.preview_label.setText("프리뷰 이미지를 불러올 수 없습니다.")
            else:
                self.logger.debug("프리뷰 경로 없음")
                self.preview_label.setText("프리뷰 없음")

            # 상세 정보 업데이트
            self.status_label.setText(f"상태: {version.get('status', 'Unknown')}")
            self.comment_edit.setText(version.get('comment', ''))

            # 정보 필드 업데이트
            for field, value in {
                '버전': version.get('name', ''),
                '작업자': version.get('worker_name', ''),
                '생성일': str(version.get('created_at', '')),
                '경로': version.get('file_path', ''),
                '렌더 경로': version.get('render_path', ''),
                '프리뷰 경로': version.get('preview_path', '')
            }.items():
                self.logger.debug(f"필드 업데이트 - {field}: {value}")
                self.info_fields[field].setText(value)

        except Exception as e:
            self.logger.error(f"버전 상세 정보 표시 실패: {str(e)}", exc_info=True)

    def open_folder(self, path):
        """경로를 탐색기에서 엽니다."""
        if os.path.isfile(path):
            # 파일인 경우 상위 폴더 열기
            parent_dir = os.path.dirname(path)
            subprocess.Popen(f'explorer "{parent_dir}"')
        elif os.path.isdir(path):
            # 폴더인 경우 해당 폴더 열기
            subprocess.Popen(f'explorer "{path}"')
        else:
            QMessageBox.warning(self, "경고", "유효한 경로가 아닙니다.")

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def clear_details(self):
        """상세 정보 초기화"""
        self.preview_label.clear()
        self.preview_label.setText("버전을 선택하세요")
        self.status_label.clear()
        self.comment_edit.clear()
        for field in self.info_fields.values():
            field.clear()