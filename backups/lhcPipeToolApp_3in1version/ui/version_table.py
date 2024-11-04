"""버전 테이블 위젯"""
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal
from ..services.version_service import VersionService
from ..utils.logger import setup_logger

class VersionTableWidget(QTableWidget):
    version_selected = Signal(int)

    def __init__(self, version_service):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.version_service = version_service
        self.setup_ui()

    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 안내 메시지 라벨
        self.message_label = QLabel("샷을 선택하면 버전 정보가 표시됩니다.")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 14px;
                padding: 20px;
                background-color: #1e1e1e;
            }
        """)

        # 테이블 위젯
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["버전", "작업자", "날짜", "상태"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                border: none;
                outline: none;
                gridline-color: #2d2d2d;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2d2d2d;
                color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #2d5a7c;
                border: none;
                outline: none;
            }
            QTableWidget::item:hover:!selected {
                background-color: #262626;
            }
            QHeaderView::section {
                background-color: #252525;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #4A90E2;
                color: #ffffff;
                font-weight: bold;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 헤더 설정
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # 선택 모드 설정
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # 행 단위 선택
        self.table.setSelectionMode(QTableWidget.SingleSelection)  # 단일 선택만 가능
        
        # 테이블 선택 시그널 연결
        self.table.itemSelectionChanged.connect(self.handle_selection_changed)
        
        # 기본적으로 테이블은 숨기고 메시지를 표시
        self.table.hide()
        layout.addWidget(self.message_label)
        layout.addWidget(self.table)

    def handle_selection_changed(self):
        """테이블 선택 변경 처리"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.version_selected.emit(-1)
            return
            
        row = selected_items[0].row()
        try:
            cursor = self.version_service.connector.cursor()
            cursor.execute("""
                SELECT FIRST 1 SKIP ? id 
                FROM versions 
                WHERE shot_id = ? 
                ORDER BY created_at DESC
            """, (row, self.current_shot_id))
            result = cursor.fetchone()
            if result:
                self.version_selected.emit(result[0])
            else:
                self.version_selected.emit(-1)
        except Exception as e:
            self.logger.error(f"버전 선택 처리 실패: {str(e)}")
            self.version_selected.emit(-1)

    def load_versions(self, version_type, id_value):
        """버전 목록 로드"""
        try:
            self.current_type = version_type
            self.current_id = id_value
            
            # 동적 쿼리 대신 정적 쿼리 사용
            cursor = self.version_service.connector.cursor()
            query = """
                SELECT 
                    'v' || LPAD(v.version_number, 3, '0') as version,
                    w.name as worker_name,
                    v.created_at,
                    v.status
                FROM versions v
                LEFT JOIN workers w ON v.worker_id = w.id 
                WHERE v.version_type = ? 
            """
            
            # 버전 타입에 따라 조건 추가
            if version_type == 'project':
                query += " AND v.project_id = ?"
            elif version_type == 'sequence':
                query += " AND v.sequence_id = ?"
            elif version_type == 'shot':
                query += " AND v.shot_id = ?"
                
            query += " ORDER BY v.version_number DESC"

            self.logger.info(f"실행할 쿼리: {query}")
            self.logger.info(f"파라미터: version_type={version_type}, id_value={id_value}")
            
            cursor.execute(query, (version_type, id_value))
            versions = cursor.fetchall()

            # 테이블 표시 및 메시지 숨기기
            self.message_label.hide()
            self.table.show()
            
            self.table.setRowCount(len(versions))
            for row, version in enumerate(versions):
                for col, value in enumerate(version):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)

            # 컬럼 너비 조정
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"버전 목록 로드 실패: {str(e)}", exc_info=True)
            self.message_label.setText("버전 목록을 불러오는데 실패했습니다.")
            self.message_label.show()
            self.table.hide()

    def clear_versions(self):
        """버전 목록 초기화"""
        self.current_shot_id = None
        self.table.hide()
        self.message_label.show()
        self.table.setRowCount(0)