"""새 버전 생성 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QPushButton, QLabel, QTextEdit, 
                              QFileDialog, QMessageBox, QGridLayout, QHBoxLayout)
import os

class NewVersionDialog(QDialog):
    def __init__(self, version_service, version_type, item_id, parent=None):
        super().__init__(parent)
        self.version_service = version_service
        self.version_type = version_type
        self.item_id = item_id
        self.hierarchy_info = self.get_hierarchy_info()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("새 버전 생성")
        layout = QVBoxLayout(self)
        
        # 버전 타입 표시
        type_label = QLabel(f"버전 타입: {self.get_type_display()}")
        type_label.setStyleSheet("""
            QLabel {
                color: #4A90E2;
                font-weight: bold;
                font-size: 14px;
                padding: 5px;
            }
        """)
        layout.addWidget(type_label)
        
        # 계층 구조 정보 표시
        if self.hierarchy_info:
            info_layout = QGridLayout()
            row = 0
            for key, value in self.hierarchy_info.items():
                if value:  # 값이 있는 경우만 표시
                    label = QLabel(f"{key}:")
                    value_label = QLabel(value)
                    info_layout.addWidget(label, row, 0)
                    info_layout.addWidget(value_label, row, 1)
                    row += 1
            layout.addLayout(info_layout)
        
        # 작업자 이름
        self.worker_input = QLineEdit()
        layout.addWidget(QLabel("작업자:"))
        layout.addWidget(self.worker_input)
        
        # 자동 생성된 경로 표시
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        layout.addWidget(QLabel("생성될 경로:"))
        layout.addWidget(self.path_label)
        
        # 파일 선택
        self.file_path_input = QLineEdit()
        self.file_browse_btn = QPushButton("파일 찾기...")
        self.file_browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(QLabel("작업 파일:"))
        layout.addWidget(self.file_path_input)
        layout.addWidget(self.file_browse_btn)
        
        # 프리뷰 파일 선택
        self.preview_path_input = QLineEdit()
        self.preview_browse_btn = QPushButton("프리뷰 파일 찾기...")
        self.preview_browse_btn.clicked.connect(self.browse_preview)
        layout.addWidget(QLabel("프리뷰 파일:"))
        layout.addWidget(self.preview_path_input)
        layout.addWidget(self.preview_browse_btn)
        
        # 코멘트
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(100)
        layout.addWidget(QLabel("코멘트:"))
        layout.addWidget(self.comment_input)
        
        # 버튼
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("버전 생성")
        self.create_button.clicked.connect(self.create_version)
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 초기 경로 업데이트
        self.update_version_path()

    def get_hierarchy_info(self):
        """계층 구조 정보 조회"""
        try:
            if self.version_type == 'project':
                project = self.version_service.project_service.get_project(self.item_id)
                return {'프로젝트': project[1] if project else None}
            elif self.version_type == 'sequence':
                sequence = self.version_service.project_service.get_sequence(self.item_id)
                if sequence:
                    project = self.version_service.project_service.get_project(sequence[1])
                    return {
                        '프로젝트': project[1] if project else None,
                        '시퀀스': sequence[2]
                    }
            elif self.version_type == 'shot':
                shot = self.version_service.project_service.get_shot(self.item_id)
                if shot:
                    sequence = self.version_service.project_service.get_sequence(shot[1])
                    if sequence:
                        project = self.version_service.project_service.get_project(sequence[1])
                        return {
                            '프로젝트': project[1] if project else None,
                            '시퀀스': sequence[2],
                            '샷': shot[2]
                        }
            return None
        except Exception as e:
            self.logger.error(f"계층 구조 정보 조회 실패: {str(e)}")
            return None

    def get_type_display(self):
        """버전 타입 표시 텍스트"""
        return {
            'project': '프로젝트 버전',
            'sequence': '시퀀스 버전',
            'shot': '샷 버전'
        }.get(self.version_type, '알 수 없는 타입')

    def update_version_path(self):
        """버전 경로 업데이트"""
        try:
            if not self.hierarchy_info:
                return

            next_version = self.version_service.get_next_version_number(
                self.version_type, self.item_id
            )
            
            version_path = self.version_service.get_version_path(
                self.version_type,
                self.hierarchy_info.get('프로젝트'),
                self.hierarchy_info.get('시퀀스'),
                self.hierarchy_info.get('샷'),
                next_version
            )
            
            if version_path:
                self.path_label.setText(version_path)
                self.path_label.setStyleSheet("color: #4A90E2;")
        except Exception as e:
            self.logger.error(f"경로 업데이트 실패: {str(e)}")
            self.path_label.setText("경로 생성 실패")
            self.path_label.setStyleSheet("color: #FF6B6B;")

    def create_version(self):
        """버전 생성"""
        worker_name = self.worker_input.text().strip()
        if not worker_name:
            QMessageBox.warning(self, "경고", "작업자 이름을 입력해주세요.")
            return
            
        try:
            # 경로 생성
            version_path = self.path_label.text()
            os.makedirs(version_path, exist_ok=True)
            
            success = self.version_service.create_version(
                version_type=self.version_type,
                id_value=self.item_id,
                worker_name=worker_name,
                file_path=self.file_path_input.text(),
                preview_path=self.preview_path_input.text(),
                comment=self.comment_input.toPlainText(),
                render_path=version_path
            )
            
            if success:
                self.accept()
            else:
                QMessageBox.critical(self, "오류", "버전 생성에 실패했습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"버전 생성 실패: {str(e)}")