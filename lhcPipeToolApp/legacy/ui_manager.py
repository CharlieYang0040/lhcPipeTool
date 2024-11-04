from PySide6.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout

class UIManager(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Firebird DB Manager")
        self.setGeometry(100, 100, 600, 400)

        # 메인 레이아웃
        layout = QVBoxLayout()

        # 작업자 추가 입력
        self.worker_input = QLineEdit()
        self.worker_input.setPlaceholderText("Enter worker name")
        self.add_worker_button = QPushButton("Add Worker")
        self.add_worker_button.clicked.connect(self.add_worker)
        layout.addWidget(QLabel("Add Worker:"))
        layout.addWidget(self.worker_input)
        layout.addWidget(self.add_worker_button)

        # 버전 추가 입력
        self.shot_input = QLineEdit()
        self.shot_input.setPlaceholderText("Enter shot name")
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("Enter version")
        self.worker_for_version_input = QLineEdit()
        self.worker_for_version_input.setPlaceholderText("Enter worker name for version")
        self.add_version_button = QPushButton("Add Version")
        self.add_version_button.clicked.connect(self.add_version)

        version_layout = QHBoxLayout()
        version_layout.addWidget(self.shot_input)
        version_layout.addWidget(self.version_input)
        version_layout.addWidget(self.worker_for_version_input)
        version_layout.addWidget(self.add_version_button)
        layout.addLayout(version_layout)

        # 데이터 조회 테이블
        self.table_widget = QTableWidget(0, 4)
        self.table_widget.setHorizontalHeaderLabels(["Shot", "Version", "Worker", "Created At"])
        layout.addWidget(self.table_widget)

        # 데이터 조회 버튼
        self.view_data_button = QPushButton("View Data")
        self.view_data_button.clicked.connect(self.view_data)
        layout.addWidget(self.view_data_button)

        # 메인 위젯 설정
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def add_worker(self):
        """작업자 추가"""
        worker_name = self.worker_input.text()
        if worker_name:
            self.db_manager.insert_worker(worker_name)
            self.worker_input.clear()

    def add_version(self):
        """버전 추가"""
        shot_name = self.shot_input.text()
        version = self.version_input.text()
        worker_name = self.worker_for_version_input.text()
        if shot_name and version and worker_name:
            self.db_manager.insert_version(shot_name, version, worker_name)
            self.shot_input.clear()
            self.version_input.clear()
            self.worker_for_version_input.clear()

    def view_data(self):
        """데이터 조회"""
        self.table_widget.setRowCount(0)
        data = self.db_manager.fetch_versions()
        for row_data in data:
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            for column, item in enumerate(row_data):
                self.table_widget.setItem(row_position, column, QTableWidgetItem(str(item)))
