"""프로젝트 구조 새로고침 서비스"""
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

class RefreshService:
    def __init__(self, db_connector, project_service, version_service, logger):
        self.db_connector = db_connector
        self.project_service = project_service
        self.version_service = version_service
        self.logger = logger

    def refresh_project_structure(self, parent_widget):
        """프로젝트 구조 새로고침"""
        try:
            self.logger.info("프로젝트 구조 새로고침 시작")
            
            root_path = self._get_project_root()
            if not root_path:
                QMessageBox.warning(parent_widget, "경고", "프로젝트 루트 경로가 설정되지 않았습니다.")
                return False
                
            self.logger.info(f"프로젝트 루트 경로: {root_path}")
                
            # 프로젝트 구조 동기화
            self.logger.info("프로젝트 구조 동기화 시작")
            self.sync_project_structure(root_path)
            
            QMessageBox.information(parent_widget, "성공", "프로젝트 구조를 성공적으로 동기화했습니다.")
            self.logger.info("프로젝트 구조 새로고침 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"프로젝트 구조 동기화 실패: {str(e)}", exc_info=True)
            QMessageBox.critical(parent_widget, "오류", f"프로젝트 구조 동기화 실패: {str(e)}")
            return False

    def _get_project_root(self):
        """프로젝트 루트 경로 가져오기"""
        cursor = self.db_connector.cursor()
        cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'project_root'")
        result = cursor.fetchone()
        
        if not result:
            self.logger.warning("프로젝트 루트 경로가 설정되지 않음")
            return None
            
        root_path = Path(result[0])
        if not root_path.exists():
            self.logger.error(f"프로젝트 루트 경로가 존재하지 않음: {root_path}")
            return None
            
        return root_path

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
            self._sync_shots(sequence_id, seq_dir)

    def _sync_shots(self, sequence_id, seq_dir):
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
            self._sync_versions(shot_id, shot_dir)

    def _sync_versions(self, shot_id, shot_dir):
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