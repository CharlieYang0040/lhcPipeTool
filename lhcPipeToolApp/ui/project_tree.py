"""프로젝트 트리 위젯"""
import os
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QApplication
from PySide6.QtCore import Signal, Qt, QSize, QEvent
from ..services.project_service import ProjectService
from ..services.version_services import (
    ShotVersionService, SequenceVersionService, ProjectVersionService
)
from ..utils.logger import setup_logger
from .project_tree_item import CustomTreeItemWidget
from .new_shot_dialog import NewShotDialog
from .new_sequence_dialog import NewSequenceDialog
from .new_project_dialog import NewProjectDialog
from .new_version_dialog import NewVersionDialog
from ..utils.event_system import EventSystem
from ..config.app_state import AppState
from ..styles.components import get_tree_style

class ProjectTreeWidget(QTreeWidget):
    item_selected = Signal(int)
    item_type_changed = Signal(str, int)

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
        self.setup_ui()
        self.load_projects()
        # 빈 공간 클릭 이벤트 연결
        self.viewport().installEventFilter(self)
        self.installEventFilter(self)
        
        # 이벤트 구독
        EventSystem.subscribe('project_updated', self.refresh)
        EventSystem.subscribe('sequence_updated', self.refresh)
        EventSystem.subscribe('shot_updated', self.refresh)
        EventSystem.subscribe('version_updated', self.refresh)

    def setup_ui(self):
        """UI 초기화"""
        self.setHeaderLabels(["영상연출실"])
        self.setColumnCount(1)
        
        # 화면 해상도에 따른 크기 조정
        screen = QApplication.primaryScreen()
        scale_factor = screen.logicalDotsPerInch() / 96
        
        # 들여쓰기 크기 조정
        indentation = int(24 * scale_factor)
        self.setIndentation(indentation)
        
        # 아이콘 크기 조정
        icon_size = int(20 * scale_factor)
        self.setIconSize(QSize(icon_size, icon_size))
        
        # 트리 너비 조정
        tree_width = int(400 * scale_factor)
        self.setColumnWidth(0, tree_width)
        
        self.setStyleSheet(get_tree_style())
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemClicked.connect(self.handle_item_click)
        
    # TODO 열려있던 계층 구조 유지
    def load_projects(self):
        """프로젝트 목록 로드"""
        self.clear()
        try:
            cursor = self.project_service.connector.cursor()
            
            # 프로젝트 조회
            cursor.execute("SELECT * FROM projects ORDER BY name")
            projects = cursor.fetchall()
            
            self.setSelectionMode(QTreeWidget.ExtendedSelection)

            for project in projects:
                latest_version = self.version_services["project"].get_latest_version(project[0])
                preview_path = latest_version[7] if latest_version else None
                project_item = QTreeWidgetItem([""])
                project_item.setData(0, Qt.UserRole, ("project", project[0]))
                project_widget = CustomTreeItemWidget(project[1], "project", preview_path)
                self.addTopLevelItem(project_item)
                self.setItemWidget(project_item, 0, project_widget)
                
                # 시퀀스 조회
                cursor.execute("""
                    SELECT * FROM sequences 
                    WHERE project_id = ? 
                    ORDER BY name
                """, (project[0],))
                sequences = cursor.fetchall()
                
                for sequence in sequences:
                    latest_version = self.version_services["sequence"].get_latest_version(sequence[0])
                    preview_path = latest_version[7] if latest_version else None
                    seq_item = QTreeWidgetItem([""])
                    seq_item.setData(0, Qt.UserRole, ("sequence", sequence[0]))
                    seq_widget = CustomTreeItemWidget(sequence[1], "sequence", preview_path)
                    project_item.addChild(seq_item)
                    self.setItemWidget(seq_item, 0, seq_widget)
                    
                    # 샷 조회
                    cursor.execute("""
                        SELECT s.*, v.preview_path 
                        FROM shots s 
                        LEFT JOIN (
                            SELECT shot_id, preview_path, created_at
                            FROM versions v1
                            WHERE created_at = (
                                SELECT MAX(created_at)
                                FROM versions v2
                                WHERE v2.shot_id = v1.shot_id
                            )
                        ) v ON s.id = v.shot_id 
                        WHERE s.sequence_id = ? 
                        ORDER BY s.name
                    """, (sequence[0],))
                    shots = cursor.fetchall()
                    
                    for shot in shots:
                        latest_version = self.version_services["shot"].get_latest_version(shot[0])
                        preview_path = latest_version[7] if latest_version else None
                        shot_item = QTreeWidgetItem([""])
                        shot_item.setData(0, Qt.UserRole, ("shot", shot[0]))
                        shot_widget = CustomTreeItemWidget(shot[1], "shot", preview_path)
                        seq_item.addChild(shot_item)
                        self.setItemWidget(shot_item, 0, shot_widget)
                
                project_item.setExpanded(True)
                
        except Exception as e:
            self.logger.error(f"프로젝트 목록 로드 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", f"프로젝트 목록 로드 실패: {str(e)}")

    def show_context_menu(self, position):
        """우클릭 컨텍스트 메뉴 표시"""
        menu = QMenu()
        item = self.itemAt(position)
        
        if not item:
            menu.addAction("새 프로젝트 추가", lambda: self.add_project())
            menu.exec_(self.viewport().mapToGlobal(position))
            return

        if item:
            item_type, item_id = item.data(0, Qt.UserRole)
            
            if item_type == "project":
                menu.addAction("시퀀스 추가", lambda: self.add_sequence(item, item_id))
                menu.addAction("프로젝트 버전 추가", lambda: self.add_version(item, "project", item_id))
                menu.addAction("프로젝트 삭제", lambda: self.delete_project(item, item_id))
            elif item_type == "sequence":
                menu.addAction("샷 추가", lambda: self.add_shot(item, item_id))
                menu.addAction("시퀀스 버전 추가", lambda: self.add_version(item, "sequence", item_id))
                menu.addAction("시퀀스 삭제", lambda: self.delete_sequence(item, item_id))
            elif item_type == "shot":
                menu.addAction("버전 추가", lambda: self.add_version(item, "shot", item_id))
                menu.addAction("샷 삭제", lambda: self.delete_shot(item, item_id))
                
            menu.exec_(self.viewport().mapToGlobal(position))

    def add_project(self):
        """프로젝트 추가"""
        try:
            dialog = NewProjectDialog(self.project_service, self)

            if dialog.exec_():
                self.logger.info("새 프로젝트 생성 성공")
                self.refresh()
                return True
                
            self.logger.debug("프로젝트 생성 취소됨")
            return False
        
        except Exception as e:
            self.logger.error(f"프로젝트 추가 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", f"프로젝트 추가 실패: {str(e)}")
            return False
        
    def add_sequence(self, parent_item, project_id):
        """시퀀스 추가"""
        try:
            dialog = NewSequenceDialog(self.project_service, project_id, self)
            
            if dialog.exec_():
                self.logger.info("새 시퀀스 생성 성공")
                self.refresh()
                return True
                
            self.logger.debug("시퀀스 생성 취소됨")
            return False
            
        except Exception as e:
            self.logger.error(f"시퀀스 추가 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", f"시퀀스 추가 실패: {str(e)}")
            return False

    def add_shot(self, parent_item, sequence_id):
        """샷 추가"""
        try:
            dialog = NewShotDialog(self.project_service, sequence_id, self)
            
            if dialog.exec_():
                self.logger.info("새 샷 생성 성공")
                self.refresh()
                return True
                
            self.logger.debug("샷 생성 취소됨")
            return False
            
        except Exception as e:
            self.logger.error(f"샷 추가 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", f"샷 추가 실패: {str(e)}")
            return False

    def add_version(self, parent_item, item_type, item_id):
        """버전 추가"""
        try:
            self.logger.debug(f"버전 추가 시작 - item_type: {item_type}, item_id: {item_id}")

            dialog = NewVersionDialog(self.db_connector, self, item_id, item_type, self)
                
            if dialog.exec_():
                self.logger.info("새 버전 생성 성공")
                # 버전 테이블 새로고침을 위해 shot_selected 시그널 재발생
                self.item_selected.emit(item_id)
                return True
                
            self.logger.debug("버전 생성 취소됨")
            return False
            
        except Exception as e:
            self.logger.error(f"버전 추가 실패: {str(e)}", exc_info=True)
            return False

    def delete_project(self, item, project_id):
        """프로젝트 삭제"""
        reply = QMessageBox.question(self, "프로젝트 삭제", 
                                   "정말로 이 프로젝트를 삭제하시겠습니까?\n모든 관련 시퀀스와 샷이 함께 삭제됩니다.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if self.project_service.delete_project(project_id):
                    index = self.indexOfTopLevelItem(item)
                    self.takeTopLevelItem(index)
            except Exception as e:
                QMessageBox.critical(self, "오류", f"프로젝트 삭제 실패: {str(e)}")

    def delete_sequence(self, item, sequence_id):
        """시퀀스 삭제"""
        reply = QMessageBox.question(self, "시퀀스 삭제", 
                                   "정말로 이 시퀀스를 삭제하시겠습니까?\n모든 관련 샷이 함께 삭제됩니다.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if self.project_service.delete_sequence(sequence_id):
                    parent = item.parent()
                    parent.removeChild(item)
            except Exception as e:
                QMessageBox.critical(self, "오류", f"시퀀스 삭제 실패: {str(e)}")

    def delete_shot(self, item, shot_id):
        """샷 삭제"""
        reply = QMessageBox.question(self, "샷 삭제", 
                                   "정말로 이 샷을 삭제하시겠습니까?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if self.project_service.delete_shot(shot_id):
                    parent = item.parent()
                    parent.removeChild(item)
            except Exception as e:
                QMessageBox.critical(self, "오류", f"샷 삭제 실패: {str(e)}")

    def handle_item_click(self, item, column):
        """트리 아이템 클릭 처리"""
        if not item:
            return
        
        item_type, item_id = item.data(0, Qt.UserRole)
        self.logger.debug(f"트리 아이템 클릭 - type: {item_type}, id: {item_id}")
        
        # AppState 업데이트
        self.app_state.current_item_type = item_type
        self.app_state.current_item_id = item_id
        
        # 두 시그널 모두 발생
        self.item_selected.emit(item_id)  # 버전 테이블용
        self.item_type_changed.emit(item_type, item_id)  # 디테일 패널용

    def eventFilter(self, obj, event):
        if (obj == self.viewport() and 
            event.type() == QEvent.MouseButtonPress):
            
            # 클릭한 위치의 아이템 확인
            item = self.itemAt(event.pos())
            
            # 아이템이 없는 곳을 클릭했을 경우
            if not item:
                self.clearSelection()  # 선택 해제
                self.item_selected.emit(-1)  # 선택 해제 시그널 발생
                
        elif event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Delete:
                self.delete_selected_items()
                return True
            
        return super().eventFilter(obj, event)

    def refresh(self):
        """프로젝트 트리 새로고침"""
        self.load_projects()

    def delete_selected_items(self):
        """선택된 아이템들 삭제"""
        self.logger.debug(f"선택된 아이템들 : {self.selectedItems()}")
        selected_items = self.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            item_type, item_id = item.data(0, Qt.UserRole)
            self.delete_item(item, item_type, item_id)

    def delete_item(self, item, item_type, item_id):
        """아이템 삭제"""
        if item_type == "project":
            self.delete_project(item, item_id)
        elif item_type == "sequence":
            self.delete_sequence(item, item_id)
        elif item_type == "shot":
            self.delete_shot(item, item_id)

        
