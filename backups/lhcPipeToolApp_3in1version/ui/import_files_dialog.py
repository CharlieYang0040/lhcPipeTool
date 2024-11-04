"""파일 임포트 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QListWidget, QListWidgetItem,
                              QLabel, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt
import shutil
from pathlib import Path
from ..utils.logger import setup_logger

class ImportFilesDialog(QDialog):
    def __init__(self, version_service, shot_id, parent=None):
        super().__init__(parent)
        self.version_service = version_service
        self.shot_id = shot_id
        self.selected_files = []
        self.logger = setup_logger(__name__)
        self.logger.info(f"ImportFilesDialog 초기화 - Shot ID: {shot_id}")
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Import Render Files")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        
        # 파일 목록
        self.file_list = QListWidget()
        layout.addWidget(QLabel("Selected Files:"))
        layout.addWidget(self.file_list)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        add_files_button = QPushButton("Add Files")
        add_files_button.clicked.connect(self.add_files)
        button_layout.addWidget(add_files_button)
        
        add_folder_button = QPushButton("Add Folder")
        add_folder_button.clicked.connect(self.add_folder)
        button_layout.addWidget(add_folder_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(remove_button)
        
        layout.addLayout(button_layout)
        
        # 임포트/취소 버튼
        final_button_layout = QHBoxLayout()
        
        import_button = QPushButton("Import")
        import_button.clicked.connect(self.import_files)
        final_button_layout.addWidget(import_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        final_button_layout.addWidget(cancel_button)
        
        layout.addLayout(final_button_layout)
        
    def add_files(self):
        """파일 선택 다이얼로그"""
        self.logger.info("파일 선택 다이얼로그 열기")
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Render Files",
            "",
            "Render Files (*.exr *.png *.jpg);;All Files (*.*)"
        )
        
        for file_path in files:
            self.logger.debug(f"파일 추가: {file_path}")
            self.add_to_list(Path(file_path))
            
    def add_folder(self):
        """폴더 선택 다이얼로그"""
        self.logger.info("폴더 선택 다이얼로그 열기")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Render Folder"
        )
        
        if folder:
            folder_path = Path(folder)
            self.logger.info(f"선택된 폴더: {folder_path}")
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    self.logger.debug(f"파일 추가: {file_path}")
                    self.add_to_list(file_path)
                    
    def add_to_list(self, file_path):
        """리스트에 파일 추가"""
        item = QListWidgetItem(str(file_path))
        item.setData(Qt.UserRole, str(file_path))
        self.file_list.addItem(item)
        
    def remove_selected(self):
        """선택된 항목 제거"""
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
            
    def import_files(self):
        """선택된 파일들 임포트"""
        if self.file_list.count() == 0:
            self.logger.warning("임포트할 파일이 선택되지 않음")
            QMessageBox.warning(
                self,
                "Warning",
                "No files selected for import!"
            )
            return
            
        try:
            version_num = self.version_service.get_next_version_number(self.shot_id)
            render_root = Path(self.version_service.get_render_root())
            version_dir = render_root / f"shot_{self.shot_id}" / f"v{version_num:03d}"
            self.logger.info(f"새 버전 디렉토리 생성: {version_dir}")
            version_dir.mkdir(parents=True, exist_ok=True)
            
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                source_path = Path(item.data(Qt.UserRole))
                dest_path = version_dir / source_path.name
                self.logger.debug(f"파일 복사: {source_path} -> {dest_path}")
                shutil.copy2(source_path, dest_path)
                
            self.logger.info(f"파일 임포트 완료 - 버전: v{version_num:03d}")
            QMessageBox.information(
                self,
                "Success",
                f"Successfully imported files to version v{version_num:03d}"
            )
            self.accept()
            
        except Exception as e:
            self.logger.error(f"파일 임포트 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to import files: {e}"
            )