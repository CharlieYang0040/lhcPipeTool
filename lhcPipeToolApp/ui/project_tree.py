"""프로젝트 트리 위젯"""
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox
from PySide6.QtCore import Signal, Qt, QSize
from ..services.project_service import ProjectService
from ..services.version_service import VersionService
from ..services.project_version_service import ProjectVersionService
from ..services.sequence_version_service import SequenceVersionService
from ..utils.logger import setup_logger
from .project_tree_item import CustomTreeItemWidget
from .new_version_dialog import NewVersionDialog
from ..utils.event_system import EventSystem
import os

class ProjectTreeWidget(QTreeWidget):
    shot_selected = Signal(int)  # 샷 ID 시그널

    def __init__(self, db_connector):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.project_service = ProjectService(db_connector)
        self.version_service = VersionService(db_connector)
        self.project_version_service = ProjectVersionService(db_connector)
        self.sequence_version_service = SequenceVersionService(db_connector)
        self.setup_ui()
        self.load_projects()
        # 빈 공간 클릭 이벤트 연결
        self.viewport().installEventFilter(self)
        
        # 이벤트 구독
        EventSystem.subscribe('project_updated', self.refresh)

    def setup_ui(self):
        """UI 초기화"""
        self.setHeaderLabels(["Project Structure"])
        self.setColumnCount(1)
        self.setIndentation(24)
        self.setIconSize(QSize(20, 20))
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        arrow_right = os.path.join(self.base_path, 'lhcPipeToolApp', 'resources', 'icons', 'ue-arrow-right.svg')
        arrow_down = os.path.join(self.base_path, 'lhcPipeToolApp', 'resources', 'icons', 'ue-arrow-down.svg')
        
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: #15151e;
                border: none;
                outline: none;
            }}
            
            QTreeWidget::item {{
                padding: 4px;
                border: none;
                outline: none;
            }}
            
            QTreeWidget::item:selected {{
                outline: none;
                background: #2d2d3d;
            }}
            
            QTreeWidget::item:hover {{
                background: #1f1f2c;
            }}
            
            QTreeWidget::branch {{
                background: transparent;
                border: none;
            }}
            
            /* 헤더 스타일 추가 */
            QHeaderView::section {{
                background-color: #1a1a24;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #2d2d3d;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-weight: 500;
                font-size: 14px;
            }}
            
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: url({arrow_right.replace('\\', '/')});
            }}
            
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: url({arrow_down.replace('\\', '/')});
            }}
            
            QScrollBar:vertical {{
                background: #1a1a24;
                width: 8px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: #2d2d3d;
                min-height: 20px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: #363647;
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        self.setColumnWidth(0, 400)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemClicked.connect(self.handle_item_click)

    def load_projects(self):
        """프로젝트 목록 로드"""
        self.clear()
        try:
            cursor = self.project_service.connector.cursor()
            
            # 프로젝트 조회
            cursor.execute("SELECT * FROM projects ORDER BY name")
            projects = cursor.fetchall()
            
            for project in projects:
                project_item = QTreeWidgetItem([""])
                project_item.setData(0, Qt.UserRole, ("project", project[0]))
                project_widget = CustomTreeItemWidget(project[1], "project")
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
                    seq_item = QTreeWidgetItem([""])
                    seq_item.setData(0, Qt.UserRole, ("sequence", sequence[0]))
                    seq_widget = CustomTreeItemWidget(sequence[1], "sequence")
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
                        latest_version = self.version_service.get_latest_version(shot[0])
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

    def add_sequence(self, parent_item, project_id):
        """시퀀스 추가"""
        name, ok = QInputDialog.getText(self, "시퀀 추가", "시퀀스 이름을 입력하세요:")
        if ok and name:
            # 이름 유효성 검사 추가
            if len(name) > 100:  # 데이터베이스 필드 길이에 맞춰 조정
                QMessageBox.warning(self, "경고", "시퀀스 이름이 너무 깁니다.")
                return
                
            try:
                sequence_id = self.project_service.create_sequence(project_id, name.strip())
                if sequence_id:
                    self.refresh()
            except Exception as e:
                self.logger.error(f"시퀀스 추가 실패: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "오류", f"시퀀스 추가 실패: {str(e)}")

    def add_shot(self, parent_item, sequence_id):
        """샷 추가"""
        name, ok = QInputDialog.getText(self, "샷 추가", "샷 이름을 입력하세요:")
        if ok and name:
            try:
                shot_id = self.project_service.create_shot(sequence_id, name)
                if shot_id:
                    self.refresh()
            except Exception as e:
                self.logger.error(f"샷 추가 실패: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "오류", f"샷 추가 실패: {str(e)}")

    def add_version(self, parent_item, item_type, item_id):
        """버전 추가"""
        try:
            self.logger.debug(f"버전 추가 시작 - item_type: {item_type}, item_id: {item_id}")
            
            # 새 버전 다이얼로그 생성 및 실행
            if item_type == "project":
                dialog = NewVersionDialog(self.project_version_service, item_id, self)
            elif item_type == "sequence":
                dialog = NewVersionDialog(self.sequence_version_service, item_id, self)
            else:  # shot
                dialog = NewVersionDialog(self.version_service, item_id, self)
            
            if dialog.exec_():
                self.logger.info("새 버전 생성 성공")
                # 버전 테이블 새로고침을 위해 shot_selected 시그널 재발생
                if item_type == "shot":
                    self.shot_selected.emit(item_id)
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
            
        # 아이템의 타입과 ID 가져오기
        item_type, item_id = item.data(0, Qt.UserRole)
        
        # 샷 아이템 클릭 시 시그널 발생
        if item_type == "shot":
            self.shot_selected.emit(item_id)
        else:
            # 샷이 아닌 경우 버전 테이블 초기화
            self.shot_selected.emit(-1)  # -1은 선택 해제를 의미

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QMouseEvent
        
        if (obj == self.viewport() and 
            event.type() == QEvent.MouseButtonPress):
            
            # 클릭한 위치의 아이템 확인
            item = self.itemAt(event.pos())
            
            # 아이템이 없는 곳을 클릭했을 경우
            if not item:
                self.clearSelection()  # 선택 해제
                self.shot_selected.emit(-1)  # 선택 해제 시그널 발생
                
        return super().eventFilter(obj, event)

    def refresh(self):
        """프로젝트 트리 새로고침"""
        self.load_projects()