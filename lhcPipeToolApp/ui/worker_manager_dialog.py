"""작업자 관리 다이얼로그"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLabel, QLineEdit, QComboBox
)
from ..utils.logger import setup_logger
from ..styles.components import get_dialog_style, get_button_style, get_table_style, get_input_style

class WorkerManagerDialog(QDialog):
    def __init__(self, worker_service, parent=None):
        super().__init__(parent)
        self.worker_service = worker_service
        self.logger = setup_logger(__name__)
        self.setup_ui()
        self.load_workers()
        
        # 스타일시트 적용
        self.setStyleSheet(get_dialog_style())
        
    def setup_ui(self):
        self.setWindowTitle("작업자 관리")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        
        # 새 작업자 추가 영역
        add_layout = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("작업자 이름")
        self.department_combo = QComboBox()
        self.department_combo.addItems(["Animation", "FX", "Lighting", "Editor"])
        add_btn = QPushButton("작업자 추가")
        add_btn.clicked.connect(self.add_worker)
        
        add_layout.addWidget(QLabel("이름:"))
        add_layout.addWidget(self.name_edit)
        add_layout.addWidget(QLabel("부서:"))
        add_layout.addWidget(self.department_combo)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)
        
        # 작업자 목록 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(3)  # ID, 이름, 부서만 표시
        self.table.setHorizontalHeaderLabels(["ID", "이름", "부서"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # 테이블 편집 비활성화
        layout.addWidget(self.table)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        delete_btn = QPushButton("작업자 삭제")
        delete_btn.clicked.connect(self.delete_worker)
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.load_workers)
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        # 입력 필드 스타일 적용
        self.name_edit.setStyleSheet(get_input_style())
        self.department_combo.setStyleSheet(get_input_style())
        
        # 버튼 스타일 적용
        add_btn.setStyleSheet(get_button_style())
        delete_btn.setStyleSheet(get_button_style())
        refresh_btn.setStyleSheet(get_button_style()) 
        close_btn.setStyleSheet(get_button_style())
        
        # 테이블 스타일 적용
        self.table.setStyleSheet(get_table_style())
        
    def load_workers(self):
        """작업자 목록 로드"""
        workers = self.worker_service.get_all_workers()
        self.table.setRowCount(len(workers))
        
        for row, worker in enumerate(workers):
            # worker 딕셔너리: {'id': ..., 'name': ..., 'department': ...}
            self.table.setItem(row, 0, QTableWidgetItem(str(worker['id'])))  # id
            self.table.setItem(row, 1, QTableWidgetItem(worker['name']))       # name
            # department가 없을 수 있으므로 조건부로 설정
            department = worker.get('department', "")
            self.table.setItem(row, 2, QTableWidgetItem(department))            # department
            
    def add_worker(self):
        """새 작업자 추가"""
        name = self.name_edit.text().strip()
        department = self.department_combo.currentText()
        
        if not name:
            QMessageBox.warning(self, "경고", "작업자 이름을 입력하세요.")
            return
            
        try:
            self.worker_service.create_worker(name, 'lion', department=department)
            self.logger.info(f"새 작업자 추가: 이름={name}, 비밀번호=lion, 부서={department}")
            self.name_edit.clear()
            self.load_workers()
        except ValueError as e:
            self.logger.error(f"작업자 추가 실패: {str(e)}")
            QMessageBox.warning(self, "오류", str(e))

            
    def delete_worker(self):
        """작업자 삭제"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "삭제할 작업자를 선택하세요.")
            return
            
        worker_id_item = self.table.item(current_row, 0)
        worker_name_item = self.table.item(current_row, 1)
        
        if not worker_id_item or not worker_name_item:
            QMessageBox.warning(self, "오류", "선택한 작업자의 정보가 불완전합니다.")
            return
        
        worker_id = int(worker_id_item.text())
        worker_name = worker_name_item.text()
        
        reply = QMessageBox.question(
            self, "확인", 
            f"작업자 '{worker_name}'을(를) 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.worker_service.delete_worker(worker_id)
                self.load_workers()
            except ValueError as e:
                QMessageBox.warning(self, "오류", str(e))
