"""프로젝트 트리 위젯"""
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox
from PySide6.QtCore import Signal, Qt, QSize
from ..services.project_service import ProjectService
from ..utils.logger import setup_logger
from .custom_tree_item import CustomTreeItemWidget

class ProjectTreeWidget(QTreeWidget):
    shot_selected = Signal(int)  # 샷 ID 시그널

    def __init__(self, db_connector):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.project_service = ProjectService(db_connector)
        self.setup_ui()
        self.load_projects()
        
    def setup_ui(self):
        """UI 초기화"""
        self.setHeaderLabels(["Project Structure"])
        self.setColumnCount(1)
        self.setIndentation(20)
        self.setIconSize(QSize(20, 20))
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                border: none;
                show-decoration-selected: 1;
                outline: none;  /* focus 점선 제거 */
            }
            QTreeWidget::item {
                height: 80px;
                padding: 5px;
                padding-left: 15px;  /* 왼쪽 여백 추가 */
                border-bottom: 1px solid #2d2d2d;
                outline: none;  /* focus 점선 제거 */
            }
            /* 선택 시 배경색만 변경하고 테두리는 제거 */
            QTreeWidget::item:selected {
                background-color: #2d5a7c;
                border-bottom: 1px solid #2d2d2d;  /* 기본 bottom border 유지 */
                outline: none;  /* focus 점선 제거 */
            }
            /* hover 효과도 더 미묘하게 수정 */
            QTreeWidget::item:hover:!selected {
                background-color: #262626;
            }
            
            QTreeWidget::item:focus {
                outline: none;  /* focus 점선 제거 */
            }
            
            /* 프로젝트 레벨 (최상위) 브랜치 */
            QTreeWidget::branch:has-children:!has-siblings,
            QTreeWidget::branch:has-children:has-siblings {
                border-left: 3px solid #4A90E2;  /* 파란색, 더 굵은 선 */
            }
            
            /* 시퀀스 레벨 브랜치 */
            QTreeWidget::branch:!has-children:has-siblings,
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
                border-left: 2px solid #50C878;  /* 초록색, 중간 굵기 */
            }
            
            /* 샷 레벨 브랜치 */
            QTreeWidget::branch:!has-children:!has-siblings {
                border-left: 2px solid #FFB6C1;  /* 분홍색, 얇은 선 */
            }
            
            /* 확장/축소 화살표 스타일 */
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(resources/icons/branch-closed.png);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(resources/icons/branch-open.png);
            }
            
            /* 아이템 배경색 */
            QTreeWidget::item:has-children {
                background-color: #252525;
            }
            QTreeWidget::item:has-children:selected {
                background-color: #2d5a7c;
            }
            QTreeWidget::item:!has-children {
                background-color: #1e1e1e;
            }
            QTreeWidget::item:!has-children:selected {
                background-color: #2d5a7c;
            }
        """)
        
        # 컬럼 너비 설정
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
                project_widget = CustomTreeItemWidget(project[1])
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
                    seq_widget = CustomTreeItemWidget(sequence[1])
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
                        shot_item = QTreeWidgetItem([""])
                        shot_item.setData(0, Qt.UserRole, ("shot", shot[0]))
                        preview_path = shot[3] if len(shot) > 3 else None
                        shot_widget = CustomTreeItemWidget(shot[1], preview_path)
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
                menu.addAction("프로젝트 삭제", lambda: self.delete_project(item, item_id))
            elif item_type == "sequence":
                menu.addAction("샷 추가", lambda: self.add_shot(item, item_id))
                menu.addAction("시퀀스 삭제", lambda: self.delete_sequence(item, item_id))
            elif item_type == "shot":
                menu.addAction("샷 삭제", lambda: self.delete_shot(item, item_id))
                
            menu.exec_(self.viewport().mapToGlobal(position))

    def add_sequence(self, parent_item, project_id):
        """시퀀스 추가"""
        name, ok = QInputDialog.getText(self, "시퀀스 추가", "시퀀스 이름을 입력하세요:")
        if ok and name:
            # 이름 유효성 검사 추가
            if len(name) > 100:  # 데이터베이스 필드 길이에 맞춰 조정
                QMessageBox.warning(self, "경고", "시퀀스 이름이 너무 깁니다.")
                return
                
            try:
                sequence_id = self.project_service.create_sequence(project_id, name.strip())
                if sequence_id:
                    seq_item = QTreeWidgetItem([name])
                    seq_item.setData(0, Qt.UserRole, ("sequence", sequence_id))
                    parent_item.addChild(seq_item)
                    parent_item.setExpanded(True)
            except Exception as e:
                QMessageBox.critical(self, "오류", f"시퀀스 추가 실패: {str(e)}")

    def add_shot(self, parent_item, sequence_id):
        """샷 추가"""
        name, ok = QInputDialog.getText(self, "샷 추가", "샷 이름을 입력하세요:")
        if ok and name:
            try:
                shot_id = self.project_service.create_shot(sequence_id, name)
                if shot_id:
                    shot_item = QTreeWidgetItem([name, "in_progress"])
                    shot_item.setData(0, Qt.UserRole, ("shot", shot_id))
                    parent_item.addChild(shot_item)
                    parent_item.setExpanded(True)
            except Exception as e:
                QMessageBox.critical(self, "오류", f"샷 추가 실패: {str(e)}")

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