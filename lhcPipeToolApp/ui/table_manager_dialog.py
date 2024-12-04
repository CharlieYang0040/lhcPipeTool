"""테이블 관리 다이얼로그"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox, QLineEdit, QFormLayout, QGroupBox, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from ..styles.components import get_dialog_style, get_button_style, get_table_style, get_input_style
from ..utils.logger import setup_logger

class CreateTableDialog(QDialog):
    """테이블 생성 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("새 테이블 생성")
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # 테이블 정보 입력 폼
        form_layout = QFormLayout()
        self.table_name = QLineEdit()
        form_layout.addRow("테이블 이름:", self.table_name)
        
        # 테이블 위젯
        self.columns_table = QTableWidget()
        self.columns_table.setColumnCount(3)
        self.columns_table.setHorizontalHeaderLabels(["컬럼명", "데이터 타입", "제약조건"])
        self.columns_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 컬럼 추가/삭제 버튼
        btn_layout = QHBoxLayout()
        add_column_btn = QPushButton("컬럼 추가")
        remove_column_btn = QPushButton("컬럼 삭제")
        add_column_btn.clicked.connect(self.add_column)
        remove_column_btn.clicked.connect(self.remove_column)
        btn_layout.addWidget(add_column_btn)
        btn_layout.addWidget(remove_column_btn)
        
        # 확인/취소 버튼
        dialog_buttons = QHBoxLayout()
        ok_btn = QPushButton("생성")
        cancel_btn = QPushButton("취소")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        dialog_buttons.addWidget(ok_btn)
        dialog_buttons.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.columns_table)
        layout.addLayout(btn_layout)
        layout.addLayout(dialog_buttons)

        # 편집 관련 설정 추가
        self.columns_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.columns_table.horizontalHeader().setStretchLastSection(True)
        self.columns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 셀 크기 조정 설정
        self.columns_table.verticalHeader().setDefaultSectionSize(40)  # 행 높이
        self.columns_table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 편집 시 셀이 전체 내용을 표시하도록 설정
        self.columns_table.setWordWrap(True)
        self.columns_table.setTextElideMode(Qt.ElideNone)
        
        # 마우스 추적 활성화 (호버 효과)
        self.columns_table.setMouseTracking(True)
        
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(get_dialog_style())
        
        # 버튼 스타일 적용
        for button in self.findChildren(QPushButton):
            button.setStyleSheet(get_button_style())
            
        # 테이블 스타일 적용
        self.columns_table.setStyleSheet(get_table_style())

        # 입력 위젯 스타일 적용
        self.table_name.setStyleSheet(get_input_style())

    def add_column(self):
        row = self.columns_table.rowCount()
        self.columns_table.insertRow(row)
        
    def remove_column(self):
        current_row = self.columns_table.currentRow()
        if current_row >= 0:
            self.columns_table.removeRow(current_row)
            
    def get_table_info(self):
        """테이블 생성 정보 반환"""
        columns = []
        for row in range(self.columns_table.rowCount()):
            column = {
                'name': self.columns_table.item(row, 0).text() if self.columns_table.item(row, 0) else '',
                'type': self.columns_table.item(row, 1).text() if self.columns_table.item(row, 1) else '',
                'constraints': self.columns_table.item(row, 2).text() if self.columns_table.item(row, 2) else ''
            }
            columns.append(column)
            
        return {
            'table_name': self.table_name.text() if self.table_name else '',
            'columns': columns
        }

