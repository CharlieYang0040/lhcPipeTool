"""새 버전 생성 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QApplication,
                              QPushButton, QLabel, QTextEdit, QComboBox,
                              QFileDialog, QMessageBox, QHBoxLayout,
                              QButtonGroup, QRadioButton, QWidget)
from ..utils.logger import setup_logger
from ..utils.preview_generator import PreviewGenerator
import os
from PySide6.QtCore import Qt, QEvent, QSettings, QSize
from PySide6.QtGui import QIcon, QPixmap, QImage

class NewVersionDialog(QDialog):
    def __init__(self, version_service, shot_id, parent=None):
        super().__init__(parent)
        self.version_service = version_service
        self.shot_id = shot_id
        self.logger = setup_logger(__name__)
        self.preview_generator = PreviewGenerator()
        self.settings = QSettings('LHC', 'PipeTool')
        self.setup_ui()
        self.load_worker_history()
        
        # 다이얼로그 클릭 이벤트 설정
        self.setFocusPolicy(Qt.ClickFocus)
        self.installEventFilter(self)
        
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
        self.setWindowTitle("새 버전 생성")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # SVG 아이콘 정의 (완전한 SVG XML 형식)
        FOLDER_ICON = '''<?xml version="1.0" encoding="UTF-8"?>
            <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 7C3 5.89543 3.89543 5 5 5H9L11 7H19C20.1046 7 21 7.89543 21 9V17C21 18.1046 20.1046 19 19 19H5C3.89543 19 3 18.1046 3 17V7Z" 
                      stroke="#e0e0e0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        arrow_down = os.path.join(self.base_path, 'lhcPipeToolApp', 'resources', 'icons', 'ue-arrow-down.svg')

        # 스타일 정의
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #15151e;
            }}
            QLabel {{
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 14px;
            }}
            QLineEdit, QTextEdit {{
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 5px;
                font-family: 'Segoe UI';
                font-size: 14px;
            }}
            QComboBox {{
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 5px;
                padding-right: 25px;
                font-family: 'Segoe UI';
                font-size: 14px;
                min-height: 25px;
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox::down-arrow {{
                image: url({arrow_down.replace('\\', '/')});
            }}
            QComboBox::drop-down::after {{
                color: #e0e0e0;
                font-size: 14px;
            }}
            QComboBox:on {{
                border: 1px solid #4a4a5a;
            }}
            QComboBox QAbstractItemView {{
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                color: #e0e0e0;
                selection-background-color: #2d2d3d;
                padding: 5px;
            }}
            QPushButton {{
                background-color: #2d2d3d;
                border: none;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 8px;
                font-family: 'Segoe UI';
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #363647;
            }}
            QPushButton:pressed {{
                background-color: #404052;
            }}
            QPushButton#iconButton {{
                padding: 5px;
                width: 30px;
                height: 30px;
                background-color: transparent;
            }}
            QPushButton#iconButton:hover {{
                background-color: #2d2d3d;
            }}
            QPushButton#iconButton:pressed {{
                background-color: #363647;
            }}
            QRadioButton {{
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 13px;
                spacing: 5px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
            }}
            QLineEdit#previewPath {{
                color: #808080;
                font-size: 12px;
                background-color: #1a1a24;
                border: 1px solid #2d2d3d;
                padding: 3px;
            }}
            QLineEdit#previewPath[text=""] {{
                color: rgba(224, 224, 224, 0.5);
            }}
        """)
        
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
        
        # 파일 찾기 버튼을 SVG 아이콘으로 설정
        self.file_browse_btn = QPushButton()
        self.file_browse_btn.setObjectName("iconButton")
        self.file_browse_btn.setFixedSize(QSize(30, 30))
        
        # SVG 문자열로부터 QIcon 생성
        icon = QIcon()
        icon.addPixmap(QPixmap.fromImage(QImage.fromData(FOLDER_ICON.encode('utf-8'), 'SVG')), QIcon.Normal, QIcon.Off)
        self.file_browse_btn.setIcon(icon)
        self.file_browse_btn.setIconSize(QSize(20, 20))
        self.file_browse_btn.setToolTip("파일 찾기")
        self.file_browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_input, 1)
        file_layout.addWidget(self.file_browse_btn)
        layout.addLayout(file_layout)
        
        # 상태 선택
        status_layout = QHBoxLayout()
        status_layout.setSpacing(5)
        status_label = QLabel("상태:")
        status_label.setFixedWidth(60)
        status_layout.addWidget(status_label)
        
        self.status_group = QButtonGroup(self)
        status_widget = QWidget()
        status_buttons_layout = QHBoxLayout(status_widget)
        status_buttons_layout.setSpacing(8)
        status_buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        status_options = ['pending', 'in_progress', 'review', 'approved', 'rejected']
        for i, status in enumerate(status_options):
            radio = QRadioButton(status)
            if i == 0:
                radio.setChecked(True)
            self.status_group.addButton(radio, i)
            status_buttons_layout.addWidget(radio)
        
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
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 모든 QLineEdit 위젯에 포커스 정책 설정
        self.worker_input.setFocusPolicy(Qt.ClickFocus)
        self.file_path_input.setFocusPolicy(Qt.ClickFocus)
        self.preview_path_input.setFocusPolicy(Qt.ClickFocus)
        self.comment_input.setFocusPolicy(Qt.ClickFocus)
        
        # Tab 순서 설정
        self.setTabOrder(self.worker_input, self.file_path_input)
        self.setTabOrder(self.file_path_input, self.file_browse_btn)
        self.setTabOrder(self.file_browse_btn, self.comment_input)
        self.setTabOrder(self.comment_input, self.create_button)
        self.setTabOrder(self.create_button, self.cancel_button)
        
        # 상태 라디오 버튼들 간의 Tab 순서 설정
        status_buttons = self.status_group.buttons()
        for i in range(len(status_buttons)-1):
            self.setTabOrder(status_buttons[i], status_buttons[i+1])
        
        # 마지막 라디오 버튼에서 코멘트로 이동
        if status_buttons:
            self.setTabOrder(status_buttons[-1], self.comment_input)

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
        file_path = os.path.normpath(self.file_path_input.text().strip())
        
        if not worker_name:
            QMessageBox.warning(self, "경고", "작업자 이름을 입력해주세요!")
            return
            
        if not file_path:
            QMessageBox.warning(self, "경고", "파일을 선택해주세요!")
            return
        
        # 상태 가져오기
        status = self.status_group.checkedButton().text()
        
        # 프리뷰 경로가 비어있으면 자동 생성 시도
        preview_path = os.path.normpath(self.preview_path_input.text().strip())
        if not preview_path:
            preview_path = self.preview_generator.create_preview(file_path)
        
        # 작업자 히스토리 저장
        self.save_worker_history(worker_name)
        
        # TODO item_type에 따라 버전 생성
        success = self.version_service.create_version(
            shot_id=self.shot_id,
            worker_name=worker_name,
            file_path=file_path,
            preview_path=preview_path,
            comment=self.comment_input.toPlainText(),
            status=status
        )
        
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "오류", "버전 생성에 실패했습니다!")