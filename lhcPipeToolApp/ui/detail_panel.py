"""디테일 패널"""
import os, subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QMessageBox, QHBoxLayout,
    QFrame, QLineEdit, QPushButton, QApplication, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPixmap
from ..services.project_service import ProjectService
from ..services.version_services import (
    ShotVersionService, SequenceVersionService, ProjectVersionService
)
from ..utils.logger import setup_logger
from ..utils.db_utils import convert_date_format
from ..config.app_state import AppState

class AspectRatioWidget(QWidget):
    """16:9 비율을 유지하는 위젯"""
    def __init__(self, widget, aspect_ratio=16/9):
        super().__init__()
        self.aspect_ratio = aspect_ratio
        self.widget = widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        
        # 최소/최대 크기 설정
        self.setMinimumSize(200, 112)  # 16:9 비율 유지
        self.setMaximumSize(1920, 1080)  # 적절한 최대 크기 설정

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        height = self.height()
        
        # 현재 비율 계산
        current_ratio = width / height if height else 0
        
        if current_ratio > self.aspect_ratio:
            # 너비가 더 넓은 경우, 높이 기준으로 너비 조정
            target_width = int(height * self.aspect_ratio)
            self.widget.setGeometry((width - target_width) // 2, 0, target_width, height)
        else:
            # 높이가 더 높은 경우, 너비 기준으로 높이 조정
            target_height = int(width / self.aspect_ratio)
            self.widget.setGeometry(0, (height - target_height) // 2, width, target_height)

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
        # 각 타입별 필요한 필드 정의
        self.type_field_configs = {
            'project': {
                '이름': {'type': 'line'},
                '코멘트': {'type': 'text'},
                '상태': {'type': 'line'},
                '생성일': {'type': 'line'},
                '버전 수': {'type': 'line'}
            },
            'sequence': {
                '이름': {'type': 'line'},
                '코멘트': {'type': 'text'},
                '상태': {'type': 'line'},
                '생성일': {'type': 'line'},
                '레벨 경로': {'type': 'line', 'buttons': ['복사', '열기']},
                '샷 수': {'type': 'line'}
            },
            'shot': {
                '이름': {'type': 'line'},
                '코멘트': {'type': 'text'},
                '상태': {'type': 'line'},
                '생성일': {'type': 'line'},
                '프레임 범위': {'type': 'line'},
                '버전 수': {'type': 'line'}
            },
            'version': {
                '버전': {'type': 'line'},
                '작업자': {'type': 'line'},
                '코멘트': {'type': 'text'},
                '상태': {'type': 'line'},
                '생성일': {'type': 'line'},
                '경로': {'type': 'line', 'buttons': ['복사', '열기']},
                '렌더 경로': {'type': 'line', 'buttons': ['복사', '열기']},
                '프리뷰 경로': {'type': 'line', 'buttons': ['복사', '열기']}
            }
        }
        
        self.setup_ui()

        # 이벤트 필터 설치
        self.preview_label.installEventFilter(self)

        self.original_pixmap = None  # 원본 이미지 저장용 변수 추가

    def setup_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 0, 0)
        main_layout.setSpacing(10)

        # 메인 위젯
        self.item_widget = QWidget()
        item_layout = QVBoxLayout(self.item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(10)
        main_layout.addWidget(self.item_widget)

        # 아이템 정보를 감싸는 프레임
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 8px;
                padding: 1px;
            }
        """)
        item_frame_layout = QVBoxLayout(item_frame)
        item_frame_layout.setContentsMargins(15, 15, 15, 15)
        item_frame_layout.setSpacing(10)

        # 프리뷰 레이블을 위한 컨테이너
        preview_container = QWidget()
        preview_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # 프리뷰 레이블
        self.preview_label = QLabel()
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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

        # 프리뷰 레이블을 AspectRatioWidget으로 감싸기
        aspect_ratio_widget = AspectRatioWidget(self.preview_label)
        preview_layout.addWidget(aspect_ratio_widget)
        item_frame_layout.addWidget(preview_container)

        # 필드 컨테이너 생성
        fields_container = QWidget()
        fields_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        fields_layout = QVBoxLayout(fields_container)
        fields_layout.setSpacing(12)
        fields_layout.setContentsMargins(0, 0, 0, 0)

        # # 상태 필드
        # status_container = self._create_field_container("상태")
        # self.status_field = self._create_line_edit()
        # status_container.layout().addWidget(self.status_field)
        # fields_layout.addWidget(status_container)

        # # 설명/코멘트 필드
        # comment_container = self._create_field_container("설명")
        # self.comment_field = self._create_text_edit()
        # comment_container.layout().addWidget(self.comment_field)
        # fields_layout.addWidget(comment_container)

        # 각 타입별 필드들을 모두 생성하고 숨김 상태로 초기화
        self.type_fields = {}
        for item_type, fields in self.type_field_configs.items():
            self.type_fields[item_type] = {}
            for field_name, field_props in fields.items():
                field_container = self._create_field_container(field_name)
                
                if field_props['type'] == 'line':
                    field_widget = self._create_line_edit()
                    input_container = QHBoxLayout()
                    input_container.setSpacing(4)
                    input_container.addWidget(field_widget)
                    
                    # 버튼 추가
                    if 'buttons' in field_props:
                        for btn_text in field_props['buttons']:
                            icon = "📋" if btn_text == "복사" else "📁"
                            btn = self._create_action_button(icon)
                            input_container.addWidget(btn)
                    
                    field_container.layout().addLayout(input_container)
                else:
                    field_widget = self._create_text_edit()
                    field_container.layout().addWidget(field_widget)
                
                self.type_fields[item_type][field_name] = {
                    'container': field_container,
                    'widget': field_widget
                }
                fields_layout.addWidget(field_container)
                field_container.hide()  # 초기에는 모든 필드를 숨김

        item_frame_layout.addWidget(fields_container)
        item_frame_layout.addStretch()
        item_layout.addWidget(item_frame)

    def _create_field_container(self, label_text):
        """필드 컨테이너 생성"""
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                color: #8e8e9a;
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: 500;
            }
        """)
        layout.addWidget(label)
        return container

    def _create_line_edit(self):
        """인 에딧 위젯 생성"""
        widget = QLineEdit()
        widget.setReadOnly(True)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        widget.setFixedHeight(32)
        widget.setStyleSheet("""
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
        return widget

    def _create_text_edit(self):
        """텍스트 에딧 위젯 생성"""
        widget = QTextEdit()
        widget.setReadOnly(True)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        widget.setFixedHeight(60)
        widget.setStyleSheet("""
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
        return widget

    def _create_action_button(self, icon_text):
        """액션 버튼 생성"""
        btn = QPushButton(icon_text)
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
        return btn

    def show_item_details(self, item_type, item_id):
        """아이템 타입별 상세 정보 표시"""
        try:
            self.logger.debug(f"아이템 상세 정보 표시 - type: {item_type}, id: {item_id}")
            
            # 모든 필드 숨기기
            for type_fields in self.type_fields.values():
                for field_data in type_fields.values():
                    field_data['container'].hide()

            # 현재 타입의 필드만 표시
            if item_type in self.type_fields:
                for field_data in self.type_fields[item_type].values():
                    field_data['container'].show()

            # 기존의 show_item_details 로직 실행
            if item_type == "project":
                self._show_project_fields(item_id)
            elif item_type == "sequence":
                self._show_sequence_fields(item_id)
            elif item_type == "shot":
                self._show_shot_fields(item_id)
            elif item_type == "version":
                self._show_version_fields(item_id)
                
        except Exception as e:
            self.logger.error(f"아이템 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def _show_project_fields(self, project_id):
        """프로젝트 필드 표시"""
        try:
            # 프로젝트 데이터 로드
            project = self.version_services["project"].get_project_details(project_id)
            if not project:
                self.logger.warning(f"프로젝트 정보를 찾을 수 없음 - project_id: {project_id}")
                self.clear_item_details()
                return

            # 필드 데이터 업데이트
            fields_data = {
                '이름': project.get('name', ''),
                '코멘트': project.get('description', ''),
                '생성일': project.get('created_at', ''),
                '상태': project.get('status', ''),
                '버전 수': str(project.get('version_count', 0))
            }
            self._update_fields_data('project', fields_data)

            # 프리뷰 표시
            if project.get('preview_path'):
                self._show_preview(project['preview_path'])
            else:
                self.preview_label.setText("프리뷰 없음")

        except Exception as e:
            self.logger.error(f"프로젝트 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def _show_sequence_fields(self, sequence_id):
        """시퀀스 필드 표시"""
        try:
            # 시퀀스 데이터 로드
            sequence = self.version_services["sequence"].get_sequence_details(sequence_id)
            if not sequence:
                self.logger.warning(f"시퀀스 정보를 찾을 수 없음 - sequence_id: {sequence_id}")
                self.clear_item_details()
                return

            # 필드 데이터 업데이트
            fields_data = {
                '이름': sequence.get('name', ''),
                '코멘트': sequence.get('description', ''),
                '레벨 경로': sequence.get('level_path', ''),
                '생성일': sequence.get('created_at', ''),
                '상태': sequence.get('status', ''),
                '샷 수': str(sequence.get('shot_count', 0))
            }
            self._update_fields_data('sequence', fields_data)

            # 프리뷰 표시
            if sequence.get('preview_path'):
                self._show_preview(sequence['preview_path'])
            else:
                self.preview_label.setText("프리뷰 없음")

        except Exception as e:
            self.logger.error(f"시퀀스 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def _show_shot_fields(self, shot_id):
        """샷 필드 표시"""
        try:
            # 샷 데이터 로드
            shot = self.version_services["shot"].get_shot_details(shot_id)
            if not shot:
                self.logger.warning(f"샷 정보를 찾을 수 없음 - shot_id: {shot_id}")
                self.clear_item_details()
                return

            # 필드 데이터 업데이트
            fields_data = {
                '이름': shot.get('name', ''),
                '코멘트': shot.get('description', ''),
                '생성일': shot.get('created_at', ''),
                '상태': shot.get('status', ''),
                '프레임 범위': f"{shot.get('start_frame', '')} - {shot.get('end_frame', '')}",
                '버전 수': str(shot.get('version_count', 0))
            }
            self._update_fields_data('shot', fields_data)

            # 프리뷰 표시
            if shot.get('preview_path'):
                self._show_preview(shot['preview_path'])
            else:
                self.preview_label.setText("프리뷰 없음")

        except Exception as e:
            self.logger.error(f"샷 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def _show_version_fields(self, version_id):
        """버전 필드 표시"""
        try:
            self.logger.debug(f"버전 상세 정보 표시 시작 - version_id: {version_id}")
            
            # 버전 데이터 로드
            version = self.version_services[self.app_state.current_item_type].get_version_details(version_id)
            self.logger.debug(f"로드된 버전 데이터: {version}")
            
            if not version:
                self.logger.warning(f"버전 정보를 찾을 수 없음 - version_id: {version_id}")
                self.clear_item_details()
                return

            # 필드 데이터 업데이트 전에 모든 필드 숨기기
            for type_fields in self.type_fields.values():
                for field_data in type_fields.values():
                    field_data['container'].hide()

            # 버전 타입의 필드만 표시
            for field_data in self.type_fields['version'].values():
                field_data['container'].show()

            # 필드 데이터 업데이트
            fields_data = {
                '버전': version.get('name', ''),
                '작업자': version.get('worker_name', ''),
                '코멘트': version.get('comment', ''),
                '생성일': convert_date_format(version.get('created_at', '')),
                '상태': version.get('status', ''),
                '경로': version.get('file_path', ''),
                '렌더 경로': version.get('render_path', ''),
                '프리뷰 경로': version.get('preview_path', '')
            }
            
            self.logger.debug(f"업데이트할 필드 데이터: {fields_data}")
            
            # 각 필드 업데이트
            for field_name, value in fields_data.items():
                if field_name in self.type_fields['version']:
                    field_widget = self.type_fields['version'][field_name]['widget']
                    if isinstance(field_widget, QTextEdit):
                        field_widget.setPlainText(str(value))
                    else:
                        field_widget.setText(str(value))
                    self.logger.debug(f"필드 '{field_name}' 업데이트됨: {value}")

            # 프리뷰 표시
            preview_path = version.get('preview_path')
            if preview_path and os.path.exists(preview_path):
                self._show_preview(preview_path)
                self.logger.debug(f"프리뷰 이미지 표시됨: {preview_path}")
            else:
                self.preview_label.setText("프리뷰 없음")
                self.logger.debug("프리뷰 이미지 없음")

        except Exception as e:
            self.logger.error(f"버전 상세 정보 표시 실패: {str(e)}", exc_info=True)
            self.clear_item_details()

    def _update_fields_data(self, item_type, fields_data):
        """필드 데이터 업데이트"""
        if item_type in self.type_fields:
            for field_name, value in fields_data.items():
                if field_name in self.type_fields[item_type]:
                    field_widget = self.type_fields[item_type][field_name]['widget']
                    if isinstance(field_widget, QTextEdit):
                        field_widget.setPlainText(str(value))
                    else:
                        field_widget.setText(str(value))

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
            # 원본 이미지 로드 및 저장
            self.original_pixmap = QPixmap(preview_path)
            if not self.original_pixmap.isNull():
                self._update_preview_size()
                self.preview_label.setAlignment(Qt.AlignCenter)
                self.preview_label.setScaledContents(False)
            else:
                self.logger.warning("프리뷰 이미지 로드 실패")
                self.preview_label.setText("프리뷰 이미지를 불러올 수 없습니다.")
                self.original_pixmap = None
        except Exception as e:
            self.logger.error(f"프리뷰 이미지 표시 실패: {str(e)}")
            self.preview_label.setText("프리뷰 이미지 로드 오류")
            self.original_pixmap = None

    def _update_preview_size(self):
        """프리뷰 이미지 크기 업데이트"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            label_size = self.preview_label.size()
            scaled_pixmap = self.original_pixmap.scaled(
                label_size.width(),
                label_size.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)

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
        self.preview_label.setPixmap(QPixmap())  # 기존 픽스맵 명시적 제거
        self.preview_label.setText("버전을 선택하세요")
        self.status_label.clear()
        self.comment_edit.clear()
        for field in self.info_fields.values():
            field.clear()

    def clear_item_details(self):
        """아이템 정보 초기화"""
        self.preview_label.clear()
        self.preview_label.setText("프리뷰 없음")
        self.original_pixmap = None  # 원��� 이미지도 초기화
        
        # 모든 타입의 모든 필드 초기화
        for type_fields in self.type_fields.values():
            for field_data in type_fields.values():
                field_widget = field_data['widget']
                if isinstance(field_widget, QTextEdit):
                    field_widget.setPlainText('')
                else:
                    field_widget.setText('')

    # 프리뷰 레이블의 리사이즈 이벤트 처리를 위한 이벤트 필터 추가
    def eventFilter(self, obj, event):
        if obj == self.preview_label and event.type() == QEvent.Resize:
            self._update_preview_size()
        return super().eventFilter(obj, event)