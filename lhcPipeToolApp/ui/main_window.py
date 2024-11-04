"""메인 윈도우"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QMenuBar, QMenu, QDialog, QMessageBox, QToolBar, QStyle, QTextEdit
)
from PySide6.QtCore import Qt
from pathlib import Path
from .project_tree import ProjectTreeWidget
from .version_table import VersionTableWidget
from .detail_panel import DetailPanel
from ..services.project_service import ProjectService
from ..services.version_service import VersionService
from ..services.worker_service import WorkerService
from ..database.table_manager import TableManager
from ..utils.logger import setup_logger

class MainWindow(QMainWindow):
    def __init__(self, db_connector):
        super().__init__()
        self.db_connector = db_connector
        self.logger = setup_logger(__name__)
        
        if not self.db_connector.connection and not self.db_connector.connect():
            self.logger.error("데이터베이스 연결 실패")
            raise Exception("데이터베이스 연결 실패")
        
        self.table_manager = TableManager(db_connector)
        
        # # 테이블 생성 및 컬럼 추가
        # self.table_manager.create_all_tables()
        # self.table_manager.add_path_columns()
        
        # 서비스 초기화
        self.project_service = ProjectService(db_connector)
        self.version_service = VersionService(db_connector)
        self.worker_service = WorkerService(db_connector)
        
        # settings 테이블 초기화
        self.table_manager.initialize_settings()
        
        self.init_ui()
        self.setup_menu()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Pipeline Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # 메인 위젯 및 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 툴바 추가
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 새로고침 버튼
        refresh_action = toolbar.addAction("새로고침")
        refresh_action.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_action.triggered.connect(self.refresh_project_structure)
        
        # DB 출력 버튼
        show_db_action = toolbar.addAction("DB 출력")
        show_db_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogInfoView))
        show_db_action.triggered.connect(self.show_database_contents)
        
        # DB 초기화 버튼
        clear_db_action = toolbar.addAction("DB 초기화")
        clear_db_action.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        clear_db_action.triggered.connect(self.clear_database)
        
        # 스플리터 생성
        splitter = QSplitter()
        layout.addWidget(splitter)
        
        # 프로젝트 트리
        self.project_tree = ProjectTreeWidget(self.db_connector)
        splitter.addWidget(self.project_tree)
        
        # 버전 테이블
        self.version_table = VersionTableWidget(self.db_connector)
        splitter.addWidget(self.version_table)
        
        # 상세 정보 패널
        self.detail_panel = DetailPanel(self.db_connector)
        splitter.addWidget(self.detail_panel)
        
        # 시그널 연결
        self.project_tree.shot_selected.connect(self.handle_shot_selection)
        self.version_table.version_selected.connect(self.detail_panel.show_version_details)

    def setup_menu(self):
        """메뉴바 설정"""
        menubar = self.menuBar()
        
        # 프로젝트 메뉴
        project_menu = menubar.addMenu('프로젝트')
        new_project_action = project_menu.addAction('새 프로젝트')
        new_project_action.triggered.connect(self.show_new_project_dialog)
        
        # 버전 메뉴
        version_menu = menubar.addMenu('버전')
        new_version_action = version_menu.addAction('새 버전')
        new_version_action.triggered.connect(self.show_new_version_dialog)
        render_manager_action = version_menu.addAction('렌더 관리자')
        render_manager_action.triggered.connect(self.show_render_manager)
        
        # 작업자 메뉴
        worker_menu = menubar.addMenu('작업자')
        manage_workers_action = worker_menu.addAction('작업자 관리')
        manage_workers_action.triggered.connect(self.show_worker_manager)
        
        # 설정 메뉴
        settings_menu = menubar.addMenu('설정')
        settings_action = settings_menu.addAction('설정')
        settings_action.triggered.connect(self.show_settings_dialog)

    def show_new_project_dialog(self):
        """새 프로젝트 다이얼로그"""
        from .new_project_dialog import NewProjectDialog
        dialog = NewProjectDialog(self.project_service, self)
        if dialog.exec_() == QDialog.Accepted:
            self.project_tree.load_projects()

    def show_new_version_dialog(self):
        """새 버전 다이얼로그"""
        current_item = self.project_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "경고", "샷을 선택해주세요.")
            return
            
        item_type, shot_id = current_item.data(0, Qt.UserRole)
        if item_type != "shot":
            QMessageBox.warning(self, "경고", "샷을 선택해주세요.")
            return
            
        from .new_version_dialog import NewVersionDialog
        dialog = NewVersionDialog(self.version_service, shot_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.version_table.load_versions(shot_id)

    def show_render_manager(self):
        """렌더 관리자 다이얼로그"""
        current_item = self.project_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "경고", "샷을 선택해주세요.")
            return
            
        item_type, shot_id = current_item.data(0, Qt.UserRole)
        if item_type != "shot":
            QMessageBox.warning(self, "경고", "샷을 선택해주세요.")
            return
            
        from .render_manager_dialog import RenderManagerDialog
        dialog = RenderManagerDialog(self.version_service, shot_id, self)
        dialog.exec_()

    def show_settings_dialog(self):
        """설정 다이얼로그"""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.db_connector, self)
        dialog.exec_()

    def show_sequence_dialog(self, project_id, sequence=None):
        """시퀀스 생성/편집 다이얼로그"""
        from .sequence_dialog import SequenceDialog
        dialog = SequenceDialog(self.project_service, project_id, sequence, self)
        if dialog.exec_() == QDialog.Accepted:
            self.project_tree.load_projects()

    def show_shot_dialog(self, sequence_id, shot=None):
        """샷 생성/편집 다이얼로그"""
        from .shot_dialog import ShotDialog
        dialog = ShotDialog(self.project_service, sequence_id, shot, self)
        if dialog.exec_() == QDialog.Accepted:
            self.project_tree.load_projects()

    def show_worker_manager(self):
        """작업자 관리 다이얼로그"""
        from .worker_manager_dialog import WorkerManagerDialog
        dialog = WorkerManagerDialog(self.worker_service, self)
        dialog.exec_()

    def refresh_project_structure(self):
        """프로젝트 조 새로고침"""
        try:
            self.logger.info("프로젝트 구조 새로고침 시작")
            
            # 설정에서 프로젝트 루트 경로 가져오기
            cursor = self.db_connector.cursor()
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'project_root'")
            result = cursor.fetchone()
            
            if not result:
                self.logger.warning("프로젝트 루트 경로가 설정되지 않음")
                QMessageBox.warning(self, "경고", "프로젝트 루트 경로가 설정되지 않았습니다.")
                return
                
            root_path = Path(result[0])
            self.logger.info(f"프로젝트 루트 경로: {root_path}")
            
            if not root_path.exists():
                self.logger.error(f"프로젝트 루트 경로가 존재하지 않음: {root_path}")
                QMessageBox.warning(self, "경고", "프로젝트 루트 경로가 존재하지 않습니다.")
                return
                
            # 프로젝트 구조 동기화
            self.logger.info("프로젝트 구조 동기화 시작")
            self.sync_project_structure(root_path)
            
            # UI 새로고침
            self.logger.info("UI 새로고침")
            self.project_tree.load_projects()
            QMessageBox.information(self, "성공", "프로젝트 구조를 성공적으로 동기화했습니다.")
            self.logger.info("프로젝트 구조 새로고침 완료")
            
        except Exception as e:
            self.logger.error(f"프로젝트 구조 동기화 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "오류", f"프로젝트 구조 동기화 실패: {str(e)}")

    def sync_project_structure(self, root_path):
        """프로젝트 구조 동기화"""
        try:
            for project_dir in root_path.iterdir():
                if not project_dir.is_dir():
                    continue
                    
                # 프로젝트 생성 또는 업데이트
                project = self.project_service.get_project_by_name(project_dir.name)
                if not project:
                    project_id = self.project_service.create_project(
                        name=project_dir.name,
                        path=str(project_dir)
                    )
                else:
                    project_id = project[0]
                    self.project_service.update_project_path(project_id, str(project_dir))
                
                # 시퀀스 동기화
                self._sync_sequences(project_id, project_dir)
                
        except Exception as e:
            self.logger.error(f"프로젝트 구조 동기화 실패: {str(e)}")
            raise

    def _sync_sequences(self, project_id, project_dir):
        """시퀀스 동기화"""
        for seq_dir in project_dir.iterdir():
            if not seq_dir.is_dir():
                continue
                
            # 시퀀스 생성 또는 업데이트
            sequence = self.project_service.get_sequence_by_name(project_id, seq_dir.name)
            if not sequence:
                sequence_id = self.project_service.create_sequence(
                    project_id=project_id,
                    name=seq_dir.name
                )
            else:
                sequence_id = sequence[0]
                
            # 샷 동기화
            self.sync_shots(sequence_id, seq_dir)

    def sync_shots(self, sequence_id, seq_dir):
        """샷 동기화"""
        for shot_dir in seq_dir.iterdir():
            if not shot_dir.is_dir():
                continue
                
            # 샷 생성 또는 업데이트
            shot = self.project_service.get_shot_by_name(sequence_id, shot_dir.name)
            if not shot:
                shot_id = self.project_service.create_shot(
                    sequence_id=sequence_id,
                    name=shot_dir.name
                )
            else:
                shot_id = shot[0]
                
            # 버전 동기화
            self.sync_versions(shot_id, shot_dir)

    def sync_versions(self, shot_id, shot_dir):
        """버전 동기화"""
        for version_dir in shot_dir.glob('v*'):
            if not version_dir.is_dir():
                continue
                
            try:
                version_num = int(version_dir.name[1:])
                # 버전 생성 또는 업데이트
                version = self.version_service.get_version_by_id(shot_id)
                if not version:
                    self.version_service.create_version(
                        shot_id=shot_id,
                        worker_name="system",  # 시스템에 의한 자동 생성
                        file_path=str(version_dir),
                        comment="Auto-imported from filesystem"
                    )
            except ValueError:
                continue

    def show_database_contents(self):
        """데이터베이스 내용 출력"""
        try:
            cursor = self.db_connector.cursor()
            output = []
            
            # 원하는 테이블 순서 정의
            ordered_tables = ['PROJECTS', 'SEQUENCES', 'SHOTS', 'VERSIONS', 'WORKERS', 'SETTINGS']
            
            # 실제 존재하는 테이블 확인
            cursor.execute("""
                SELECT RDB$RELATION_NAME 
                FROM RDB$RELATIONS 
                WHERE RDB$SYSTEM_FLAG = 0
            """)
            existing_tables = {table[0].strip() for table in cursor.fetchall()}
            
            # 존재하는 테이블만 순서대로 처리
            for table in ordered_tables:
                if table in existing_tables:
                    output.append(f"\n=== {table} 테이블 ===")
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    # 컬럼명 조회
                    cursor.execute(f"""
                        SELECT RDB$FIELD_NAME 
                        FROM RDB$RELATION_FIELDS 
                        WHERE RDB$RELATION_NAME = '{table}'
                        ORDER BY RDB$FIELD_POSITION
                    """)
                    columns = [col[0].strip() for col in cursor.fetchall()]
                    
                    output.append("컬럼: " + ", ".join(columns))
                    for row in rows:
                        output.append(str(row))
            
            # 결과 표시
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("데이터베이스 내용")
            msg_box.setIcon(QMessageBox.Information)
            
            # 텍스트 에디터 위젯 생성 및 설정
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setMinimumWidth(600)
            text_edit.setMinimumHeight(400)
            
            # 테이블 내용을 HTML 형식으로 포맷팅
            html_content = "<pre style='font-family: Consolas, monospace;'>"
            for line in output:
                if line.startswith("==="): # 테이블 제목
                    html_content += f"<h3 style='color: blue;'>{line}</h3>"
                elif line.startswith("컬럼:"): # 컬럼 헤더
                    html_content += f"<p style='color: green;'>{line}</p>"
                else: # 데이터 행
                    html_content += f"{line}<br>"
            html_content += "</pre>"
            
            text_edit.setHtml(html_content)
            
            # 메시지 박스에 텍스트 에디터 추가
            msg_box.layout().addWidget(text_edit, 0, 0, 1, msg_box.layout().columnCount())
            msg_box.exec()
            
        except Exception as e:
            self.logger.error(f"데이터베이스 내용 조회 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"데이터베이스 내용 조회 실패: {str(e)}")

    def clear_database(self):
        """데이터베이스 초기화"""
        try:
            reply = QMessageBox.question(
                self, 
                "데이터베이스 초기화", 
                "정말로 모든 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.db_connector.cursor()
                
                # 외래 키 제약 조건 때문에 순서대로 삭제
                tables = ['versions', 'shots', 'sequences', 'projects']
                
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                
                self.db_connector.commit()
                self.project_tree.clear()
                QMessageBox.information(self, "성공", "데이터베이스가 초기화되었습니다.")
                
        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"데이터베이스 초기화 실패: {str(e)}")

    def handle_shot_selection(self, shot_id):
        """샷 선택 처리"""
        if shot_id == -1:
            self.version_table.clear_versions()
        else:
            self.version_table.load_versions(shot_id)