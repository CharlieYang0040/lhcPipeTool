"""설정 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QPushButton, QLabel, QMessageBox, 
                              QTabWidget, QWidget, QFormLayout, 
                              QGroupBox, QHBoxLayout, QFileDialog)
import json
import os
from pathlib import Path
from ..services.project_service import ProjectService
from ..services.version_services import (ProjectVersionService, SequenceVersionService, ShotVersionService)
from ..database.table_manager import TableManager
from ..utils.logger import setup_logger

class SettingsDialog(QDialog):
    def __init__(self, db_connector, parent=None):
        super().__init__(parent)
        self.logger = setup_logger(__name__)
        self.db_connector = db_connector
        self.settings_file = "config/settings.json"
        self.load_settings()
        self.setup_ui()
        self.project_service = ProjectService(self.db_connector)
        self.version_services = {
            "project": ProjectVersionService(self.db_connector),
            "sequence": SequenceVersionService(self.db_connector),
            "shot": ShotVersionService(self.db_connector)
        }
        self.table_manager = TableManager(self.db_connector)
    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 경로 설정 탭
        path_tab = QWidget()
        path_layout = QFormLayout(path_tab)
        
        # 프로젝트 루트 경로 설정
        path_group = QGroupBox("Project Settings")
        path_group_layout = QVBoxLayout()
        
        root_layout = QHBoxLayout()
        self.project_root_input = QLineEdit(self.settings.get("project_root", ""))
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_project_root)
        import_button = QPushButton("Import Projects")
        import_button.clicked.connect(self.import_projects)
        
        root_layout.addWidget(self.project_root_input)
        root_layout.addWidget(browse_button)
        path_group_layout.addLayout(root_layout)
        path_group_layout.addWidget(import_button)
        
        path_group.setLayout(path_group_layout)
        path_layout.addRow(path_group)
        
        self.render_output_input = QLineEdit(self.settings.get("render_output", ""))
        path_layout.addRow("Render Output:", self.render_output_input)
        
        self.preview_output_input = QLineEdit(self.settings.get("preview_output", ""))
        path_layout.addRow("Preview Output:", self.preview_output_input)
        
        tab_widget.addTab(path_tab, "Paths")
        
        # 데이터베이스 설정 탭
        db_tab = QWidget()
        db_layout = QFormLayout(db_tab)
        
        self.db_host_input = QLineEdit(self.settings.get("db_host", "localhost"))
        db_layout.addRow("Database Host:", self.db_host_input)
        
        self.db_name_input = QLineEdit(self.settings.get("db_name", ""))
        db_layout.addRow("Database Name:", self.db_name_input)
        
        self.db_user_input = QLineEdit(self.settings.get("db_user", "SYSDBA"))
        db_layout.addRow("Database User:", self.db_user_input)
        
        self.db_password_input = QLineEdit(self.settings.get("db_password", ""))
        self.db_password_input.setEchoMode(QLineEdit.Password)
        db_layout.addRow("Database Password:", self.db_password_input)
        
        tab_widget.addTab(db_tab, "Database")
        
        # 버튼
        button_layout = QVBoxLayout()
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def load_settings(self):
        """설정 파일 로드"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
        except Exception as e:
            print(f"설정 로드 오류: {e}")
            self.settings = {}
            
    def save_settings(self, key=None, value=None):
        """설정 저장"""
        settings = {
            "project_root": self.project_root_input.text(),
            "render_output": self.render_output_input.text(),
            "preview_output": self.preview_output_input.text(),
            "db_host": self.db_host_input.text(),
            "db_name": self.db_name_input.text(),
            "db_user": self.db_user_input.text(),
            "db_password": self.db_password_input.text()
        }
        
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            # 데이터베이스에도 설정 저장
            cursor = self.db_connector.cursor()
            for key, value in settings.items():
                cursor.execute("""
                    UPDATE OR INSERT INTO settings (setting_key, setting_value)
                    VALUES (?, ?)
                    MATCHING (setting_key)
                """, (key, value))
            self.db_connector.commit()
            
            self.logger.info("설정 저장 성공")
            self.accept()
        except Exception as e:
            self.logger.error(f"설정 저장 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
            
    def browse_project_root(self):
        directory = QFileDialog.getExistingDirectory(self, "프로젝트 루트 디렉토리 선택")
        if directory:
            self.project_root_input.setText(directory)
            # 설정 저장
            self.save_settings('project_root', directory)
            
    def import_projects(self):
        """프로젝트 구조 임포트"""
        self.logger.info("프로젝트 구조 임포트 시작")
        
        root_path = Path(self.project_root_input.text())
        self.logger.info(f"프로젝트 루트 경로: {root_path}")
        
        if not root_path.exists():
            self.logger.warning(f"프로젝트 루트 경로가 존재하지 않음: {root_path}")
            QMessageBox.warning(self, "경고", "프로젝트 루트 경로가 존재하지 않습니다.")
            return
            
        try:
            # 프로젝트 구조 스캔
            self.logger.info("프로젝트 구조 스캔 시작")
            projects = self.scan_project_structure(root_path)
            self.logger.info(f"스캔된 프로젝트 수: {len(projects)}")
            
            # 데이터베이스에 등록
            self.logger.info("데이터베이스 등록 시작")
            for project in projects:
                self.logger.debug(f"프로젝트 등록 중: {project}")
                self.register_project(project)
                
            self.logger.info("프로젝트 구조 임포트 완료")
            QMessageBox.information(self, "성공", "프로젝트 구조를 성공적으로 임포트했습니다.")
            
        except Exception as e:
            self.logger.error(f"프로젝트 임포트 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", f"프로젝트 임포트 실패: {str(e)}")

    def scan_project_structure(self, root_path):
        """프로젝트 구조 스캔"""
        projects = []
        
        for project_dir in root_path.iterdir():
            if not project_dir.is_dir():
                continue
                
            project = {
                'name': project_dir.name,
                'path': str(project_dir),
                'sequences': []
            }
            
            # 시퀀스 스캔
            for seq_dir in project_dir.iterdir():
                if not seq_dir.is_dir():
                    continue
                    
                sequence = {
                    'name': seq_dir.name,
                    'shots': []
                }
                
                # 샷 스캔
                for shot_dir in seq_dir.iterdir():
                    if not shot_dir.is_dir():
                        continue
                        
                    shot = {
                        'name': shot_dir.name,
                        'versions': []
                    }
                    
                    # 버전 스캔
                    for version_dir in shot_dir.glob('v*'):
                        if not version_dir.is_dir():
                            continue
                            
                        try:
                            version_num = int(version_dir.name[1:])
                            shot['versions'].append({
                                'number': version_num,
                                'path': str(version_dir)
                            })
                        except ValueError:
                            continue
                            
                    sequence['shots'].append(shot)
                project['sequences'].append(sequence)
            projects.append(project)
            
        return projects

    def register_project(self, project_data):
        """프로젝트 구조를 데이터베이스에 등록"""
        # 프로젝트 생성
        project_id = self.project_service.create_project(
            name=project_data['name'],
            path=project_data['path']
        )
        
        # 시퀀스 생성
        for sequence in project_data['sequences']:
            sequence_id = self.project_service.create_sequence(
                project_id=project_id,
                name=sequence['name']
            )
            
            # 샷 생성
            for shot in sequence['shots']:
                shot_id = self.project_service.create_shot(
                    sequence_id=sequence_id,
                    name=shot['name']
                )
                
                # 버전 생성
                for version in shot['versions']:
                    self.project_service.create_version(
                        shot_id=shot_id,
                        version_number=version['number'],
                        file_path=version['path'],
                    )