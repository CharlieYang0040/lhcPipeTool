# main.py

import sys
from PySide6.QtWidgets import QApplication
from file_manager import FileManager
from worker_manager import WorkerManager
from ui_main import MainWindow
from utils import get_base_path

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 기본 경로 설정
    base_path = get_base_path()

    # 파일 매니저 및 작업자 매니저 생성
    file_manager = FileManager(base_path)
    worker_manager = WorkerManager(file_manager)

    # 메인 윈도우 생성
    window = MainWindow()

    # 버전 및 작업자 등록 버튼 클릭 시 실행되는 함수 연결
    def add_version():
        selected_item = window.tree_widget.currentItem()
        if selected_item:
            shot_name = selected_item.text(0)
            sequence_name = selected_item.parent().text(0)
            version = window.version_input.text()
            worker = window.worker_input.text()

            if version and worker:
                worker_manager.add_version(sequence_name, shot_name, version, worker)
                worker_manager.add_worker(worker)
                window.add_shot_info(shot_name, version, worker)
    
    window.add_button.clicked.connect(add_version)

    # 트리 뷰에서 폴더 구조 로드
    def load_projects():
        file_manager.load_projects(window.tree_widget)
    
    window.tree_widget.itemClicked.connect(load_projects)
    window.show()
    sys.exit(app.exec())