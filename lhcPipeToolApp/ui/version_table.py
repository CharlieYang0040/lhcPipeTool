"""버전 테이블 위젯"""
from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QVBoxLayout, 
                               QWidget, QMessageBox, QMenu, QHeaderView, QDialog)
from PySide6.QtCore import Qt, Signal, QEvent
from ..services.version_service import VersionService
from ..ui.new_version_dialog import NewVersionDialog
from ..utils.logger import setup_logger
from ..utils.db_utils import convert_date_format
import os

class VersionTableWidget(QWidget):
    version_selected = Signal(int)

    def __init__(self, db_connector):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.version_service = VersionService(db_connector)
        self.new_version_dialog = NewVersionDialog(self.version_service, self)
        self.setup_ui()
        
        # 테이블 선택 변경 시그널 연결
        self.table.itemSelectionChanged.connect(self.handle_selection_changed)
        
        # 이벤트 필터 및 기타 시그널 연결
        self.table.viewport().installEventFilter(self)
        self.table.doubleClicked.connect(self.handle_double_click)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 테이블 위젯 설정
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["버전", "작업자", "날짜", "상태"])
        
        # 테이블 동작 설정
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 수평 헤더 설정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # 버전 컬럼
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 작업자 컬럼
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 날짜 컬럼
        header.setSectionResizeMode(3, QHeaderView.Stretch)     # 상태 컬럼
        
        # 수직 헤더 설정
        self.table.verticalHeader().setVisible(True)  # 수직 헤더 표시
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(36)  # 행 높이 설정
        
        # 테이블 스타일 설정
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #15151e;
                border: none;
                outline: none;
                gridline-color: #2d2d3d;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2d2d3d;
                border-right: 1px solid #2d2d3d;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            
            /* 헤더 공통 스타일 */
            QHeaderView {
                background-color: #1a1a24;
            }
            
            QHeaderView::section {
                background-color: #1a1a24;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #2d2d3d;
                border-right: 1px solid #2d2d3d;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-weight: 500;
                font-size: 14px;
            }
            
            /* 수직 헤더 특별 스타일 */
            QHeaderView::section:vertical {
                width: 30px;
                background-color: #1a1a24;
                border-right: 1px solid #2d2d3d;
            }
            
            /* 코너 위젯 스타일 */
            QTableCornerButton::section {
                background-color: #1a1a24;
                border: none;
                border-bottom: 1px solid #2d2d3d;
                border-right: 1px solid #2d2d3d;
            }
            
            /* 선택 스타일 */
            QTableWidget::item:selected {
                background-color: #2d2d3d;
                color: #ffffff;
            }
            
            QTableWidget::item:hover:!selected {
                background-color: #1f1f2c;
            }
        """)

        # 키보드 이벤트 처리를 위한 이벤트 필터 설치
        self.table.installEventFilter(self)

        layout.addWidget(self.table)

    def handle_double_click(self, index):
        """더블클릭 처리"""
        row = index.row()
        version_id = self.table.item(row, 0).data(Qt.UserRole)
        version = self.version_service.get_version_details(version_id)
        
        if version and version['file_path']:
            try:
                os.startfile(version['file_path'])
            except Exception as e:
                self.logger.error(f"파일 실행 실패: {str(e)}")
                QMessageBox.warning(self, "오류", "파일을 실행할 수 없습니다.")

    def show_context_menu(self, pos):
        """컨텍스트 메뉴 표시"""
        item = self.table.itemAt(pos)
        if item:
            menu = QMenu(self)
            edit_action = menu.addAction("수정")
            menu.addSeparator()
            delete_action = menu.addAction("버전 삭제")
            
            action = menu.exec_(self.table.viewport().mapToGlobal(pos))
            if action == delete_action:
                row = item.row()
                version_id = self.table.item(row, 0).data(Qt.UserRole)
                self.delete_version(version_id)
            elif action == edit_action:
                row = item.row()
                version_id = self.table.item(row, 0).data(Qt.UserRole)
                self.edit_version(version_id)

    def edit_version(self, version_id):
        """버전 수정"""
        version_details = self.version_service.get_version_details(version_id)
        if version_details:
            dialog = NewVersionDialog(self.version_service, self.current_shot_id, self)
            dialog.worker_input.setCurrentText(version_details['worker_name'])
            dialog.file_path_input.setText(version_details['file_path'])
            dialog.preview_path_input.setText(version_details['preview_path'])
            dialog.comment_input.setText(f"Resubmit from {version_details['name']}")
            
            # 상태 설정
            status_buttons = dialog.status_group.buttons()
            for button in status_buttons:
                if button.text() == version_details['status']:
                    button.setChecked(True)
                    break
            
            if dialog.exec_() == QDialog.Accepted:
                self.load_versions(self.current_shot_id)

    def delete_version(self, version_id):
        """버전 삭제"""
        reply = QMessageBox.question(
            self, 
            "버전 삭제", 
            "정말로 이 버전을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.version_service.delete_version(version_id):
                self.load_versions(self.current_shot_id)
            else:
                QMessageBox.warning(self, "오류", "버전을 삭제하는데 실패했습니다.")

    def load_versions(self, shot_id):
        """버전 목록 로드"""
        self.current_shot_id = shot_id
        self.table.setRowCount(0)
        
        try:
            self.logger.debug(f"샷 ID {shot_id}의 버전 목록 로드 시작")
            versions = self.version_service.get_all_versions(shot_id)
            
            if not versions:
                self.logger.debug("버전 정보가 없습니다.")
                return

            self.logger.debug(f"조회된 버전 수: {len(versions)}")
            self.logger.debug(f"첫 번째 버전 데이터 구조: {versions[0]}")  # 데이터 구조 확인

            self.table.setRowCount(len(versions))
            for row, version in enumerate(versions):
                try:
                    self.logger.debug(f"버전 데이터 처리 - row {row}: {version}")
                    
                    # 수직 헤더 번호 설정
                    self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(row + 1)))
                    
                    # 버전 정보 매핑 시도
                    version_name = version[1] if len(version) > 1 else "Unknown"
                    version_id = version[0] if len(version) > 0 else -1
                    worker_name = version[3] if len(version) > 3 else "Unknown"
                    created_at = version[4] if len(version) > 4 else "Unknown"
                    status = version[5] if len(version) > 5 else "Unknown"
                    
                    self.logger.debug(f"""버전 정보 매핑:
                        version_name: {version_name}
                        version_id: {version_id}
                        worker_name: {worker_name}
                        created_at: {created_at}
                        status: {status}
                    """)

                    # 버전 아이템 생성
                    version_item = QTableWidgetItem(str(version_name))
                    version_item.setData(Qt.UserRole, version_id)
                    version_item.setTextAlignment(Qt.AlignCenter)
                    
                    # 작업자, 날짜, 상태 아이템 생성
                    worker_item = QTableWidgetItem(str(worker_name))
                    date_item = QTableWidgetItem(convert_date_format(created_at))
                    status_item = QTableWidgetItem(str(status))
                    
                    # 아이템 정렬 설정
                    for item in [worker_item, date_item, status_item]:
                        item.setTextAlignment(Qt.AlignCenter)
                    
                    # 테이블에 아이템 추가
                    self.table.setItem(row, 0, version_item)
                    self.table.setItem(row, 1, worker_item)
                    self.table.setItem(row, 2, date_item)
                    self.table.setItem(row, 3, status_item)
                    
                    self.logger.debug(f"행 {row} 데이터 설정 완료")

                except Exception as e:
                    self.logger.error(f"행 {row} 처리 중 오류 발생: {str(e)}", exc_info=True)
                    continue

            # 컬럼 너비 초기값 설정
            self.table.setColumnWidth(0, 80)   # 버전
            self.table.setColumnWidth(1, 100)  # 작업자
            self.table.setColumnWidth(2, 150)  # 날짜
            self.logger.debug("버전 목록 로드 완료")
            
        except Exception as e:
            self.logger.error(f"버전 목록 로드 실패: {str(e)}", exc_info=True)

    def clear_versions(self):
        """버전 테이블 초기화"""
        self.table.setRowCount(0)
        self.current_shot_id = None  # 현재 선택된 샷 ID 초기화
        self.version_selected.emit(-1)  # 버전 선택 해제 시그널 생

    def handle_selection_changed(self):
        """테이블 선택 변경 처리"""
        selected_items = self.table.selectedItems()
        self.logger.debug(f"선택된 아이템: {selected_items}")
        
        if not selected_items:
            self.logger.debug("선택된 아이템 없음, 시그널 발생: -1")
            self.version_selected.emit(-1)
            return
            
        row = selected_items[0].row()
        version_id = self.table.item(row, 0).data(Qt.UserRole)
        self.logger.debug(f"선택된 버전 ID: {version_id}")
        self.version_selected.emit(version_id)

    def eventFilter(self, obj, event):
        """이벤트 필터"""
        if obj == self.table and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Delete:
                self.delete_selected_versions()
                return True
        return super().eventFilter(obj, event)

    def delete_selected_versions(self):
        """선택된 버전들 삭제"""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
            
        version_ids = []
        for row in selected_rows:
            version_id = self.table.item(row, 0).data(Qt.UserRole)
            version_ids.append(version_id)
        
        if len(version_ids) == 1:
            message = "이 버전을 삭제하시겠습니까?"
        else:
            message = f"선택한 {len(version_ids)}개의 버전을 삭제하시겠습니까?"
        
        reply = QMessageBox.question(
            self, 
            "버전 삭제", 
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = True
            for version_id in version_ids:
                if not self.version_service.delete_version(version_id):
                    success = False
                    
            if success:
                self.load_versions(self.current_shot_id)
            else:
                QMessageBox.warning(self, "오류", "일부 버전을 삭제하는데 실패했습니다.")