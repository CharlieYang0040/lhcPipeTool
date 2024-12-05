"""메인 윈도우"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QMessageBox, QToolBar, QStyle, QApplication,
    QLabel, QSizePolicy
)
from .project_tree import ProjectTreeWidget
from .version_table import VersionTableWidget
from .detail_panel import DetailPanel

from ..models.project import Project
from ..models.sequence import Sequence
from ..models.shot import Shot
from ..models.version_models import ShotVersion, SequenceVersion, ProjectVersion
from ..models.worker import Worker
from ..models.refresh import Refresh
from ..models.database import Database

from ..services.project_service import ProjectService
from ..services.worker_service import WorkerService
from ..services.refresh_service import RefreshService
from ..services.database_service import DatabaseService
from ..services.version_services import (ShotVersionService, SequenceVersionService, ProjectVersionService)
from ..services.settings_service import SettingsService

from ..database.table_manager import TableManager
from ..utils.logger import setup_logger
from ..utils.decorators import require_admin
from ..config.app_state import AppState
from ..styles.components import get_toolbar_style

class MainWindow(QMainWindow):
    def __init__(self, db_connector):
        super().__init__()
        self.db_connector = db_connector
        self.logger = setup_logger(__name__)
        self.require_admin = require_admin(db_connector)
        self.app_state = AppState()
        if not self.db_connector.connection and not self.db_connector.connect():
            self.logger.error("데이터베이스 연결 실패")
            raise Exception("데이터베이스 연결 실패")
        
        self.table_manager = TableManager(db_connector)
        
        # 서비스 초기화
        # self.worker_service 초기화
        self.worker_service = WorkerService(Worker(db_connector))
        
        # self.project_service 초기화
        self.project_service = ProjectService(
            Project(db_connector), 
            Sequence(db_connector), 
            Shot(db_connector), 
            {
                "shot": ShotVersion(db_connector),
                "sequence": SequenceVersion(db_connector),
                "project": ProjectVersion(db_connector)
            }, 
            self.worker_service
        )
        
        # self.version_services 초기화
        self.version_services = {
            "shot": ShotVersionService(
                ShotVersion(db_connector), 
                self.worker_service
            ),
            "sequence": SequenceVersionService(
                SequenceVersion(db_connector), 
                self.worker_service
            ),
            "project": ProjectVersionService(
                ProjectVersion(db_connector), 
                self.worker_service
            )
        }
        
        # self.refresh_service 초기화
        self.refresh_service = RefreshService(
            Refresh(db_connector), 
            self.project_service, 
            self.version_services, 
            self.app_state.current_worker['id']
        )
        
        # self.database_service 초기화
        self.database_service = DatabaseService(Database(db_connector))

        # self.settings_service 초기화
        self.settings_service = SettingsService(db_connector)
        
        self.table_manager.initialize_settings()
        self.init_ui()
        self.setup_menu()
    
    def init_ui(self):
        """UI 초기화"""
        # 화면 정보 가져오기
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        # 윈도우 크기 계산 (화면 크기의 75%)
        window_width = int(screen_width * 0.60)
        window_height = int(screen_height * 0.75)
        
        # 윈도우 위치 계산 (화면 중앙)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.setWindowTitle("Pipeline Tool")
        self.setGeometry(x, y, window_width, window_height)
        
        # 메인 위젯 및 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 툴바 추가
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 툴바 스타일 수정
        toolbar.setStyleSheet(get_toolbar_style())
        
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
        
        # 툴바 오른쪽에 로그인 정보 추가
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # 로그인 정보 레이블 추가
        self.login_info = QLabel()
        self.login_info.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                padding: 0 10px;
                font-size: 12px;
            }
        """)
        self.update_login_info()  # 로그인 정보 업데이트
        toolbar.addWidget(self.login_info)
        
        # 스플리터 생성
        splitter = QSplitter()
        layout.addWidget(splitter)
        
        # 스플리터 비율 설정
        splitter.setStretchFactor(1, 2)  # 프로젝트 트리
        splitter.setStretchFactor(1, 2)  # 버전 테이블
        splitter.setStretchFactor(1, 2)  # 상세 정보 패널
        
        # 프로젝트 트리
        self.project_tree = ProjectTreeWidget(self.project_service, self.version_services, self.settings_service)
        splitter.addWidget(self.project_tree)
        
        # 버전 테이블
        self.version_table = VersionTableWidget(self.version_services, self.settings_service, self.project_tree)
        splitter.addWidget(self.version_table)
        
        # 상세 정보 패널
        self.detail_panel = DetailPanel(self.project_service, self.version_services)
        splitter.addWidget(self.detail_panel)
        
        # 메인 윈도우 스타일 수정
        self.setStyleSheet("""
            QMainWindow {
                background-color: #15151e;
            }
            QSplitter {
                background-color: #15151e;
            }
            QSplitter::handle {
                background-color: #2d2d3d;
            }
            QMenuBar {
                background-color: #15151e;
                color: #e0e0e0;
            }
            QMenuBar::item:selected {
                background-color: #2d2d3d;
            }
            QMenu {
                background-color: #15151e;
                color: #e0e0e0;
                border: 1px solid #2d2d3d;
            }
            QMenu::item:selected {
                background-color: #2d2d3d;
            }
        """)
        
        # 시그널 연결
        self.project_tree.item_selected.connect(self.handle_item_selection)
        self.project_tree.item_type_changed.connect(self.handle_item_type_changed)
        self.version_table.version_selected.connect(self.handle_version_selection)

    def setup_menu(self):
        """메뉴바 설정"""
        menubar = self.menuBar()
        
        # 프로젝트 메뉴
        project_menu = menubar.addMenu('프로젝트')
        new_project_action = project_menu.addAction('새 프로젝트')
        new_project_action.triggered.connect(self.show_new_project_dialog)
        new_sequence_action = project_menu.addAction('새 시퀀스')
        new_sequence_action.triggered.connect(self.show_new_sequence_dialog)
        new_shot_action = project_menu.addAction('새 샷')
        new_shot_action.triggered.connect(self.show_new_shot_dialog)
        new_version_action = project_menu.addAction('새 버전')
        new_version_action.triggered.connect(self.show_new_version_dialog)
        
        # 버전 메뉴
        manager_menu = menubar.addMenu('관리자')
        render_manager_action = manager_menu.addAction('렌더 관리자')
        render_manager_action.triggered.connect(self.show_render_manager)
        manage_workers_action = manager_menu.addAction('작업자 관리자')
        manage_workers_action.triggered.connect(self.show_worker_manager)
        table_manager_action = manager_menu.addAction('테이블 관리자')
        table_manager_action.triggered.connect(self.show_table_manager)
        
        # 설정 메뉴
        settings_menu = menubar.addMenu('설정')
        settings_action = settings_menu.addAction('설정')
        settings_action.triggered.connect(self.show_settings_dialog)

    def show_new_project_dialog(self):
        """새 프로젝트 다이얼로그"""
        from .new_project_dialog import NewProjectDialog
        dialog = NewProjectDialog(self.project_service, self)
        dialog.exec_()

    def show_new_sequence_dialog(self, project_id, sequence=None):
        """시퀀스 생성/편집 다이얼로그"""
        from .new_sequence_dialog import SequenceDialog
        dialog = SequenceDialog(self.project_service, project_id, sequence, self)
        dialog.exec_()

    def show_new_shot_dialog(self, sequence_id, shot=None):
        """샷 생성/편집 다이얼로그"""
        from .new_shot_dialog import ShotDialog
        dialog = ShotDialog(self.project_service, sequence_id, shot, self)
        dialog.exec_()

    def show_new_version_dialog(self):
        """새 버전 다이얼로그"""
        if not self.app_state.current_item_id:
            QMessageBox.warning(self, "경고", "아이템을 선택해주세요.")
            return
            
        from .new_version_dialog import NewVersionDialog
        dialog = NewVersionDialog(
            self.db_connector, 
            self.project_tree,
            self.app_state.current_item_id, 
            self.app_state.current_item_type, 
            self
        )
        dialog.exec_()

    def show_render_manager(self):
        """렌더 관리자 다이얼로그"""
        if not self.app_state.current_item_id or self.app_state.current_item_type != "shot":
            QMessageBox.warning(self, "경고", "샷을 선택해주세요.")
            return
            
        from .render_manager_dialog import RenderManagerDialog
        dialog = RenderManagerDialog(
            self.version_services[self.app_state.current_item_type], 
            self.app_state.current_item_id, 
            self
        )
        dialog.exec_()

    def show_settings_dialog(self):
        """설정 다이얼로그"""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(
            self.project_service, 
            self.settings_service, 
            self.version_services, 
            self
        )
        dialog.exec_()

    # @require_admin
    def show_worker_manager(self):
        """작업자 관리 다이얼로그"""
        from .worker_manager_dialog import WorkerManagerDialog
        dialog = WorkerManagerDialog(self.worker_service, self)
        dialog.exec_()

    # @require_admin
    def show_table_manager(self):
        """테이블 관리 다이얼로그"""
        from .table_manager_dialog import TableManagerDialog
        dialog = TableManagerDialog(self.table_manager, self.database_service, self)
        dialog.exec_()

    @require_admin
    def refresh_project_structure(self):
        """프로젝트 구조 새로고침"""
        if self.refresh_service.refresh_project_structure(self):
            self.logger.info("UI 새로고침")
            self.project_tree.load_projects()

    def show_database_contents(self):
        """데이터베이스 내용 출력"""
        self.database_service.show_database_contents(self)

    @require_admin
    def clear_database(self):
        """데이터베이스 초기화"""
        if self.database_service.clear_database(self):
            self.project_tree.clear()

    def handle_item_selection(self, item_id):
        """아이템 선택 처리"""
        if item_id == -1:
            self.version_table.clear_versions()
        else:
            self.version_table.load_versions(item_id)

    def handle_version_selection(self, item_id):
        """버전테이블에서 버전 선택 처리"""
        self.detail_panel._show_version_fields(item_id)

    def handle_item_type_changed(self, item_type, item_id):
        """아이템 타입 변경 처리"""
        self.detail_panel.show_item_details(item_type, item_id)

    def update_login_info(self):
        """로그인 정보 업데이트"""
        user = self.app_state.current_worker
        if user:
            info_text = f"사용자: {user['name']} ({user['id']}) | 권한: {user['role']}"
            self.login_info.setText(info_text)