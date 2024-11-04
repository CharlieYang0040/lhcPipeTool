# ui_main.py

from PySide6.QtWidgets import QMainWindow, QTreeWidget, QVBoxLayout, QWidget, QSplitter, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QHBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Manager")
        self.setGeometry(100, 100, 800, 600)

        # 스플리터(좌측: 트리뷰, 우측: 테이블뷰 + 입력 필드)
        splitter = QSplitter()

        # 좌측 트리 뷰
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Project Structure"])
        splitter.addWidget(self.tree_widget)

        # 우측 패널 (테이블뷰 + 입력 필드)
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # 샷 정보 테이블 뷰 (샷 이름, 버전, 작업자)
        self.table_widget = QTableWidget(0, 3)
        self.table_widget.setHorizontalHeaderLabels(["Shot", "Version", "Worker"])
        right_layout.addWidget(self.table_widget)

        # 작업자 입력 필드
        self.worker_input = QLineEdit()
        self.version_input = QLineEdit()

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Version:"))
        input_layout.addWidget(self.version_input)
        input_layout.addWidget(QLabel("Worker:"))
        input_layout.addWidget(self.worker_input)
        right_layout.addLayout(input_layout)

        # 등록 버튼
        self.add_button = QPushButton("Add Version")
        right_layout.addWidget(self.add_button)

        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        # 메인 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(layout)
