"""파일 관리 서비스"""
import os
import shutil
from pathlib import Path
from ..utils.logger import setup_logger
from ..services.settings_service import SettingsService
from ..services.version_services import (
    ProjectVersionService, 
    SequenceVersionService, 
    ShotVersionService
)

class FileManageService:
    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.logger = setup_logger(__name__)
        self.settings_service = SettingsService(db_connector)
        self.version_services = {
            "project": ProjectVersionService(db_connector, self.logger),
            "sequence": SequenceVersionService(db_connector, self.logger),
            "shot": ShotVersionService(db_connector, self.logger)
        }
        
    def get_version_path(self, item_type, item_id, version_number):
        """버전 경로 생성"""
        try:
            render_output = self.settings_service.get_setting('render_output')
            if not render_output:
                raise ValueError("렌더 출력 경로가 설정되지 않았습니다.")
                
            # 아이템 정보 가져오기
            if item_type == "project":
                details = self.version_services["project"].get_project_details(item_id)
                if not details:
                    raise ValueError(f"프로젝트를 찾을 수 없습니다: {item_id}")
                    
                path_components = [
                    render_output,
                    details['name'],
                    f"v{version_number:03d}"
                ]
            
            elif item_type == "sequence":
                details = self.version_services["sequence"].get_sequence_details(item_id)
                if not details:
                    raise ValueError(f"시퀀스를 찾을 수 없습니다: {item_id}")
                    
                path_components = [
                    render_output,
                    details['project_name'],
                    details['name'],
                    f"v{version_number:03d}"
                ]
            
            elif item_type == "shot":
                details = self.version_services["shot"].get_shot_details(item_id)
                if not details:
                    raise ValueError(f"샷을 찾을 수 없습니다: {item_id}")
                    
                path_components = [
                    render_output,
                    details['project_name'],
                    details['sequence_name'],
                    details['name'],
                    f"v{version_number:03d}"
                ]
            else:
                raise ValueError(f"잘못된 아이템 타입: {item_type}")
                
            return os.path.join(*path_components)
            
        except Exception as e:
            self.logger.error(f"버전 경로 생성 실패: {str(e)}")
            raise
            
    def create_version_directory(self, version_path):
        """버전 디렉토리 생성"""
        try:
            path = Path(version_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"버전 디렉토리 생성: {version_path}")
            return True
        except Exception as e:
            self.logger.error(f"버전 디렉토리 생성 실패: {str(e)}")
            return False
            
    def copy_file_to_version(self, source_file, version_path):
        """파일을 버전 디렉토리로 복사"""
        try:
            if not os.path.exists(source_file):
                raise FileNotFoundError(f"소스 파일을 찾을 수 없습니다: {source_file}")
                
            # 대상 디렉토리 생성
            self.create_version_directory(version_path)
            
            # 파일 이름 추출 및 대상 경로 생성
            file_name = os.path.basename(source_file)
            target_file = os.path.join(version_path, file_name)
            
            # 파일 복사
            shutil.copy2(source_file, target_file)
            self.logger.info(f"파일 복사 완료: {target_file}")
            
            return target_file
            
        except Exception as e:
            self.logger.error(f"파일 복사 실패: {str(e)}")
            raise
            
    def get_next_version_number(self, item_type, item_id):
        """다음 버전 번호 가져오기"""
        try:
            cursor = self.db_connector.cursor()
            
            if item_type == "project":
                table = "project_versions"
                id_column = "project_id"
            elif item_type == "sequence":
                table = "sequence_versions"
                id_column = "sequence_id"
            elif item_type == "shot":
                table = "versions"
                id_column = "shot_id"
            else:
                raise ValueError(f"잘못된 아이템 타입: {item_type}")
                
            # 현재 최대 버전 번호 조회
            query = f"""
                SELECT MAX(VERSION_NUMBER)
                FROM {table}
                WHERE {id_column} = ?
            """
            cursor.execute(query, (item_id,))
            result = cursor.fetchone()
            
            # 첫 버전이면 1, 아니면 최대 버전 + 1
            return (result[0] or 0) + 1
            
        except Exception as e:
            self.logger.error(f"다음 버전 번호 조회 실패: {str(e)}")
            raise
            
    def process_version_file(self, item_type, item_id, source_file):
        """버전 파일 처리"""
        try:
            # 다음 버전 번호 가져오기
            version_number = self.get_next_version_number(item_type, item_id)
            
            # 버전 경로 생성
            version_path = self.get_version_path(item_type, item_id, version_number)
            
            # 파일 복사
            target_file = self.copy_file_to_version(source_file, version_path)
            
            return {
                'version_number': version_number,
                'version_path': version_path,
                'file_path': target_file
            }
            
        except Exception as e:
            self.logger.error(f"버전 파일 처리 실패: {str(e)}")
            raise