class TableManagerDialog(QDialog):
    def __init__(self, table_manager, database_service, parent=None):
        super().__init__(parent)
        self.table_manager = table_manager
        self.database_service = database_service
        self.logger = setup_logger(__name__)
        self.setup_ui()
        self.load_tables()
        self.apply_styles()
        
    def setup_ui(self):
        self.setWindowTitle("테이블 관리")
        self.setMinimumWidth(1200)
        self.setMinimumHeight(900)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 상단 컨트롤 영역
        top_control = QHBoxLayout()
        
        # 테이블 선택 그룹
        table_select_group = QGroupBox("테이블 선택")
        table_select_layout = QHBoxLayout(table_select_group)
        self.table_combo = QComboBox()
        self.table_combo.currentTextChanged.connect(self.on_table_selected)
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.load_tables)
        table_select_layout.addWidget(self.table_combo, stretch=1)
        table_select_layout.addWidget(refresh_btn)
        
        # 테이블 관리 버튼 그룹
        table_control_group = QGroupBox("테이블 관리")
        table_btn_layout = QHBoxLayout(table_control_group)
        create_btn = QPushButton("테이블 생성")
        recreate_btn = QPushButton("테이블 재생성")
        create_all_btn = QPushButton("모든 테이블 생성")
        drop_table_btn = QPushButton("테이블 삭제")
        
        create_btn.clicked.connect(self.show_create_table_dialog)
        recreate_btn.clicked.connect(self.recreate_table)
        create_all_btn.clicked.connect(self.create_all_tables)
        drop_table_btn.clicked.connect(self.drop_table)
        
        table_btn_layout.addWidget(create_btn)
        table_btn_layout.addWidget(recreate_btn)
        table_btn_layout.addWidget(create_all_btn)
        table_btn_layout.addWidget(drop_table_btn)
        
        top_control.addWidget(table_select_group, stretch=1)
        top_control.addWidget(table_control_group, stretch=2)
        
        # 데이터 관리 버튼 그룹
        data_control_group = QGroupBox("데이터 관리")
        data_btn_layout = QHBoxLayout(data_control_group)
        
        view_data_btn = QPushButton("데이터 조회")
        self.delete_btn = QPushButton("선택 항목 삭제")
        self.save_changes_btn = QPushButton("변경사항 저장")
        add_column_btn = QPushButton("컬럼 추가")
        
        view_data_btn.clicked.connect(self.view_table_data)
        self.delete_btn.clicked.connect(self.delete_selected_items)
        self.save_changes_btn.clicked.connect(self.save_changes)
        add_column_btn.clicked.connect(self.show_add_column_dialog)
        
        self.delete_btn.setEnabled(False)
        self.save_changes_btn.setEnabled(False)
        
        data_btn_layout.addWidget(view_data_btn)
        data_btn_layout.addWidget(self.delete_btn)
        data_btn_layout.addWidget(self.save_changes_btn)
        data_btn_layout.addWidget(add_column_btn)
        
        # 테이블 위젯
        self.data_table = QTableWidget()
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.itemChanged.connect(self.on_item_changed)
        
        # 편집 관련 설정
        self.data_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
        # 테이블 레이아웃 설정
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.data_table.verticalHeader().setDefaultSectionSize(40)
        self.data_table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 테이블 크기 정책 설정
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 편집 시 셀이 전체 내용을 표시하도록 설정
        self.data_table.setWordWrap(True)
        self.data_table.setTextElideMode(Qt.ElideNone)
        self.data_table.setMouseTracking(True)
        
        main_layout.addLayout(top_control)
        main_layout.addWidget(data_control_group)
        main_layout.addWidget(self.data_table)

        # 다이얼로그가 표시된 후 자동으로 레이아웃 조정
        QTimer.singleShot(0, self.adjust_table_layout)

    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(get_dialog_style())
        
        # 버튼 스타일 적용
        for button in self.findChildren(QPushButton):
            button.setStyleSheet(get_button_style())
            
        # 테이블 스타일 적용
        self.data_table.setStyleSheet(get_table_style())

        # 입력 위젯 스타일 적용
        self.table_combo.setStyleSheet(get_input_style())

    def show_add_column_dialog(self):
        """컬럼 추가 다이얼로그 표시"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("컬럼 추가")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        column_name = QLineEdit()
        column_type = QComboBox()
        column_type.addItems(['VARCHAR(255)', 'INTEGER', 'TIMESTAMP', 'BOOLEAN', 'TEXT'])
        nullable = QComboBox()
        nullable.addItems(['NULL', 'NOT NULL'])
        default_value = QLineEdit()
        
        layout.addRow("컬럼명:", column_name)
        layout.addRow("데이터 타입:", column_type)
        layout.addRow("NULL 허용:", nullable)
        layout.addRow("기본값:", default_value)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("추가")
        cancel_btn = QPushButton("취소")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow("", buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                # ALTER TABLE 쿼리 생성
                constraints = []
                if nullable.currentText() == 'NOT NULL':
                    constraints.append('NOT NULL')
                if default_value.text():
                    constraints.append(f"DEFAULT {default_value.text()}")
                    
                column_def = (
                    f"{column_name.text()} {column_type.currentText()} "
                    f"{' '.join(constraints)}"
                ).strip()
                
                if self.database_service.add_column(table_name, column_def):
                    QMessageBox.information(self, "성공", "컬럼이 추가되었습니다.")
                    self.view_table_data()
                else:
                    QMessageBox.warning(self, "실패", "컬럼 추가에 실패했습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"컬럼 추가 중 오류 발생: {str(e)}")

    def on_item_changed(self, item):
        """데이터 테이블에서 항목이 변경될 때 호출"""
        self.delete_btn.setEnabled(True)
        self.save_changes_btn.setEnabled(True)
        
    def save_changes(self):
        """수정된 데이터 저장"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return
        
        try:
            # 변경된 데이터를 수집
            updated_data = []
            for row in range(self.data_table.rowCount()):
                row_data = {}
                for col in range(self.data_table.columnCount()):
                    column_name = self.data_table.horizontalHeaderItem(col).text()
                    row_data[column_name] = self.data_table.item(row, col).text()
                updated_data.append(row_data)
            
            # 데이터베이스에 변경 사항 저장
            if self.database_service.update_table_data(table_name, updated_data):
                QMessageBox.information(self, "성공", "변경 사항이 저장되었습니다.")
                self.save_changes_btn.setEnabled(False)
            else:
                QMessageBox.warning(self, "실패", "변경 사항 저장에 실패했습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"변경 사항 저장 중 오류 발생: {str(e)}")

    def show_create_table_dialog(self):
        """테이블 생성 다이얼로그 표시"""
        dialog = CreateTableDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            table_info = dialog.get_table_info()
            self.create_new_table(table_info)
            
    def create_new_table(self, table_info):
        """새 테이블 생성"""
        try:
            if self.database_service.create_custom_table(table_info):
                QMessageBox.information(self, "성공", "테이블이 생성되었습니다.")
                self.load_tables()
            else:
                QMessageBox.warning(self, "실패", "테이블 생성에 실패했습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"테이블 생성 중 오류 발생: {str(e)}")
            
    def drop_table(self):
        """테이블 삭제"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return
        
        if self.database_service.drop_table(table_name):
            QMessageBox.information(self, "성공", "테이블이 삭제되었습니다.")
            self.load_tables()
            
    def delete_selected_items(self):
        """선택된 항목 삭제"""
        selected_rows = set(item.row() for item in self.data_table.selectedItems())
        if not selected_rows:
            return
            
        reply = QMessageBox.question(
            self, "확인", 
            f"선택한 {len(selected_rows)}개의 항목을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            table_name = self.table_combo.currentText()
            try:
                # 선택된 행의 기본키 값들을 수집
                primary_keys = []
                for row in selected_rows:
                    # 기본키 컬럼의 인덱스를 찾아야 함
                    pk_value = self.data_table.item(row, 0).text()  # 임시로 첫 번째 컬럼을 기본키로 가정
                    primary_keys.append(pk_value)
                
                if self.database_service.delete_table_rows(table_name, primary_keys):
                    self.view_table_data()  # 테이블 데이터 새로고침
                    QMessageBox.information(self, "성공", "선택한 항목이 삭제되었습니다.")
                else:
                    QMessageBox.warning(self, "실패", "항목 삭제에 실패했습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"항목 삭제 중 오류 발생: {str(e)}")
            
    def load_tables(self):
        """테이블 목록 로드"""
        current_table = self.table_combo.currentText()
        self.table_combo.clear()
        # database_service를 통해 테이블 목록 조회
        tables = self.database_service.get_all_tables()
        self.table_combo.addItems([table.strip() for table in tables])
        
        # 이전 선택 테이블 복원
        if current_table:
            index = self.table_combo.findText(current_table)
            if index >= 0:
                self.table_combo.setCurrentIndex(index)
                
    def on_table_selected(self):
        """테이블 선택 시 데이터 조회"""
        self.view_table_data()
                
    def view_table_data(self):
        """테이블 데이터 조회"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return
        
        try:
            # database_service를 통해 테이블 데이터 조회
            data = self.database_service.get_table_data(table_name)
            if not data:
                self.data_table.setRowCount(0)
                self.data_table.setColumnCount(0)
                return
            
            # 컬럼 설정
            columns = list(data[0].keys())
            self.data_table.setColumnCount(len(columns))
            self.data_table.setHorizontalHeaderLabels(columns)
            
            # 데이터 행 추가
            self.data_table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, (column, value) in enumerate(row_data.items()):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.data_table.setItem(row_idx, col_idx, item)
            
            # 컬럼 크기 자동 조정
            self.data_table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"테이블 데이터 조회 실패: {str(e)}")
            QMessageBox.warning(self, "오류", f"데이터 조회 실패: {str(e)}")
            
    def recreate_table(self):
        """선택된 테이블 재생성"""
        table_name = self.table_combo.currentText()
        reply = QMessageBox.question(
            self, "확인", 
            f"테이블 '{table_name}'을(를) 재생성하시겠습니까?\n기존 데이터는 모두 삭제됩니다.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.table_manager.recreate_table(table_name):
                    QMessageBox.information(self, "성공", f"테이블 '{table_name}' 재생성 완료")
                    self.load_tables()
                else:
                    QMessageBox.warning(self, "실패", f"테이블 '{table_name}' 재생성 실패")
            except Exception as e:
                QMessageBox.critical(self, "오류", str(e))
                
    def create_all_tables(self):
        """모든 테이블 생성"""
        reply = QMessageBox.question(
            self, "확인", 
            "모든 테이블을 생성하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.table_manager.create_all_tables():
                    QMessageBox.information(self, "성공", "모든 테이블 생성 완료")
                    self.load_tables()
                else:
                    QMessageBox.warning(self, "실패", "일부 테이블 생성 실패")
            except Exception as e:
                QMessageBox.critical(self, "오류", str(e))

    def adjust_table_layout(self):
        """테이블 레이아웃 자동 조정"""
        if self.data_table.rowCount() > 0:
            self.data_table.resizeColumnsToContents()
            
            # 전체 컬럼 너비 계산
            total_width = 0
            for col in range(self.data_table.columnCount()):
                total_width += self.data_table.columnWidth(col)
            
            # 테이블 너비가 충분하지 않으면 각 컬럼 크기 조정
            available_width = self.data_table.width()
            if total_width < available_width:
                ratio = available_width / total_width
                for col in range(self.data_table.columnCount()):
                    new_width = int(self.data_table.columnWidth(col) * ratio)
                    self.data_table.setColumnWidth(col, new_width)

    def showEvent(self, event):
        """다이얼로그가 표시될 때 호출되는 이벤트"""
        super().showEvent(event)
        # 초기 데이터 로드 및 레이아웃 조정
        self.view_table_data()
        QTimer.singleShot(100, self.adjust_table_layout)  # 약간의 지연을 두어 윈도우 크기가 확정된 후 실행