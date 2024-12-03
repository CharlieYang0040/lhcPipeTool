"""새 버전 생성 다이얼로그"""
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QApplication,
                              QPushButton, QLabel, QTextEdit, QComboBox,
                              QFileDialog, QMessageBox, QHBoxLayout,
                              QButtonGroup, QRadioButton, QWidget)
from PySide6.QtCore import Qt, QEvent, QSettings, QTimer
from PySide6.QtGui import QIcon

from ..utils.logger import setup_logger
from ..utils.preview_generator import PreviewGenerator
from ..services.version_services import (
    ShotVersionService, SequenceVersionService, ProjectVersionService
)
from ..services.file_manage_service import FileManageService
from ..styles.components import get_dialog_style, get_button_style

class NewVersionDialog(QDialog):
    def __init__(self, db_connector, project_tree, item_id, item_type, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.item_type = item_type
        self.logger = setup_logger(__name__)
        self.preview_generator = PreviewGenerator()
        self.settings = QSettings('LHC', 'PipeTool')
        self.project_tree = project_tree
        self.file_manager = FileManageService(db_connector)
        self.version_services = {
            "shot": ShotVersionService(db_connector, self.logger),
            "sequence": SequenceVersionService(db_connector, self.logger),
            "project": ProjectVersionService(db_connector, self.logger)
        }
        
        self.setup_ui()
        self.load_worker_history()
        
        # 다이얼로그 클릭 이벤트 설정
        self.setFocusPolicy(Qt.ClickFocus)
        self.installEventFilter(self)
        
        # 레이아웃 설정 후 탭 순서 설정
        self.setup_tab_order()
        
    def eventFilter(self, obj, event):
        """이벤트 필터"""
        if obj == self and event.type() == QEvent.MouseButtonPress:
            # 현재 포커스된 위젯이 있다면 포커스 해제
            focused_widget = QApplication.focusWidget()
            if focused_widget:
                focused_widget.clearFocus()
            # 다이얼로그 자체에 포커스 설정
            self.setFocus()
            return True
        return super().eventFilter(obj, event)
        
    def setup_ui(self):
        self.logger.debug(f"item_type: {self.item_type}")
        if self.item_type == "project":
            self.setWindowTitle("새 프로젝트 버전 생성")
        elif self.item_type == "sequence":
            self.setWindowTitle("새 시퀀스 버전 생성")
        else:  # shot
            self.setWindowTitle("새 샷 버전 생성")
            
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 중앙화된 스타일 적용
        self.setStyleSheet(get_dialog_style())
        
        # 작업자 이름
        worker_layout = QHBoxLayout()
        worker_layout.setSpacing(10)
        worker_label = QLabel("작업자:")
        worker_label.setFixedWidth(60)
        self.worker_input = QComboBox()
        self.worker_input.setEditable(True)
        self.worker_input.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        self.worker_input.setMinimumWidth(200)
                
        worker_layout.addWidget(worker_label)
        worker_layout.addWidget(self.worker_input, 1)
        layout.addLayout(worker_layout)
        
        # 파일 선택
        file_layout = QHBoxLayout()
        file_layout.setSpacing(10)
        file_label = QLabel("파일:")
        file_label.setFixedWidth(60)
        
        self.file_path_input = QLineEdit()
        self.file_path_input.editingFinished.connect(self.handle_file_path_change)
        
        # 파일 브라우저 버튼
        self.file_browse_btn = QPushButton()
        self.file_browse_btn.setObjectName("iconButton")
        self.file_browse_btn.setFixedSize(30, 30)
        self.file_browse_btn.setIcon(QIcon("lhcPipeToolApp/resources/icons/folder-icon.svg"))
        self.file_browse_btn.setStyleSheet(get_button_style(min_width=13))
        self.file_browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_input, 1)
        file_layout.addWidget(self.file_browse_btn)
        layout.addLayout(file_layout)
        
        # 상태 선택
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        status_label = QLabel("상태:")
        status_label.setFixedWidth(60)
        
        # 상태 라디오 버튼 그룹
        status_widget = QWidget()
        status_buttons_layout = QHBoxLayout(status_widget)
        status_buttons_layout.setSpacing(15)
        status_buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_group = QButtonGroup(self)
        statuses = [
            "pending", "in_progress", "review", 
            "approved", "hold", "omitted"
            ]
        
        for i, status in enumerate(statuses):
            radio = QRadioButton(status)
            if i == 0:
                radio.setChecked(True)
            self.status_group.addButton(radio, i)
            status_buttons_layout.addWidget(radio)
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(status_widget, 1)
        layout.addLayout(status_layout)
        
        # 프리뷰 파일 경로
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(10)
        preview_label = QLabel("프리뷰:")
        preview_label.setFixedWidth(60)
        self.preview_path_input = QLineEdit()
        self.preview_path_input.setObjectName("previewPath")
        self.preview_path_input.setReadOnly(True)
        self.preview_path_input.setPlaceholderText("자동으로 생성됩니다.")
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_path_input, 1)
        layout.addLayout(preview_layout)
        
        # 코멘트
        comment_layout = QVBoxLayout()
        comment_layout.setSpacing(5)
        comment_label = QLabel("코멘트:")
        self.comment_input = QTextEdit()
        self.comment_input.setMinimumHeight(80)
        self.comment_input.setMaximumHeight(120)
        comment_layout.addWidget(comment_label)
        comment_layout.addWidget(self.comment_input)
        layout.addLayout(comment_layout)
        
        # 버튼 컨테이너
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 확인/취소 버튼
        self.create_button = QPushButton("버전 생성")
        self.create_button.setMinimumWidth(100)
        self.create_button.clicked.connect(self.create_version)
        self.create_button.setStyleSheet(get_button_style())
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(get_button_style())
        
        button_layout.addStretch()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 모든 QLineEdit 위젯에 포커스 정책 설정
        self.worker_input.setFocusPolicy(Qt.ClickFocus)
        self.file_path_input.setFocusPolicy(Qt.ClickFocus)
        self.preview_path_input.setFocusPolicy(Qt.ClickFocus)
        self.comment_input.setFocusPolicy(Qt.ClickFocus)

    def setup_tab_order(self):
        """탭 순서 설정"""
        # 약간의 딜레이 후 탭 순서 설정
        QTimer.singleShot(100, self._set_tab_order)

    def _set_tab_order(self):
        """실제 탭 순서 설정"""
        self.worker_input.setFocusPolicy(Qt.StrongFocus)
        self.file_path_input.setFocusPolicy(Qt.StrongFocus)
        self.file_browse_btn.setFocusPolicy(Qt.StrongFocus)
        self.comment_input.setFocusPolicy(Qt.StrongFocus)
        self.create_button.setFocusPolicy(Qt.StrongFocus)
        self.cancel_button.setFocusPolicy(Qt.StrongFocus)
        
        # 상태 라디오 버튼들의 포커스 정책 설정
        for button in self.status_group.buttons():
            button.setFocusPolicy(Qt.StrongFocus)
        
        # 탭 순서 설정
        self.setTabOrder(self.worker_input, self.file_path_input)
        self.setTabOrder(self.file_path_input, self.file_browse_btn)
        self.setTabOrder(self.file_browse_btn, self.status_group.buttons()[0])
        
        # 라디오 버튼들 간의 탭 순서
        status_buttons = self.status_group.buttons()
        for i in range(len(status_buttons)-1):
            self.setTabOrder(status_buttons[i], status_buttons[i+1])
        
        # 마지막 라디오 버튼에서 코멘트로
        if status_buttons:
            self.setTabOrder(status_buttons[-1], self.comment_input)
        
        self.setTabOrder(self.comment_input, self.create_button)
        self.setTabOrder(self.create_button, self.cancel_button)

    def load_worker_history(self):
        """작업자 히스토리 로드"""
        try:
            workers = self.settings.value('worker_history', [])
            if workers:
                self.worker_input.addItems(workers)
        except Exception as e:
            self.logger.error(f"작업자 히스토리 로드 실패: {str(e)}")

    def save_worker_history(self, worker_name):
        """작업자 히스토리 저장"""
        try:
            workers = self.settings.value('worker_history', [])
            if not isinstance(workers, list):
                workers = []
            
            # 중복 제거 및 최근 항목을 앞으로
            if worker_name in workers:
                workers.remove(worker_name)
            workers.insert(0, worker_name)
            
            # 최대 10개까지만 저장
            workers = workers[:10]
            self.settings.setValue('worker_history', workers)
            
        except Exception as e:
            self.logger.error(f"작업자 히스토리 저장 실패: {str(e)}")

    def handle_file_path_change(self):
        """파일 경로 입력 완료 처리"""
        try:
            file_path = self.file_path_input.text().strip()
            if file_path and os.path.exists(file_path):  # 파일이 실제로 존재하는 경우에만
                self.logger.debug(f"파일 경로 입력 완료: {file_path}")
                # 프리뷰 자동 생성
                preview_path = self.preview_generator.create_preview(file_path)
                if preview_path:
                    self.preview_path_input.setText(preview_path)
                    
        except Exception as e:
            self.logger.error(f"파일 경로 처리 중 오류 발생: {str(e)}")
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "파일 택", "", 
            "모든 파일 (*.*);;비디오 파일 (*.mp4 *.mov *.avi);;이미지 파일 (*.jpg *.png *.exr *.dpx)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            # 프리뷰 자동 생성
            preview_path = self.preview_generator.create_preview(file_path)
            if preview_path:
                self.preview_path_input.setText(preview_path)
            else:
                QMessageBox.warning(self, "경고", "프리뷰 생성에 실패했습니다.")

    def browse_preview(self):
        preview_path, _ = QFileDialog.getOpenFileName(
            self, "Select Preview File", "", "Image Files (*.jpg *.png);;Video Files (*.mp4 *.mov)"
        )
        if preview_path:
            self.preview_path_input.setText(preview_path)
            
    def create_version(self):
        worker_name = self.worker_input.currentText().strip()
        source_file = os.path.normpath(self.file_path_input.text().strip())
        
        if not worker_name:
            QMessageBox.warning(self, "경고", "작업자 이름을 입력해주세요!")
            return
            
        if not source_file:
            QMessageBox.warning(self, "경고", "파일을 선택해주세요!")
            return
            
        if not os.path.exists(source_file):
            QMessageBox.warning(self, "경고", "선택한 파일이 존재하지 않습니다!")
            return

        try:
            # 파일 처리
            file_info = self.file_manager.process_version_file(
                self.item_type,
                self.item_id,
                source_file
            )
            
            # 상태 가져오기
            status = self.status_group.checkedButton().text()
            
            # 프리뷰 경로가 비어있으면 자동 생성 시도
            preview_path = os.path.normpath(self.preview_path_input.text().strip())
            if not preview_path:
                preview_path = self.preview_generator.create_preview(file_info['file_path'])
            
            # 작업자 히스토리 저장
            self.save_worker_history(worker_name)
            
            # 버전 생성
            success = self.version_services[self.item_type].create_version(
                item_id=self.item_id,
                version_number=file_info['version_number'],
                worker_name=worker_name,
                file_path=file_info['file_path'],
                render_path=source_file,
                preview_path=preview_path,
                comment=self.comment_input.toPlainText(),
                status=status
            )

            if success:
                self.project_tree.load_projects()
                self.accept()
            else:
                QMessageBox.critical(self, "오류", "버전 생성에 실패했습니다!")
                
        except Exception as e:
            self.logger.error(f"버전 생성 중 오류 발생: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", f"버전 생성 중 오류가 발생했습니다: {str(e)}")