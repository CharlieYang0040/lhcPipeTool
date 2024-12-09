"""비동기 파일 서비스"""
import asyncio
from pathlib import Path
from typing import List, Tuple, Optional
from ..handlers.async_network_handler import AsyncNetworkFileHandler
from ..handlers.network_path_handler import NetworkPathHandler
from ..utils.logger import setup_logger

class AsyncFileService:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.async_handler = AsyncNetworkFileHandler()
        self.network_handler = NetworkPathHandler()

    async def process_files(self, files_to_copy: List[Tuple[str, str]]) -> List[bool]:
        """
        여러 파일을 동시에 처리
        
        Args:
            files_to_copy (list): (source, destination) 튜플의 리스트
            
        Returns:
            list[bool]: 각 파일의 복사 성공 여부 리스트
        """
        async def copy_with_progress(source: str, destination: str) -> bool:
            try:
                # 네트워크 접근 확인 및 경로 변환
                success, actual_dest = self.network_handler.ensure_network_access(destination)
                if not success:
                    self.logger.error(f"네트워크 접근 실패: {actual_dest}")
                    return False

                async def progress_callback(progress: float):
                    self.logger.info(f"복사 진행률 ({Path(source).name}): {progress:.1f}%")
                
                return await self.async_handler.copy_with_timeout(
                    source, actual_dest, progress_callback
                )
            except Exception as e:
                self.logger.error(f"파일 처리 실패 ({source}): {str(e)}")
                return False

        # 모든 파일 복사 작업을 동시에 실행
        tasks = [
            copy_with_progress(source, dest)
            for source, dest in files_to_copy
        ]
        
        return await asyncio.gather(*tasks)

    async def copy_single_file(self, source: str, destination: str, 
                             progress_callback: Optional[callable] = None) -> bool:
        """
        단일 파일 비동기 복사
        
        Args:
            source (str): 원본 파일 경로
            destination (str): 대상 파일 경로
            progress_callback (callable, optional): 진행률 콜백 함수
            
        Returns:
            bool: 복사 성공 여부
        """
        try:
            # 네트워크 접근 확인 및 경로 변환
            success, actual_dest = self.network_handler.ensure_network_access(destination)
            if not success:
                raise PermissionError(f"네트워크 접근 실패: {actual_dest}")

            return await self.async_handler.copy_with_timeout(
                source, actual_dest, progress_callback
            )
            
        except Exception as e:
            self.logger.error(f"파일 복사 실패: {str(e)}")
            return False

    async def ensure_network_directory(self, path: str) -> bool:
        """
        네트워크 디렉토리 존재 확인 및 생성
        
        Args:
            path (str): 생성할 디렉토리 경로
            
        Returns:
            bool: 생성 성공 여부
        """
        try:
            # 네트워크 접근 확인 및 경로 변환
            success, actual_path = self.network_handler.ensure_network_access(path)
            if not success:
                raise PermissionError(f"네트워크 접근 실패: {actual_path}")

            return await self.async_handler.ensure_directory(actual_path)
            
        except Exception as e:
            self.logger.error(f"디렉토리 생성 실패: {str(e)}")
            return False