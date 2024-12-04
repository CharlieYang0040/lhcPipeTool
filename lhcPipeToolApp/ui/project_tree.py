"""프로젝트 트리 위젯"""
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QApplication
from PySide6.QtCore import Signal, Qt, QSize, QEvent
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

    def __init__(self, project_service, version_services, settings_service):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.project_service = project_service
        self.version_services = version_services
        self.settings_service = settings_service
        self.app_state = AppState()
        self.setup_ui()
        self.load_projects()
        # 빈 공간 클릭 이벤트 연결
        self.viewport().installEventFilter(self)
        self.installEventFilter(self)
        
        # 이벤트 구독
        EventSystem.subscribe('project_updated', self.load_projects)
        EventSystem.subscribe('sequence_updated', self.load_projects)
        EventSystem.subscribe('shot_updated', self.load_projects)
        EventSystem.subscribe('version_updated', self.load_projects)

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
        
    def load_projects(self):
        """프로젝트 목록 로드"""
        self.clear()
        self.logger.debug("프로젝트 목록 로드 시작")
        # self.save_expanded_state()
        try:
            # 서비스 레이어를 통해 전체 프로젝트 구조를 가져옴
            structure = self.project_service.get_full_project_structure()

            self.setSelectionMode(QTreeWidget.ExtendedSelection)

            for project_id, project in structure.items():
                project_name = project['name']
                preview_path = project.get('preview_path')

                project_item = QTreeWidgetItem([""])
                project_item.setData(0, Qt.UserRole, ("project", project_id))
                project_widget = CustomTreeItemWidget(project_name, "project", preview_path)
                self.addTopLevelItem(project_item)
                self.setItemWidget(project_item, 0, project_widget)

                for sequence_id, sequence in project['sequences'].items():
                    sequence_name = sequence['name']
                    preview_path = sequence.get('preview_path')

                    seq_item = QTreeWidgetItem([""])
                    seq_item.setData(0, Qt.UserRole, ("sequence", sequence_id))
                    seq_widget = CustomTreeItemWidget(sequence_name, "sequence", preview_path)
                    project_item.addChild(seq_item)
                    self.setItemWidget(seq_item, 0, seq_widget)

                    for shot_id, shot in sequence['shots'].items():
                        shot_name = shot['name']
                        preview_path = shot.get('preview_path')

                        shot_item = QTreeWidgetItem([""])
                        shot_item.setData(0, Qt.UserRole, ("shot", shot_id))
                        shot_widget = CustomTreeItemWidget(shot_name, "shot", preview_path)
                        seq_item.addChild(shot_item)
                        self.setItemWidget(shot_item, 0, shot_widget)

                    seq_item.setExpanded(True)

                project_item.setExpanded(True)

        except Exception as e:
            self.logger.error(f"프로젝트 목록 로드 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", f"프로젝트 목록 로드 실패: {str(e)}")
        # finally:
        #     self.restore_expanded_state()
            
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
                menu.addAction("프로젝트 삭제", lambda: self.delete_selected_items())
            elif item_type == "sequence":
                menu.addAction("샷 추가", lambda: self.add_shot(item, item_id))
                menu.addAction("시퀀스 버전 추가", lambda: self.add_version(item, "sequence", item_id))
                menu.addAction("시퀀스 삭제", lambda: self.delete_selected_items())
            elif item_type == "shot":
                menu.addAction("버전 추가", lambda: self.add_version(item, "shot", item_id))
                menu.addAction("샷 삭제", lambda: self.delete_selected_items())
                
            menu.exec_(self.viewport().mapToGlobal(position))

    def add_project(self):
        """프로젝트 추가"""
        try:
            dialog = NewProjectDialog(self.project_service, self)

            if dialog.exec_():
                self.logger.info("새 프로젝트 생성 성공")
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

            dialog = NewVersionDialog(self.version_services, self.settings_service, self, item_id, item_type, self)
                
            if dialog.exec_():
                self.logger.info("새 버전 생성 성공")
                # 버전 테이블 새로고침을 위해 shot_selected 시그널 재발생
                self.item_selected.emit(item_id)
                return True
                
            self.logger.debug("버전 생성 취소됨")
            return False
            
        except Exception as e:
            self.logger.error(f"버전 추가 실패: {str(e)}", exc_info=True)

    def delete_selected_items(self):
        """선택된 아이템들 삭제"""
        selected_items = self.selectedItems()
        if not selected_items:
            return True
                    
        reply = QMessageBox.question(
            self, 
            "항목 삭제",
            f"선택한 {len(selected_items)}개의 항목을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
                
        if reply == QMessageBox.Yes:
            for item in selected_items:
                item_type, item_id = item.data(0, Qt.UserRole)
                try:
                    if item_type == "project":
                        if self.project_service.delete_project(item_id):
                            parent = item.parent() or self.invisibleRootItem()
                            parent.removeChild(item)
                    elif item_type == "sequence":
                        if self.project_service.delete_sequence(item_id):
                            parent = item.parent()
                            parent.removeChild(item)
                    elif item_type == "shot":
                        if self.project_service.delete_shot(item_id):
                            parent = item.parent()
                            parent.removeChild(item)
                except Exception as e:
                    QMessageBox.critical(self, "오류", f"{item_type} 삭제 실패: {str(e)}")
        return True

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
                    self.project_service._commit()
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
                    self.project_service._commit()
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
                    self.project_service._commit()
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
            
            item = self.itemAt(event.pos())
            
            if not item:
                self.clearSelection()  # 선택 해제
                self.item_selected.emit(-1)  # 선택 해제 시그널 발생
                
        elif event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Delete:
                self.delete_selected_items()
            
        return super().eventFilter(obj, event)
    
    def save_expanded_state(self):
        self.expanded_items = set()
        self.logger.debug("확장된 상태 저장 시작")
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self._save_expanded_state_recursive(item)
        self.logger.debug(f"확장된 아이템: {self.expanded_items}")

    def _save_expanded_state_recursive(self, item):
        if item.isExpanded():
            item_id = item.data(0, Qt.UserRole)
            self.expanded_items.add(item_id)
            self.logger.debug(f"확장된 아이템 ID 저장: {item_id}")
        for i in range(item.childCount()):
            self._save_expanded_state_recursive(item.child(i))

    def restore_expanded_state(self):
        self.logger.debug("확장된 상태 복원 시작")
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self._restore_expanded_state_recursive(item)
        self.logger.debug("확장된 상태 복원 완료")

    def _restore_expanded_state_recursive(self, item):
        item_id = item.data(0, Qt.UserRole)
        if item_id in self.expanded_items:
            item.setExpanded(True)
            self.logger.debug(f"아이템 ID 복원: {item_id} (확장됨)")
        else:
            item.setExpanded(False)
            self.logger.debug(f"아이템 ID 복원: {item_id} (축소됨)")
        for i in range(item.childCount()):
            self._restore_expanded_state_recursive(item.child(i))
