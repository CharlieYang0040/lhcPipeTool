"""테이블 관리 다이얼로그"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, QTimeEdit, QDateTimeEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox, QWidget,
    QComboBox, QLineEdit, QFormLayout, QGroupBox, QHeaderView, QSizePolicy, QScrollArea, QLabel
)
from PySide6.QtCore import Qt, QDate, QTime, QDateTime
from ..styles.components import get_dialog_style, get_button_style, get_table_style, get_input_style
from ..utils.logger import setup_logger

class CreateTableDialog(QDialog):
    """테이블 생성 및 컬럼 관리 다이얼로그"""
    
    # 모드 상수를 정의하여 오타를 방지하고 가독성을 높임
    MODE_CREATE_TABLE = "create_table"
    MODE_CREATE_COLUMN = "create_column"
    MODE_DROP_COLUMN = "drop_column"  # 새로운 모드 추가

    def __init__(self, parent=None, mode="create_table", table_name=None, database_service=None):
        super().__init__(parent)
        self.mode = mode
        self.table_name = table_name
        self.database_service = database_service  # database_service 추가
        self.logger = setup_logger(__name__)
        self.setup_ui()
        if self.mode == self.MODE_DROP_COLUMN:
            self.load_existing_columns()  # 기존 컬럼 로드
        self.apply_styles()
        
    def setup_ui(self):
        """UI 초기화"""
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 테이블 정보 입력 그룹
        table_info_group = QGroupBox("테이블 정보")
        form_layout = QFormLayout(table_info_group)
        self.table_name_input = QLineEdit()
        
        # 모드에 따른 UI 설정
        if self.mode == self.MODE_CREATE_TABLE:
            self.setWindowTitle("새 테이블 생성")
            form_layout.addRow("테이블 이름:", self.table_name_input)
        elif self.mode == self.MODE_CREATE_COLUMN:
            self.setWindowTitle("컬럼 추가")
            self.table_name_input.setText(self.table_name)
            self.table_name_input.setEnabled(False)
            form_layout.addRow("테이블:", self.table_name_input)
        else:  # MODE_DROP_COLUMN
            self.setWindowTitle("컬럼 삭제")
            self.table_name_input.setText(self.table_name)
            self.table_name_input.setEnabled(False)
            form_layout.addRow("테이블:", self.table_name_input)
            
            # 컬럼 삭제 모드일 때 경고 메시지 추가
            warning_label = QLabel("주의: 컬럼 삭제 시 해당 컬럼의 모든 데이터가 영구적으로 삭제됩니다.")
            warning_label.setStyleSheet("color: red;")
            warning_label.setWordWrap(True)
            form_layout.addRow(warning_label)
        
        # 컬럼 정보 그룹
        column_group = QGroupBox("컬럼 정보")
        column_layout = QVBoxLayout(column_group)
        
        # 컬럼 관리 버튼 그룹
        btn_group = QHBoxLayout()
        if self.mode == self.MODE_CREATE_TABLE or self.mode == self.MODE_CREATE_COLUMN:
            add_column_btn = QPushButton("컬럼 추가")
            remove_column_btn = QPushButton("컬럼 삭제")
            add_column_btn.clicked.connect(self.add_column)
            remove_column_btn.clicked.connect(self.remove_column)
            btn_group.addWidget(add_column_btn)
            btn_group.addWidget(remove_column_btn)
        
        # 컬럼 테이블 설정
        self.columns_table = QTableWidget()
        self.setup_columns_table()
        
        # 컬럼 그룹에 위젯 추가
        column_layout.addWidget(self.columns_table)
        if self.mode == self.MODE_CREATE_TABLE or self.mode == self.MODE_CREATE_COLUMN:
            column_layout.addLayout(btn_group)
        
        # 확인/취소 버튼
        dialog_buttons = QHBoxLayout()
        dialog_buttons.setSpacing(10)
        ok_btn = QPushButton("확인")
        cancel_btn = QPushButton("취소")
        
        # 모드에 따른 확인 버튼 텍스트 변경
        if self.mode == self.MODE_DROP_COLUMN:
            ok_btn.setText("삭제")
            ok_btn.setStyleSheet(get_button_style(background_color="#e74c3c"))  # 빨간색 계열
            
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        dialog_buttons.addStretch()
        dialog_buttons.addWidget(ok_btn)
        dialog_buttons.addWidget(cancel_btn)
        
        # 전체 레이아웃 구성
        layout.addWidget(table_info_group)
        layout.addWidget(column_group)
        layout.addLayout(dialog_buttons)
        
        # 초기 컬럼 추가 (생성 모드일 때만)
        if self.mode == self.MODE_CREATE_TABLE:
            self.add_column()

    def load_existing_columns(self):
        """기존 테이블의 컬럼 목록 로드"""
        try:
            columns = self.database_service.get_table_structure(self.table_name)
            self.columns_table.setRowCount(len(columns))
            for row, column_name in enumerate(columns):
                self.columns_table.setItem(row, 0, QTableWidgetItem(column_name))
                
                # 컬럼 타입과 제약조건 정보 로드 (옵션)
                columns_info = self.database_service.database_model.get_table_columns(self.table_name)
                for col_info in columns_info:
                    if col_info['column_name'].strip() == column_name:
                        type_item = QTableWidgetItem(str(col_info['data_type']))
                        constraint_item = QTableWidgetItem("NOT NULL" if col_info.get('not_null') else "")
                        self.columns_table.setItem(row, 1, type_item)
                        self.columns_table.setItem(row, 2, constraint_item)
                        break
                        
        except Exception as e:
            self.logger.error(f"컬럼 목록 로드 실패: {str(e)}")
            QMessageBox.warning(self, "오류", f"컬럼 목록을 불러오는데 실패했습니다: {str(e)}")

    def accept(self):
        """확인 버튼 클릭 시 처리"""
        try:
            if self.mode == self.MODE_CREATE_COLUMN:
                self.create_column()
            elif self.mode == self.MODE_DROP_COLUMN:
                self.drop_column()
            else:
                super().accept()
                
        except Exception as e:
            self.logger.error(f"컬럼 삭제 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"컬럼 삭제 중 오류가 발생했습니다: {str(e)}")

    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(get_dialog_style())
        
        # 버튼 스타일 적용
        for button in self.findChildren(QPushButton):
            button.setStyleSheet(get_button_style())
        
        # 테이블 스타일 적용
        self.columns_table.setStyleSheet(get_table_style())
        
        # 입력 위젯 스타일 적용
        for widget in self.columns_table.findChildren(QComboBox):
            widget.setStyleSheet(get_input_style())
        for widget in self.columns_table.findChildren(QLineEdit):
            widget.setStyleSheet(get_input_style())
        self.table_name_input.setStyleSheet(get_input_style())

    def setup_columns_table(self):
        """컬럼 테이블 설정"""
        self.columns_table.setColumnCount(3)
        self.columns_table.setHorizontalHeaderLabels(["컬럼명", "데이터 타입", "제약조건"])
        
        # 테이블 선택 및 편집 설정
        self.columns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.columns_table.setSelectionMode(QTableWidget.SingleSelection)
        self.columns_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
        # 데이터 타입과 제약조건 목록 정의
        self.data_types = [
            # 문자열 타입
            'VARCHAR(50)',
            'VARCHAR(100)',
            'VARCHAR(500)',
            'CHAR(1)',
            'CHAR(10)',
            'TEXT',
            'BLOB SUB_TYPE TEXT',  # 대용량 텍스트
            
            # 숫자 타입
            'SMALLINT',           # -32,768 ~ 32,767
            'INTEGER',           # -2,147,483,648 ~ 2,147,483,647
            'BIGINT',           # -2^63 ~ 2^63-1
            'DECIMAL(15,2)',    # 금액 등 정확한 소수점 계산
            'DECIMAL(18,3)',    # 더 큰 정밀도
            'FLOAT',            # 단정밀도 부동소수점
            'DOUBLE PRECISION', # 배정밀도 부동소수점
            'NUMERIC(15,2)',    # DECIMAL과 유사
            
            # 날짜/시간 타입
            'DATE',             # 날짜만
            'TIME',            # 시간만
            'TIMESTAMP',       # 날짜와 시간
            
            # 논리 타입
            'BOOLEAN',         # True/False
            
            # 특수 타입
            'BLOB',            # 이진 데이터
            'BLOB SUB_TYPE 0', # 이진 BLOB
            'BLOB SUB_TYPE 1'  # 텍스트 BLOB
        ]

        self.constraints = [
            '',                          # 제약조건 없음
            'NOT NULL',                  # NULL 값 허용하지 않음
            'PRIMARY KEY',               # 기본키
            'PRIMARY KEY NOT NULL',      # 기본키 (NULL 불가)
            'UNIQUE',                    # 고유값
            'UNIQUE NOT NULL',          # 고유값 (NULL 불가)
            'GENERATED BY DEFAULT AS IDENTITY',  # 자동 증가
            'GENERATED ALWAYS AS IDENTITY',      # 항상 자동 증가
            'CHECK (VALUE > 0)',        # 양수 값만 허용
            'CHECK (VALUE >= 0)',       # 0 이상 값만 허용
            'DEFAULT NULL',             # 기본값 NULL
            'DEFAULT 0',                # 기본값 0
            'DEFAULT CURRENT_TIMESTAMP', # 기본값 현재 시간
            'DEFAULT CURRENT_DATE',     # 기본값 현재 날짜
            'DEFAULT CURRENT_TIME',     # 기본값 현재 시간
            'DEFAULT USER',             # 기본값 현재 사용자
            'COMPUTED BY',             # 계산된 컬럼
        ]
        
        # 테이블 레이아웃 설정
        self.columns_table.horizontalHeader().setStretchLastSection(True)
        self.columns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.columns_table.verticalHeader().setDefaultSectionSize(40)
        self.columns_table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 테이블 표시 설정
        self.columns_table.setWordWrap(True)
        self.columns_table.setTextElideMode(Qt.ElideNone)
        self.columns_table.setMouseTracking(False)  # 마우스 트래킹 비활성화
        
        # 크기 정책 설정
        self.columns_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 셀 더블클릭 이벤트 연결
        self.columns_table.cellDoubleClicked.connect(self.handle_cell_double_click)

    def handle_cell_double_click(self, row, column):
        """셀 더블클릭 처리"""
        if column in [1, 2]:  # 데이터 타입 또는 제약조건 컬럼
            combo = QComboBox()
            if column == 1:  # 데이터 타입
                combo.addItems(self.data_types)
            else:  # 제약조건
                combo.addItems(self.constraints)
            
            # 현재 셀의 값을 콤보박스의 현재 항목으로 설정
            current_text = self.columns_table.item(row, column).text()
            index = combo.findText(current_text)
            if index >= 0:
                combo.setCurrentIndex(index)
            
            # 콤보박스 스타일 설정
            combo.setStyleSheet(get_input_style(combo_min_height=1))
            
            # 콤보박스를 테이블 셀에 맞게 설정
            self.columns_table.setCellWidget(row, column, combo)
            
            # 콤보박스 선택 변경 시 이벤트 처리
            combo.currentTextChanged.connect(
                lambda text, r=row, c=column: self.handle_combo_changed(r, c, text))
            
            # 콤보박스 팝업이 닫힐 때 이벤트 처리
            combo.hidePopup = lambda r=row, c=column, orig=combo.hidePopup: self.handle_popup_closed(r, c, orig)
            
            # 콤보박스에 포커스 설정
            combo.showPopup()

    def handle_popup_closed(self, row, column, original_hide_popup):
        """콤보박스 팝업이 닫힐 때 처리"""
        combo = self.columns_table.cellWidget(row, column)
        if combo:
            # 원래의 hidePopup 메서드 실행
            original_hide_popup()
            
            # 현재 선택된 값으로 셀 업데이트
            current_text = combo.currentText()
            self.handle_combo_changed(row, column, current_text)

    def handle_combo_changed(self, row, column, text):
        """콤보박스 선택 변경 처리"""
        # 콤보박스 제거하고 선택된 값을 테이블 셀에 설정
        self.columns_table.removeCellWidget(row, column)
        self.columns_table.setItem(row, column, QTableWidgetItem(text))

    def add_column(self):
        """컬럼 행 추가"""
        row = self.columns_table.rowCount()
        self.columns_table.insertRow(row)
        
        # 빈 셀 추가
        for col in range(3):
            item = QTableWidgetItem("")
            if col == 0:  # 컬럼명
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.columns_table.setItem(row, col, item)

    def remove_column(self):
        """컬럼 행 삭제"""
        current_row = self.columns_table.currentRow()
        if current_row >= 0:
            self.columns_table.removeRow(current_row)
    
    def create_column(self):
        """컬럼 추가"""
        try:
            column_info = self.get_info()
            if column_info:
                if self.database_service.add_column(self.table_name, column_info):
                    QMessageBox.information(self, "성공", "컬럼이 추가되었습니다.")
                    super().accept()
                else:
                    QMessageBox.warning(self, "실패", "컬럼 추가에 실패했습니다.")
            else:
                QMessageBox.warning(self, "경고", "추가할 컬럼 정보가 없습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"컬럼 추가 중 오류 발생: {str(e)}")
            
    def drop_column(self):
        """컬럼 삭제"""
        selected_items = self.columns_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "삭제할 컬럼을 선택해주세요.")
            return
        
        column_name = selected_items[0].text()
        
        reply = QMessageBox.question(
            self, 
            "확인", 
            f"정말로 '{column_name}' 컬럼을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.database_service.drop_column(self.table_name, column_name):
                QMessageBox.information(self, "성공", "컬럼이 삭제되었습니다.")
                super().accept()
            else:
                QMessageBox.warning(self, "실패", "컬럼 삭제에 실패했습니다.")

    def get_info(self):
        """모드에 따른 정보를 반환"""
        if self.mode == self.MODE_CREATE_TABLE:
            return self.get_table_info()
        elif self.mode == self.MODE_CREATE_COLUMN:
            return self.get_column_info()
        else:
            self.logger.error(f"Invalid mode: {self.mode}")
            return None

    def get_table_info(self):
        """테이블 생성 정보 반환"""
        columns = []
        for row in range(self.columns_table.rowCount()):
            column = {
                'name': self.columns_table.item(row, 0).text() if self.columns_table.item(row, 0) else '',
                'type': self.columns_table.item(row, 1).text() if self.columns_table.item(row, 1) else '',
                'constraints': self.columns_table.item(row, 2).text() if self.columns_table.item(row, 2) else ''
            }
            if column['name']:  # 컬럼명이 있는 경우만 추가
                columns.append(column)
        return {
            'table_name': self.table_name_input.text(),
            'columns': columns
        }
            
    def get_column_info(self):
        """컬럼 정보 반환 (컬럼 추가 모드)"""
        if self.columns_table.rowCount() > 0:
            column = self._get_column_data(0)
            if column['name']:
                # 컬럼 정의 문자열 생성
                column_definition = f"{column['name']} {column['type']} {column['constraints']}".strip()
                return column_definition
        return None
            
    def _get_column_data(self, row):
        """행의 컬럼 데이터 추출"""
        name_item = self.columns_table.item(row, 0)
        type_item = self.columns_table.item(row, 1)
        constraint_item = self.columns_table.item(row, 2)
        
        # cellWidget이 있는지 먼저 확인
        type_widget = self.columns_table.cellWidget(row, 1)
        constraint_widget = self.columns_table.cellWidget(row, 2)
        
        return {
            'name': name_item.text() if name_item else '',
            'type': (type_widget.currentText() if isinstance(type_widget, QComboBox) 
                    else (type_item.text() if type_item else '')),
            'constraints': (constraint_widget.currentText() if isinstance(constraint_widget, QComboBox)
                        else (constraint_item.text() if constraint_item else ''))
        }

class AddDataDialog(QDialog):
    """데이터 추가 다이얼로그"""
    def __init__(self, parent, table_name, database_service):
        super().__init__(parent)
        self.table_name = table_name
        self.database_service = database_service
        self.logger = setup_logger(__name__)
        self.setup_ui()
        self.load_column_info()
        self.apply_styles()

    def accept(self):
        """확인 버튼 클릭 시 처리"""
        try:
            # 입력된 데이터 수집
            data = self.get_input_data()
            
            # 데이터베이스에 추가
            self.database_service.add_table_data(self.table_name, data)
            
            QMessageBox.information(self, "성공", "데이터가 추가되었습니다.")
            super().accept()
            
        except Exception as e:
            self.logger.error(f"데이터 추가 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"데이터 추가 실패: {str(e)}")

    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle(f"데이터 추가 - {self.table_name}")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 스크롤 내부 위젯
        scroll_content = QWidget()
        self.form_layout = QFormLayout(scroll_content)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)

        # 버튼
        buttons = QHBoxLayout()
        self.ok_btn = QPushButton("확인")
        cancel_btn = QPushButton("취소")
        self.ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(self.ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def load_column_info(self):
        """컬럼 정보 로드 및 입력 필드 생성"""
        try:
            columns_info = self.database_service.database_model.get_table_columns(self.table_name)
            self.input_fields = {}

            for col in columns_info:
                column_name = col['column_name'].strip()
                data_type = col['data_type']
                nullable = not col.get('not_null', False)
                
                # 라벨 생성 (필수 입력 표시)
                label_text = f"{column_name}{'*' if not nullable else ''}"
                
                # 입력 위젯 생성
                if data_type == 37:  # VARCHAR
                    widget = QLineEdit()
                elif data_type == 7:  # SMALLINT
                    widget = QSpinBox()
                    widget.setRange(-32768, 32767)
                elif data_type == 8:  # INTEGER
                    widget = QSpinBox()
                    widget.setRange(-2147483648, 2147483647)
                elif data_type == 12:  # DATE
                    widget = QDateEdit()
                    widget.setCalendarPopup(True)
                    widget.setDate(QDate.currentDate())
                elif data_type == 13:  # TIME
                    widget = QTimeEdit()
                    widget.setTime(QTime.currentTime())
                elif data_type == 35:  # TIMESTAMP
                    widget = QDateTimeEdit()
                    widget.setCalendarPopup(True)
                    widget.setDateTime(QDateTime.currentDateTime())
                else:
                    widget = QLineEdit()

                self.input_fields[column_name] = widget
                self.form_layout.addRow(label_text, widget)

        except Exception as e:
            self.logger.error(f"컬럼 정보 로드 실패: {str(e)}")
            QMessageBox.warning(self, "오류", "컬럼 정보를 불러오는데 실패했습니다.")

    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(get_dialog_style())
        
        # 버튼 스타일 적용
        for button in self.findChildren(QPushButton):
            button.setStyleSheet(get_button_style())
        
        # 입력 위젯 스타일 적용
        for widget in self.findChildren(QLineEdit):
            widget.setStyleSheet(get_input_style())

        for widget in self.findChildren(QSpinBox):
            widget.setStyleSheet(get_input_style())
        
        for widget in self.findChildren(QDateEdit):
            widget.setStyleSheet(get_input_style())

        for widget in self.findChildren(QTimeEdit):
            widget.setStyleSheet(get_input_style())

        for widget in self.findChildren(QDateTimeEdit):
            widget.setStyleSheet(get_input_style())

    def get_input_data(self):
        """입력된 데이터 수집"""
        data = {}
        for column_name, widget in self.input_fields.items():
            if isinstance(widget, QLineEdit):
                value = widget.text()
            elif isinstance(widget, QSpinBox):
                value = widget.value()
            elif isinstance(widget, (QDateEdit, QTimeEdit, QDateTimeEdit)):
                value = widget.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            else:
                value = str(widget.text())
            data[column_name] = value
        return data

class TableManagerDialog(QDialog):
    """테이블 관리 다이얼로그"""
    def __init__(self, table_manager, database_service, parent=None):
        super().__init__(parent)
        self.table_manager = table_manager
        self.database_service = database_service
        self.logger = setup_logger(__name__)
        self.setup_ui()
        self.load_tables()
        self.apply_styles()
            
    def setup_ui(self):
        """UI 초기화"""
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
        refresh_btn.clicked.connect(self.refresh_tables)
        refresh_btn.setStyleSheet(get_button_style(background_color="#2c3e50"))
        table_select_layout.addWidget(self.table_combo, stretch=1)
        table_select_layout.addWidget(refresh_btn)
        
        # 테이블 관리 버튼 그룹
        table_control_group = QGroupBox("테이블 관리")
        table_btn_layout = QHBoxLayout(table_control_group)
        
        # 주요 테이블 관리 버튼
        main_table_buttons = QHBoxLayout()
        create_btn = QPushButton("테이블 생성")
        drop_table_btn = QPushButton("테이블 삭제")
        create_column_btn = QPushButton("컬럼 추가")
        drop_column_btn = QPushButton("컬럼 삭제")  # 새로운 버튼 추가
        
        create_btn.clicked.connect(self.show_create_table_dialog)
        drop_table_btn.clicked.connect(self.drop_table)
        create_column_btn.clicked.connect(lambda: self.show_column_dialog(CreateTableDialog.MODE_CREATE_COLUMN))
        drop_column_btn.clicked.connect(lambda: self.show_column_dialog(CreateTableDialog.MODE_DROP_COLUMN))
        
        main_table_buttons.addWidget(create_btn)
        main_table_buttons.addWidget(drop_table_btn)
        main_table_buttons.addWidget(create_column_btn)
        main_table_buttons.addWidget(drop_column_btn)
        main_table_buttons.addStretch()
        
        # 보조 테이블 관리 버튼
        sub_table_buttons = QHBoxLayout()
        recreate_btn = QPushButton("테이블 재생성")
        create_all_btn = QPushButton("모든 테이블 생성")
        
        recreate_btn.clicked.connect(self.recreate_table)
        create_all_btn.clicked.connect(self.create_all_tables)
        
        # 보조 버튼 스타일 설정
        for btn in [recreate_btn, create_all_btn]:
            btn.setFixedWidth(120)
            btn.setStyleSheet(get_button_style(background_color="#34495e"))
        
        sub_table_buttons.addWidget(recreate_btn)
        sub_table_buttons.addWidget(create_all_btn)
        
        table_btn_layout.addLayout(main_table_buttons, stretch=2)
        table_btn_layout.addLayout(sub_table_buttons, stretch=1)
        
        # 데이터 관리 버튼 그룹
        data_control_group = QGroupBox("데이터 관리")
        data_btn_layout = QHBoxLayout(data_control_group)
        
        view_data_btn = QPushButton("데이터 조회")
        add_data_btn = QPushButton("데이터 추가")
        self.delete_btn = QPushButton("선택 항목 삭제")
        self.save_changes_btn = QPushButton("변경사항 저장")
        
        view_data_btn.clicked.connect(self.view_table_data)
        add_data_btn.clicked.connect(self.show_add_data_dialog)
        self.delete_btn.clicked.connect(self.delete_selected_items)
        self.save_changes_btn.clicked.connect(self.save_changes)
        
        # 데이터 조회 버튼 강조
        view_data_btn.setStyleSheet(get_button_style(background_color="#2980b9"))
        
        self.delete_btn.setEnabled(False)
        self.save_changes_btn.setEnabled(False)
        
        data_btn_layout.addWidget(view_data_btn)
        data_btn_layout.addWidget(add_data_btn)
        data_btn_layout.addWidget(self.delete_btn)
        data_btn_layout.addWidget(self.save_changes_btn)
        
        top_control.addWidget(table_select_group, stretch=1)
        top_control.addWidget(table_control_group, stretch=2)
        
        # 테이블 위젯 설정
        self.data_table = QTableWidget()
        self.setup_data_table()
        
        # 전체 레이아웃 구성
        main_layout.addLayout(top_control)
        main_layout.addWidget(data_control_group)
        main_layout.addWidget(self.data_table)

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

    def show_create_table_dialog(self):
        """테이블 생성 다이얼로그 표시"""
        dialog = CreateTableDialog(self, mode=CreateTableDialog.MODE_CREATE_TABLE)
        if dialog.exec_() == QDialog.Accepted:
            try:
                table_info = dialog.get_info()
                if table_info and self.database_service.create_custom_table(table_info):
                    QMessageBox.information(self, "성공", "테이블이 생성되었습니다.")
                    self.load_tables()
                else:
                    QMessageBox.warning(self, "실패", "테이블 생성에 실패했습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"테이블 생성 중 오류 발생: {str(e)}")

    def show_column_dialog(self, mode):
        """컬럼 관리 다이얼로그 표시"""
        table_name = self.table_combo.currentText()
        if not table_name:
            QMessageBox.warning(self, "경고", "테이블을 선택해주세요.")
            return

        dialog = CreateTableDialog(
            self, 
            mode=mode, 
            table_name=table_name,
            database_service=self.database_service
        )
        
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_tables()
            self.view_table_data()
            
    def setup_data_table(self):
        """데이터 테이블 설정"""
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.data_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.data_table.itemChanged.connect(self.on_item_changed)
        
        # 테이블 레이아웃 설정
        self.data_table.horizontalHeader().setStretchLastSection(False)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.data_table.verticalHeader().setDefaultSectionSize(40)
        self.data_table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 테이블 표시 설정
        self.data_table.setWordWrap(True)
        self.data_table.setTextElideMode(Qt.ElideNone)
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def refresh_tables(self):
        """테이블 목록 새로고침"""
        current_table = self.table_combo.currentText()
        self.table_combo.clear()
        self.load_tables()
        
        # 이전 선택 테이블이 있으면 다시 선택
        if current_table:
            index = self.table_combo.findText(current_table)
            if index >= 0:
                self.table_combo.setCurrentIndex(index)

    def show_add_data_dialog(self):
        """데이터 추가 다이얼로그 표시"""
        current_table = self.table_combo.currentText()
        if not current_table:
            QMessageBox.warning(self, "경고", "테이블을 선택해주세요.")
            return

        dialog = AddDataDialog(self, current_table, self.database_service)
        if dialog.exec_() == QDialog.Accepted:
            self.view_table_data()  # 테이블 데이터 새로고침

    def on_item_changed(self, item):
        """테이블 아이템 변경 시 처리"""
        self.delete_btn.setEnabled(True)
        self.save_changes_btn.setEnabled(True)
        
    def save_changes(self):
        """변경사항 저장"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return

        try:
            # 변경된 데이터 수집
            updated_data = []
            for row in range(self.data_table.rowCount()):
                row_data = {}
                for col in range(self.data_table.columnCount()):
                    header = self.data_table.horizontalHeaderItem(col).text()
                    item = self.data_table.item(row, col)
                    value = item.text() if item else ""
                    row_data[header] = value
                updated_data.append(row_data)

            # 데이터 업데이트
            if self.database_service.update_table_data(table_name, updated_data):
                self.save_changes_btn.setEnabled(False)
                QMessageBox.information(self, "성공", "변경사항이 저장되었습니다.")
            else:
                QMessageBox.warning(self, "실패", "변경사항 저장에 실패했습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 중 오류 발생: {str(e)}")

    def drop_table(self):
        """테이블 삭제"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return
        
        reply = QMessageBox.question(
            self, "확인", 
            f"정말로 '{table_name}' 테이블을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
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

        self.data_table.resizeColumnsToContents()
        
        # 이전 선택 테이블 복원
        if current_table:
            index = self.table_combo.findText(current_table)
            if index >= 0:
                self.table_combo.setCurrentIndex(index)
                
    def on_table_selected(self):
        """테이블 선택 시 데이터 조회"""
        self.view_table_data()
                
    def view_table_data(self):
        """이블 데이터 조회"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return
        
        try:
            # 먼저 테이블의 컬럼 구조 조회
            columns = self.database_service.get_table_structure(table_name)
            if not columns:
                self.data_table.setRowCount(0)
                self.data_table.setColumnCount(0)
                return
            
            # 컬럼 설정
            self.data_table.setColumnCount(len(columns))
            self.data_table.setHorizontalHeaderLabels(columns)
            
            # 테이블 데이터 조회
            data = self.database_service.get_table_data(table_name)
            if data:
                # 데이터가 있는 경우 행 추가
                self.data_table.setRowCount(len(data))
                for row_idx, row_data in enumerate(data):
                    for col_idx, (column, value) in enumerate(row_data.items()):
                        item = QTableWidgetItem(str(value) if value is not None else "")
                        self.data_table.setItem(row_idx, col_idx, item)
            else:
                # 데이터가 없는 경우 빈 테이블 표시
                self.data_table.setRowCount(0)
            
            # 컬럼 크 자동 조정
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
        """든 테이블 생성"""
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