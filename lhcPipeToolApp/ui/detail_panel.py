"""디테일 패널"""
import os, subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QMessageBox, QHBoxLayout,
    QFrame, QLineEdit, QPushButton, QApplication, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from ..services.project_service import ProjectService
from ..services.version_services import (
    ShotVersionService, SequenceVersionService, ProjectVersionService
)
from ..utils.logger import setup_logger
from ..config.app_state import AppState

class DetailPanel(QWidget):
    def __init__(self, db_connector):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.db_connector = db_connector
        self.project_service = ProjectService(db_connector)
        self.version_services = {
            "shot": ShotVersionService(db_connector, self.logger),
            "sequence": SequenceVersionService(db_connector, self.logger),
            "project": ProjectVersionService(db_connector, self.logger)
        }
        self.app_state = AppState()
        # type_fields를 여기서 정의
        self.type_fields = {
            'project': ['이름', '설명', '상태', '생성일', '버전 수'],
            'sequence': ['이름', '프로젝트', '상태', '생성일', '레벨 경로', '샷 수'],
            'shot': ['이름', '시퀀스', '상태', '생성일', '프레임 범위', '버전 수']
        }
        self.setup_ui()

    def setup_ui(self):
        """UI 초기화"""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # 스택 위젯 추가
        self.stack_widget = QStackedWidget()
        main_layout.addWidget(self.stack_widget)

        # 1. 버전 정보 위젯
        self.version_widget = QWidget()
        version_layout = QVBoxLayout(self.version_widget)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(10)

        # 버전 정보를 감싸는 프레임
        version_frame = QFrame()
        version_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        version_frame_layout = QVBoxLayout(version_frame)
        version_frame_layout.setContentsMargins(15, 15, 15, 15)
        version_frame_layout.setSpacing(10)

        # 프리뷰 레이블
        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(300)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #15151e;
                border: 1px solid #2d2d3d;
                border-radius: 6px;
                color: #8e8e9a;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
        """)
        version_frame_layout.addWidget(self.preview_label)

        # 버전 위젯의 나머지 필드들을 version_frame_layout에 추가
        # 버전 정보 필드 컨테이너
        fields_container = QWidget()
        fields_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        fields_layout = QVBoxLayout(fields_container)
        fields_layout.setSpacing(12)
        fields_layout.setContentsMargins(0, 0, 0, 0)

        # 상태 표시
        status_container = QWidget()
        status_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)

        status_label = QLabel("상태")
        status_label.setStyleSheet("""
            QLabel {
                color: #8e8e9a;
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: 500;
            }
        """)
        
        self.status_label = QLineEdit()
        self.status_label.setReadOnly(True)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.status_label.setFixedHeight(32)
        self.status_label.setStyleSheet("""
            QLineEdit {
                background-color: #15151e;
                border: 1px solid #2d2d3d;
                border-radius: 6px;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 13px;
                padding: 4px 8px;
            }
        """)
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_label)
        fields_layout.addWidget(status_container)

        # 코멘트 영역
        comment_container = QWidget()
        comment_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        comment_layout = QVBoxLayout(comment_container)
        comment_layout.setContentsMargins(0, 0, 0, 0)
        comment_layout.setSpacing(4)

        comment_label = QLabel("코멘트")
        comment_label.setStyleSheet("""
            QLabel {
                color: #8e8e9a;
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: 500;
            }
        """)
        
        self.comment_edit = QTextEdit()
        self.comment_edit.setReadOnly(True)
        self.comment_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.comment_edit.setFixedHeight(60)
        self.comment_edit.setStyleSheet("""
            QTextEdit {
                background-color: #15151e;
                border: 1px solid #2d2d3d;
                border-radius: 6px;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 13px;
                padding: 8px;
            }
        """)
        
        comment_layout.addWidget(comment_label)
        comment_layout.addWidget(self.comment_edit)
        fields_layout.addWidget(comment_container)

        # 정보 필드들
        self.info_fields = {}
        fields = ['버전', '작업자', '생성일', '경로', '렌더 경로', '프리뷰 경로']
        
        for field in fields:
            field_container = QWidget()
            field_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            field_layout = QVBoxLayout(field_container)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(4)

            # 레이블
            label = QLabel(field)
            label.setStyleSheet("""
                QLabel {
                    color: #8e8e9a;
                    font-family: 'Segoe UI';
                    font-size: 12px;
                    font-weight: 500;
                }
            """)
            field_layout.addWidget(label)

            # 입력 필드와 버튼을 위한 컨테이너
            input_container = QHBoxLayout()
            input_container.setSpacing(4)

            # 텍스트 필드
            value = QLineEdit()
            value.setReadOnly(True)
            value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            value.setFixedHeight(32)
            value.setStyleSheet("""
                QLineEdit {
                    background-color: #15151e;
                    border: 1px solid #2d2d3d;
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-family: 'Segoe UI';
                    font-size: 13px;
                    padding: 4px 8px;
                }
            """)
            self.info_fields[field] = value
            input_container.addWidget(value)

            # 경로 관련 필드에 버튼 추가
            if field in ['경로', '렌더 경로', '프리뷰 경로']:
                for btn_text, btn_icon in [("복사", "📋"), ("열기", "📁")]:
                    btn = QPushButton(btn_icon)
                    btn.setFixedSize(26, 26)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2d2d3d;
                            border: none;
                            border-radius: 4px;
                            color: #e0e0e0;
                            font-size: 12px;
                            padding: 4px;
                        }
                        QPushButton:hover {
                            background-color: #3d3d4d;
                        }
                        QPushButton:pressed {
                            background-color: #4a4a5a;
                        }
                    """)
                    input_container.addWidget(btn)

            field_layout.addLayout(input_container)
            fields_layout.addWidget(field_container)

        version_frame_layout.addWidget(fields_container)
        version_frame_layout.addStretch()  # 남는 공간을 하단으로 밀어냄

        version_layout.addWidget(version_frame)

        # 2. 아이템 정보 위젯
        self.item_widget = QWidget()
        item_layout = QVBoxLayout(self.item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(12)

        # 아이템 정보를 감싸는 프레임
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        item_frame_layout = QVBoxLayout(item_frame)
        item_frame_layout.setContentsMargins(15, 15, 15, 15)
        item_frame_layout.setSpacing(12)

        # 아이템 위젯의 필드들을 item_frame_layout에 추가
        self.item_fields = {}
        for field in set().union(*self.type_fields.values()):
            field_container = QWidget()
            field_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            field_layout = QVBoxLayout(field_container)
            field_layout.setSpacing(4)
            field_layout.setContentsMargins(0, 0, 0, 0)

            # 레이블
            label = QLabel(f"{field}")
            label.setStyleSheet("""
                QLabel {
                    color: #8e8e9a;
                    font-family: 'Segoe UI';
                    font-size: 12px;
                    font-weight: 500;
                }
            """)
            field_layout.addWidget(label)

            # 입력 필드와 버튼을 위한 컨테이너
            input_container = QHBoxLayout()
            input_container.setSpacing(4)

            # 값 입력 위젯 생성
            if field == '설명':
                value = QTextEdit()
                value.setReadOnly(True)
                value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                value.setFixedHeight(60)
                value.setStyleSheet("""
                    QTextEdit {
                        background-color: #15151e;
                        border: 1px solid #2d2d3d;
                        border-radius: 6px;
                        color: #e0e0e0;
                        font-family: 'Segoe UI';
                        font-size: 13px;
                        padding: 8px;
                    }
                """)
            else:
                value = QLineEdit()
                value.setReadOnly(True)
                value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                value.setFixedHeight(32)
                value.setStyleSheet("""
                    QLineEdit {
                        background-color: #15151e;
                        border: 1px solid #2d2d3d;
                        border-radius: 6px;
                        color: #e0e0e0;
                        font-family: 'Segoe UI';
                        font-size: 13px;
                        padding: 4px 8px;
                    }
                """)

            input_container.addWidget(value)

            # 레벨 경로에 대한 버튼 추가
            if field == '레벨 경로':
                for btn_text, btn_icon in [("복사", "📋"), ("열기", "📁")]:
                    btn = QPushButton(btn_icon)
                    btn.setFixedSize(26, 26)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2d2d3d;
                            border: none;
                            border-radius: 4px;
                            color: #e0e0e0;
                            font-size: 12px;
                            padding: 4px;
                        }
                        QPushButton:hover {
                            background-color: #3d3d4d;
                        }
                        QPushButton:pressed {
                            background-color: #4a4a5a;
                        }
                    """)
                    input_container.addWidget(btn)

            field_layout.addLayout(input_container)
            item_frame_layout.addWidget(field_container)
            self.item_fields[field] = value

        item_frame_layout.addStretch()
        item_layout.addWidget(item_frame)

        # 스택 위젯에 두 페이지 추가
        self.stack_widget.addWidget(self.version_widget)
        self.stack_widget.addWidget(self.item_widget)

    def setup_item_fields(self, layout):
        """아이템 정보 필드 설정"""
        # 타입별 표시할 필드를 순서대로 정의
        self.type_fields = {
            'project': [
                '이름',
                '설명',
                '상태',
                '생성일',
                '버전 수'
            ],
            'sequence': [
                '이름',
                '프로젝트',
                '상태',
                '생성일',
                '레벨 경로',
                '샷 수'
            ],
            'shot': [
                '이름',
                '시퀀스',
                '상태',
                '생성일',
                '프레임 범위',
                '버전 수'
            ]
        }

        # 필드별 특성 정의 - 더 일관된 크기로 조정
        field_properties = {
            # 기본 필드 (모든 타입에 공통)
            '이름': {'width': 250, 'multiline': False},
            '설명': {'width': 250, 'multiline': True, 'height': 60},
            '상태': {'width': 250, 'multiline': False},
            '생성일': {'width': 250, 'multiline': False},
            
            # 특수 필드
            '프로젝트': {'width': 250, 'multiline': False},
            '시퀀스': {'width': 250, 'multiline': False},
            '레벨 경로': {'width': 250, 'multiline': False, 'has_buttons': True},
            
            # 숫자 관련 필드
            '버전 수': {'width': 250, 'multiline': False},
            '샷 수': {'width': 250, 'multiline': False},
            '프레임 범위': {'width': 250, 'multiline': False}
        }

        # 섹션 프레임 설정
        section_frame = QFrame()
        section_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        section_layout = QVBoxLayout(section_frame)
        section_layout.setSpacing(12)
        section_layout.setContentsMargins(15, 15, 15, 15)

        # 필드들을 담을 컨테이너
        fields_container = QWidget()
        fields_layout = QVBoxLayout(fields_container)
        fields_layout.setSpacing(12)
        fields_layout.setContentsMargins(0, 0, 0, 0)

        # 모든 가능한 필드에 대해 위젯 생성
        for field in set().union(*self.type_fields.values()):
            field_container = QWidget()
            field_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # 수직 크기 고정
            field_layout = QVBoxLayout(field_container)
            field_layout.setSpacing(4)
            field_layout.setContentsMargins(0, 0, 0, 0)

            # 레이블 생성
            label = QLabel(f"{field}")
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # 수직 크기 고정
            label.setStyleSheet("""
                QLabel {
                    color: #8e8e9a;
                    font-family: 'Segoe UI';
                    font-size: 12px;
                    font-weight: 500;
                }
            """)
            field_layout.addWidget(label)

            # 값 입력 위젯 생성
            if field_properties[field].get('multiline', False):
                value = QTextEdit()
                value.setFixedHeight(field_properties[field]['height'])
                value.setFixedWidth(field_properties[field]['width'])
                value.setReadOnly(True)
                value.setStyleSheet("""
                    QTextEdit {
                        background-color: #15151e;
                        border: 1px solid #2d2d3d;
                        border-radius: 6px;
                        color: #e0e0e0;
                        font-family: 'Segoe UI';
                        font-size: 13px;
                        padding: 8px;
                    }
                """)
            else:
                value = QLineEdit()
                value.setReadOnly(True)
                value.setFixedWidth(field_properties[field]['width'])
                value.setFixedHeight(32)  # 높이 고정
                value.setStyleSheet("""
                    QLineEdit {
                        background-color: #15151e;
                        border: 1px solid #2d2d3d;
                        border-radius: 6px;
                        color: #e0e0e0;
                        font-family: 'Segoe UI';
                        font-size: 13px;
                        padding: 4px 8px;
                    }
                """)

            field_layout.addWidget(value)
            
            # 레벨 경로에 대한 버튼 추가
            if field_properties[field].get('has_buttons', False):
                button_container = QWidget()
                button_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # 수직 크기 고정
                button_layout = QHBoxLayout(button_container)
                button_layout.setContentsMargins(0, 4, 0, 0)
                button_layout.setSpacing(4)

                for btn_text in ["복사", "열기"]:
                    btn = QPushButton(btn_text)
                    btn.setFixedSize(60, 26)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2d2d3d;
                            border: none;
                            border-radius: 4px;
                            color: #e0e0e0;
                            font-size: 12px;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background-color: #3d3d4d;
                        }
                        QPushButton:pressed {
                            background-color: #4a4a5a;
                        }
                    """)
                    button_layout.addWidget(btn)
                
                button_layout.addStretch()
                field_layout.addWidget(button_container)

            fields_layout.addWidget(field_container)
            self.item_fields[field] = value

        # 필드 컨테이너를 섹션 레이아웃에 추가
        section_layout.addWidget(fields_container)
        
        # 남는 공간을 채우기 위한 스트레치 추가
        section_layout.addStretch()
        
        layout.addWidget(section_frame)

    def show_item_details(self, item_type, item_id):
        """아이템 타입별 상세 정보 표시"""
        try:
            self.logger.debug(f"아이템 상세 정보 표시 - type: {item_type}, id: {item_id}")
            
            # 버전이 아닌 경우 아이템 정보 페이지로 전환
            self.stack_widget.setCurrentWidget(self.item_widget)
            
            if item_type == "project":
                self.show_project_details(item_id)
            elif item_type == "sequence":
                self.show_sequence_details(item_id)
            elif item_type == "shot":
                self.show_shot_details(item_id)
                
        except Exception as e:
            self.logger.error(f"아이템 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def show_version_details(self, version_id):
        """버전 상세 정보 표시"""
        self.stack_widget.setCurrentWidget(self.version_widget)
        try:
            if version_id == -1:
                self.clear_details()
                return

            version = self.version_services[self.app_state.current_item_type].get_version_details(version_id)
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

    def show_project_details(self, project_id):
        """프로젝트 상세 정보 표시"""
        try:
            project = self.project_service.get_project_details(project_id)
            if not project:
                self.logger.warning(f"프로젝트 정보를 찾을 수 없음 - project_id: {project_id}")
                self.clear_item_details()
                return

            # 프로젝트 정보 표시
            fields_data = {
                '이름': project.get('name', ''),
                '설명': project.get('description', ''),
                '생성일': project.get('created_at', ''),
                '상태': project.get('status', ''),
                '버전 수': str(project.get('version_count', 0))
            }

            # UI 업데이트
            self._update_item_fields('project', fields_data)
            
            # 프리뷰 이미지 표시 (있는 경우)
            if project.get('preview_path'):
                self._show_preview(project['preview_path'])
            else:
                self.preview_label.setText("프리뷰 없음")

        except Exception as e:
            self.logger.error(f"프로젝트 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def show_sequence_details(self, sequence_id):
        """시퀀스 상세 정보 표시"""
        try:
            sequence = self.project_service.get_sequence_details(sequence_id)
            if not sequence:
                self.logger.warning(f"시퀀스 정보를 찾을 수 없음 - sequence_id: {sequence_id}")
                self.clear_item_details()
                return

            # 시퀀스 정보 표시
            fields_data = {
                '이름': sequence.get('name', ''),
                '프로젝트': sequence.get('project_name', ''),
                '레벨 경로': sequence.get('level_path', ''),
                '생성일': sequence.get('created_at', ''),
                '상태': sequence.get('status', ''),
                '샷 수': str(sequence.get('shot_count', 0))
            }

            # UI 업데이트
            self._update_item_fields('sequence', fields_data)
            
            # 프리뷰 이미지 표시 (있는 경우)
            if sequence.get('preview_path'):
                self._show_preview(sequence['preview_path'])
            else:
                self.preview_label.setText("프리뷰 없음")

        except Exception as e:
            self.logger.error(f"시퀀스 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def show_shot_details(self, shot_id):
        """샷 상세 정보 표시"""
        try:
            shot = self.project_service.get_shot_details(shot_id)
            if not shot:
                self.logger.warning(f"샷 정보를 찾을 수 없음 - shot_id: {shot_id}")
                self.clear_item_details()
                return

            # 샷 정보 표시
            fields_data = {
                '이름': shot.get('name', ''),
                '시퀀스': shot.get('sequence_name', ''),
                '생성일': shot.get('created_at', ''),
                '상태': shot.get('status', ''),
                '프레임 범위': f"{shot.get('start_frame', '')} - {shot.get('end_frame', '')}",
                '버전 수': str(shot.get('version_count', 0))
            }

            # UI 업데이트
            self._update_item_fields('shot', fields_data)
            
            # 프리뷰 이미지 표시 (있는 경우)
            if shot.get('preview_path'):
                self._show_preview(shot['preview_path'])
            else:
                self.preview_label.setText("프리뷰 없음")

        except Exception as e:
            self.logger.error(f"샷 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def _update_item_fields(self, item_type, fields_data):
        """아이템 필드 업데이트 헬퍼 메서드"""
        # 모든 필드를 먼저 숨김
        for field in self.item_fields:
            self.item_fields[field].parent().hide()  # 필드의 컨테이너를 숨김

        # 해당 타입의 필드만 표시
        for field in self.type_fields[item_type]:
            if field in self.item_fields:
                self.item_fields[field].parent().show()  # 필드의 컨테이너를 표시
                self.item_fields[field].setText(fields_data.get(field, ''))

    def _show_preview(self, preview_path):
        """프리뷰 이미지 표시 헬퍼 메서드"""
        try:
            pixmap = QPixmap(preview_path)
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
        except Exception as e:
            self.logger.error(f"프리뷰 이미지 표시 실패: {str(e)}")
            self.preview_label.setText("프리뷰 이미지 로드 오류")

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

    def clear_item_details(self):
        """아이템 정보 초기화"""
        for field in self.item_fields.values():
            field.clear()