"""네트워크 파일 작업 핸들러"""
import shutil
from pathlib import Path
from .network_path_handler import NetworkPathHandler
from .retry_handler import retry_handler
from ..utils.logger import setup_logger
import os

class NetworkFileHandler:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.network_handler = NetworkPathHandler()

    @retry_handler.retry_on_network_error()
    def copy_to_network(self, source: str, destination: str) -> bool:
        """
        파일을 네트워크 경로로 복사
        
        Args:
            source (str): 원본 파일 경로
            destination (str): 대상 네트워크 경로
            
        Returns:
            bool: 복사 성공 여부
        """
        try:
            # 네트워크 접근 확인 및 경로 변환
            success, actual_dest = self.network_handler.ensure_network_access(destination)
            if not success:
                raise PermissionError(f"네트워크 접근 실패: {actual_dest}")
            
            # 대상 디렉토리 생성
            dest_dir = Path(actual_dest).parent
            if not self.ensure_network_directory(str(dest_dir)):
                raise ValueError(f"대상 디렉토리 생성 실패: {dest_dir}")
            
            # 파일 복사
            shutil.copy2(source, actual_dest)
            self.logger.info(f"파일 복사 성공: {source} -> {actual_dest}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"파일 복사 실패: {str(e)}")
            raise

    @retry_handler.retry_on_network_error()
    def ensure_network_directory(self, path: str) -> bool:
        """
        네트워크 경로에 디렉토리가 있는지 확인하고 없으면 생성
        
        Args:
            path (str): 생성할 디렉토리 경로
            
        Returns:
            bool: 디렉토리 생성 성공 여부
        """
        try:
            # 네트워크 접근 확인 및 경로 변환
            success, actual_path = self.network_handler.ensure_network_access(path)
            if not success:
                raise PermissionError(f"네트워크 접근 실패: {actual_path}")

            # 상위 디렉토리들을 순차적으로 생성
            current_path = actual_path
            paths_to_create = []
            
            while current_path and not os.path.exists(current_path):
                paths_to_create.append(current_path)
                current_path = str(Path(current_path).parent)
            
            # 역순으로 디렉토리 생성
            for dir_path in reversed(paths_to_create):
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"디렉토리 생성 완료: {dir_path}")
                except Exception as e:
                    self.logger.error(f"디렉토리 생성 실패: {dir_path} - {str(e)}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"디렉토리 생성 실패: {str(e)}")
            raise

    def validate_network_path(self, path: str) -> bool:
        """
        네트워크 경로 유효성 검사
        
        Args:
            path (str): 검사할 네트워크 경로
            
        Returns:
            bool: 경로가 유효하면 True
        """
        try:
            success, actual_path = self.network_handler.ensure_network_access(path)
            if not success:
                self.logger.warning(f"네트워크 경로 접근 불가: {path}")
                return False
                
            path_obj = Path(actual_path)
            if not path_obj.exists():
                self.logger.warning(f"존재하지 않는 경로: {actual_path}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"경로 유효성 검사 실패: {str(e)}")
            return False