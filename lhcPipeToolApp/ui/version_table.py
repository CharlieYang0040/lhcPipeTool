"""버전 테이블 위젯"""
import os
from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QVBoxLayout, 
                               QWidget, QMessageBox, QMenu, QHeaderView, QDialog, QApplication)
from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QColor
from ..services.version_services import (
    ShotVersionService, SequenceVersionService, ProjectVersionService
)
from ..ui.new_version_dialog import NewVersionDialog
from ..utils.logger import setup_logger
from ..utils.db_utils import convert_date_format
from ..config.app_state import AppState
from ..styles.components import get_table_style

class VersionTableWidget(QWidget):
    version_selected = Signal(int)

    def __init__(self, db_connector):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.db_connector = db_connector
        self.version_services = {
            "shot": ShotVersionService(db_connector, self.logger),
            "sequence": SequenceVersionService(db_connector, self.logger),
            "project": ProjectVersionService(db_connector, self.logger)
        }
        self.app_state = AppState()
        self.new_version_dialog = NewVersionDialog(db_connector, item_id=None, item_type="shot", parent=self)
        
        # 화면 해상도에 따른 스케일 팩터 계산
        self.scale_factor = self.calculate_scale_factor()
        self.setup_ui()
        
        # 테이블 선택 변경 시그널 연결
        self.table.itemSelectionChanged.connect(self.handle_selection_changed)
        
        # 이벤트 필터 및 기타 시그널 연결
        self.table.viewport().installEventFilter(self)
        self.table.doubleClicked.connect(self.handle_double_click)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def calculate_scale_factor(self):
        """화면 해상도에 따른 스케일 팩터 계산"""
        screen = QApplication.primaryScreen()
        dpi = screen.logicalDotsPerInch()
        return dpi / 96

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
        
        # 해상도에 따른 폰트 크기 조정
        font_size = int(13 * self.scale_factor)
        row_height = int(36 * self.scale_factor)
        header_height = int(42 * self.scale_factor)
        
        # 수평 헤더 설정
        header = self.table.horizontalHeader()
        header.setMinimumHeight(header_height)
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # 버전 컬럼
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 작업자 컬럼
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 날짜 컬럼
        header.setSectionResizeMode(3, QHeaderView.Stretch)     # 상태 컬럼
        
        # 초기 컬럼 너비 설정
        self.table.setColumnWidth(0, int(80 * self.scale_factor))   # 버전
        self.table.setColumnWidth(1, int(100 * self.scale_factor))  # 작업자
        self.table.setColumnWidth(2, int(150 * self.scale_factor))  # 날짜
        
        # 수직 헤더 설정
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(row_height)

        # 테이블 스타일 설정
        self.table.setStyleSheet(get_table_style())

        layout.addWidget(self.table)

    def handle_double_click(self, index):
        """더블클릭 처리"""
        row = index.row()
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        version = self.version_services[self.app_state.current_item_type].get_version_details(item_id)
        
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
            edit_action = menu.addAction("수정 및 재등록")
            menu.addSeparator()
            delete_action = menu.addAction("버전 삭제")
            
            action = menu.exec_(self.table.viewport().mapToGlobal(pos))
            if action == delete_action:
                row = item.row()
                item_id = self.table.item(row, 0).data(Qt.UserRole)
                self.delete_version(item_id)
            elif action == edit_action:
                row = item.row()
                item_id = self.table.item(row, 0).data(Qt.UserRole)
                self.edit_version(item_id)

    def edit_version(self, item_id):
        """버전 수정"""
        version_details = self.version_services[self.app_state.current_item_type].get_version_details(item_id)
        if version_details:
            dialog = NewVersionDialog(self.db_connector, self.app_state.current_item_id, self.app_state.current_item_type, parent=self)
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
                self.load_versions(self.app_state.current_item_id)

    def delete_version(self, item_id):
        """버전 삭제"""
        reply = QMessageBox.question(
            self, 
            "버전 삭제", 
            "정말로 이 버전을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.version_services[self.app_state.current_item_type].delete_version(item_id):
                self.load_versions(self.app_state.current_item_id)
            else:
                QMessageBox.warning(self, "오류", "버전을 삭제하는데 실패했습니다.")

    def load_versions(self, item_id):
        """버전 목록 로드"""
        item_type = self.app_state.current_item_type
        item_id = self.app_state.current_item_id
        
        self.table.setRowCount(0)

        try:
            self.logger.debug(f"{item_type} ID {item_id}의 버전 목록 로드 시작")
            versions = self.version_services[item_type].get_all_versions(item_id)
            
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
            self.add_stretch_rows()  # 빈 공간 채우기
            self.logger.debug("버전 목록 로드 완료")
            
        except Exception as e:
            self.logger.error(f"버전 목록 로드 실패: {str(e)}", exc_info=True)

    def clear_versions(self):
        """버전 테이블 초기화"""
        row_count = 1  # 최소 1행은 표시
        self.table.setRowCount(row_count)
        
        # 수직 헤더 설정 유지
        for row in range(row_count):
            self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(row + 1)))
            # 빈 셀 설정
            for col in range(self.table.columnCount()):
                self.table.setItem(row, col, QTableWidgetItem(""))
        
        self.current_shot_id = None
        self.version_selected.emit(-1)
        self.add_stretch_rows()  # 남은 공간 채우기

    def handle_selection_changed(self):
        """테이블 선택 변경 처리"""
        selected_items = self.table.selectedItems()
        self.logger.debug(f"선택된 아이템: {selected_items}")
        
        if not selected_items:
            self.logger.debug("선택된 아이템 없음, 시그널 발생: -1")
            self.version_selected.emit(-1)
            return
            
        row = selected_items[0].row()
        item = self.table.item(row, 0)
        
        # 더미 아이템 체크
        if item and item.data(Qt.UserRole) == -1:
            self.logger.debug("더미 아이템 선택됨, 시그널 발생: -1")
            self.table.clearSelection()  # 선택 해제
            self.version_selected.emit(-1)
            return
            
        version_id = item.data(Qt.UserRole)
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
                if not self.version_services[self.app_state.current_item_type].delete_version(version_id):
                    success = False
                    
            if success:
                self.load_versions(self.app_state.current_item_id)
            else:
                QMessageBox.warning(self, "오류", "일부 버전을 삭제하는데 실패했습니다.")

    def add_stretch_rows(self):
        """테이블 끝까지 빈 공간을 채우는 더미 행 추가"""
        # 현재 모든 더미 행 제거
        for row in range(self.table.rowCount() - 1, -1, -1):
            if self.table.item(row, 0) and self.table.item(row, 0).data(Qt.UserRole) == -1:
                self.table.removeRow(row)
        
        # 테이블 뷰포트의 높이 계산
        viewport_height = self.table.viewport().height()
        header_height = self.table.horizontalHeader().height()
        row_height = self.table.rowHeight(0) if self.table.rowCount() > 0 else 25
        
        # 현재 데이터 행이 차지하는 전체 높이
        total_data_height = sum(self.table.rowHeight(row) for row in range(self.table.rowCount()))
        
        # 필요한 더미 행 수 계산
        remaining_height = viewport_height - total_data_height
        dummy_rows_needed = max(0, remaining_height // row_height)
        
        # 더미 행 추가
        for _ in range(dummy_rows_needed):
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col in range(self.table.columnCount()):
                item = QTableWidgetItem()
                item.setFlags(Qt.NoItemFlags)  # 선택/편집 불가
                item.setData(Qt.UserRole, -1)  # 더미 행 표시용 특수 ID
                item.setBackground(QColor("#15151e"))
                self.table.setItem(row, col, item)

    def resizeEvent(self, event):
        """테이블 크기 변경 시 더미 행 업데이트"""
        super().resizeEvent(event)
        QTimer.singleShot(0, self.add_stretch_rows)  # 지연 실행으로 레이아웃 업데이트 후 처리