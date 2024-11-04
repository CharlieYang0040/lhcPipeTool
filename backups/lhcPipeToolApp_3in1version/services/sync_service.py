import re
from pathlib import Path
from ..utils.logger import setup_logger
from .project_service import ProjectService
from .version_service import VersionService

class SyncService:
    def __init__(self, db_connector):
        self.connector = db_connector
        self.logger = setup_logger(__name__)
        self.project_service = ProjectService(db_connector)
        self.version_service = VersionService(db_connector)
        self.version_pattern = re.compile(r'^v\d{3}$')  # v + 정확히 3자리 숫자

    def sync_project_structure(self, root_path):
        """프로젝트 구조 동기화"""
        try:
            self.logger.info(f"프로젝트 구조 동기화 시작: {root_path}")
            root_path = Path(root_path)
            
            if not root_path.exists():
                raise FileNotFoundError(f"프로젝트 루트 경로가 존재하지 않습니다: {root_path}")
            
            for project_dir in root_path.iterdir():
                if not project_dir.is_dir():
                    continue
                    
                self._sync_project(project_dir)
                
            return True
            
        except Exception as e:
            self.logger.error(f"프로젝트 구조 동기화 실패: {str(e)}", exc_info=True)
            return False

    def _sync_project(self, project_dir):
        """개별 프로젝트 동기화"""
        try:
            # 프로젝트 생성 또는 업데이트
            project = self.project_service.get_project_by_name(project_dir.name)
            if not project:
                project_id = self.project_service.create_project(
                    name=project_dir.name,
                    path=str(project_dir)
                )
                self.logger.info(f"새 프로젝트 생성: {project_dir.name}")
            else:
                project_id = project[0]
                self.project_service.update_project_path(project_id, str(project_dir))
                self.logger.info(f"프로젝트 업데이트: {project_dir.name}")
            
            # 프로젝트 내용물 처리
            for item_dir in project_dir.iterdir():
                if not item_dir.is_dir():
                    continue
                    
                if self.version_pattern.match(item_dir.name):
                    self._sync_project_version(project_id, item_dir)
                else:
                    self._sync_sequence(project_id, item_dir)
                    
        except Exception as e:
            self.logger.error(f"프로젝트 동기화 실패: {project_dir.name} - {str(e)}")
            raise

    def _sync_project_version(self, project_id, version_dir):
        """프로젝트 버전 동기화"""
        try:
            # 버전 생성 시도
            success = self.version_service.create_version(
                version_type='project',
                id_value=project_id,
                worker_name="system",
                file_path=str(version_dir),
                comment="Auto-imported from filesystem"
            )
            if success:
                self.logger.info(f"프로젝트 버전 생성: {version_dir.name}")
            else:
                self.logger.warning(f"프로젝트 버전 생성 실패: {version_dir.name}")
        except Exception as e:
            self.logger.error(f"프로젝트 버전 동기화 실패: {str(e)}")

    def _sync_sequence(self, project_id, seq_dir):
        """시퀀스 동기화"""
        try:
            sequence = self.project_service.get_sequence_by_name(project_id, seq_dir.name)
            if not sequence:
                sequence_id = self.project_service.create_sequence(
                    project_id=project_id,
                    name=seq_dir.name
                )
                self.logger.info(f"새 시퀀스 생성: {seq_dir.name}")
            else:
                sequence_id = sequence[0]
                self.logger.info(f"시퀀스 업데이트: {seq_dir.name}")
            
            # 시퀀스 내용물 처리
            for item_dir in seq_dir.iterdir():
                if not item_dir.is_dir():
                    continue
                    
                if self.version_pattern.match(item_dir.name):
                    self._sync_sequence_version(sequence_id, item_dir)
                else:
                    self._sync_shot(sequence_id, item_dir)
                    
        except Exception as e:
            self.logger.error(f"시퀀스 동기화 실패: {seq_dir.name} - {str(e)}")
            raise

    def _sync_sequence_version(self, sequence_id, version_dir):
        """시퀀스 버전 동기화"""
        try:
            version_num = int(version_dir.name[1:])
            version = self.version_service.get_version_by_id(sequence_id)
            if not version:
                self.version_service.create_version(
                    version_type='sequence',
                    id_value=sequence_id,
                    worker_name="system",
                    file_path=str(version_dir),
                    comment="Auto-imported from filesystem"
                )
                self.logger.info(f"시퀀스 버전 생성: {version_dir.name}")
        except ValueError:
            self.logger.warning(f"잘못된 버전 폴더명: {version_dir.name}")

    def _sync_shot(self, sequence_id, shot_dir):
        """샷 동기화"""
        try:
            shot = self.project_service.get_shot_by_name(sequence_id, shot_dir.name)
            if not shot:
                shot_id = self.project_service.create_shot(
                    sequence_id=sequence_id,
                    name=shot_dir.name
                )
                self.logger.info(f"새 샷 생성: {shot_dir.name}")
            else:
                shot_id = shot[0]
                self.logger.info(f"샷 업데이트: {shot_dir.name}")
            
            # 샷 버전 처리
            for version_dir in shot_dir.glob('v[0-9][0-9][0-9]'):
                if version_dir.is_dir() and self.version_pattern.match(version_dir.name):
                    self._sync_shot_version(shot_id, version_dir)
                    
        except Exception as e:
            self.logger.error(f"샷 동기화 실패: {shot_dir.name} - {str(e)}")
            raise

    def _sync_shot_version(self, shot_id, version_dir):
        """샷 버전 동기화"""
        try:
            version_num = int(version_dir.name[1:])
            version = self.version_service.get_version_by_id(shot_id)
            if not version:
                self.version_service.create_version(
                    version_type='shot',
                    id_value=shot_id,
                    worker_name="system",
                    file_path=str(version_dir),
                    comment="Auto-imported from filesystem"
                )
                self.logger.info(f"샷 버전 생성: {version_dir.name}")
        except ValueError:
            self.logger.warning(f"잘못된 버전 폴더명: {version_dir.name}")