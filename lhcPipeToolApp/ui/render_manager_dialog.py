"""렌더 출력물 관리 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QTreeWidget, QTreeWidgetItem,
                              QLabel, QMessageBox, QMenu)
from PySide6.QtCore import Qt
from pathlib import Path
from datetime import datetime
from ..utils.logger import setup_logger

class RenderManagerDialog(QDialog):
    def __init__(self, version_service, shot_id, parent=None):
        super().__init__(parent)
        self.version_service = version_service
        self.shot_id = shot_id
        self.render_root = Path(self.version_service.get_render_root())
        self.logger = setup_logger(__name__)
        self.logger.info(f"RenderManager 초기화 - Shot ID: {shot_id}")
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Render Manager")
        self.resize(1000, 600)
        layout = QVBoxLayout(self)
        
        # 상단 정보 표시
        info_layout = QHBoxLayout()
        self.shot_info_label = QLabel()
        self.update_shot_info()
        info_layout.addWidget(self.shot_info_label)
        layout.addLayout(info_layout)
        
        # 렌더 파일 트리
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels([
            "Name", "Size", "Modified", "Type"
        ])
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(
            self.show_context_menu
        )
        layout.addWidget(self.tree_widget)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_renders)
        button_layout.addWidget(refresh_button)
        
        import_button = QPushButton("Import Files")
        import_button.clicked.connect(self.import_files)
        button_layout.addWidget(import_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 초기 데이터 로드
        self.load_renders()
        
    def update_shot_info(self):
        """샷 정보 업데이트"""
        shot_info = self.version_service.get_shot_info(self.shot_id)
        if shot_info:
            self.shot_info_label.setText(
                f"Shot: {shot_info['name']} | "
                f"Status: {shot_info['status']} | "
                f"Latest Version: {shot_info['latest_version']}"
            )
            
    def load_renders(self):
        """렌더 파일 목록 로드"""
        self.tree_widget.clear()
        render_path = self.render_root / f"shot_{self.shot_id}"
        self.logger.info(f"렌더 파일 로드 시작 - 경로: {render_path}")
        
        if not render_path.exists():
            self.logger.info(f"렌더 디렉토리 생성: {render_path}")
            render_path.mkdir(parents=True)
            
        for version_dir in sorted(render_path.glob("v*")):
            self.logger.debug(f"버전 디렉토리 처리: {version_dir}")
            version_item = QTreeWidgetItem([
                version_dir.name,
                "",
                self.format_date(version_dir.stat().st_mtime),
                "Directory"
            ])
            self.tree_widget.addTopLevelItem(version_item)
            
            # 버전 디렉토리 내 파일들 로드
            self.load_render_files(version_item, version_dir)
            
    def load_render_files(self, parent_item, directory):
        """디렉토리 내 렌더 파일들 로드"""
        for file_path in directory.glob("*"):
            if file_path.is_file():
                size = self.format_size(file_path.stat().st_size)
                modified = file_path.stat().st_mtime
                file_type = file_path.suffix[1:].upper()
                
                file_item = QTreeWidgetItem([
                    file_path.name,
                    size,
                    modified,
                    file_type
                ])
                parent_item.addChild(file_item)
                
    def format_size(self, size):
        """파일 크기 포맷팅"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
        
    def format_date(self, timestamp):
        """타임스탬프를 날짜 문자열로 변환"""
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
    def show_context_menu(self, position):
        """컨텍스트 메뉴 표시"""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        # 메뉴 아이템 추가
        open_action = menu.addAction("Open")
        open_location_action = menu.addAction("Open Location")
        menu.addSeparator()
        copy_path_action = menu.addAction("Copy Path")
        
        if item.childCount() == 0:  # 파일인 경우
            preview_action = menu.addAction("Preview")
            delete_action = menu.addAction("Delete")
        
        # 메뉴 표시 및 액션 처리
        action = menu.exec_(self.tree_widget.viewport().mapToGlobal(position))
        
        if action:
            file_path = self.get_item_path(item)
            
            if action == open_action:
                self.open_file(file_path)
            elif action == open_location_action:
                self.open_location(file_path)
            elif action == copy_path_action:
                self.copy_path_to_clipboard(file_path)
            elif action == preview_action:
                self.show_preview(file_path)
            elif action == delete_action:
                self.delete_file(file_path, item)

    def get_item_path(self, item):
        """트리 아이템의 전체 경로 반환"""
        path_parts = []
        while item:
            path_parts.insert(0, item.text(0))
            item = item.parent()
        return self.render_root / f"shot_{self.shot_id}" / "/".join(path_parts)

    def open_file(self, file_path):
        """파일 열기"""
        import os
        os.startfile(str(file_path))

    def open_location(self, file_path):
        """파일 위치 열기"""
        import subprocess
        subprocess.run(['explorer', '/select,', str(file_path)])

    def copy_path_to_clipboard(self, file_path):
        """경로를 클립보드에 복사"""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(str(file_path))

    def show_preview(self, file_path):
        """파일 프리뷰 표시"""
        from .preview_dialog import PreviewDialog
        preview_dialog = PreviewDialog(file_path, self)
        preview_dialog.exec_()

    def delete_file(self, file_path, item):
        """파일 삭제"""
        self.logger.info(f"파일 삭제 시도: {file_path}")
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete {file_path.name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                file_path.unlink()
                item.parent().removeChild(item)
                self.logger.info(f"파일 삭제 성공: {file_path}")
            except Exception as e:
                self.logger.error(f"파일 삭제 실패: {str(e)}")
                QMessageBox.critical(
                    self, 
                    "Error",
                    f"Failed to delete file: {e}"
                )

    def import_files(self):
        """파일 임포트 다이얼로그 표시"""
        from .import_files_dialog import ImportFilesDialog
        dialog = ImportFilesDialog(self.version_service, self.shot_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_renders()  # 렌더 목록 새로고침