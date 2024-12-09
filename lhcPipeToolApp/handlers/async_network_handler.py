"""비동기 네트워크 파일 핸들러"""
import asyncio
import aiofiles
import os
import time
from pathlib import Path
from typing import Optional
from .network_path_handler import NetworkPathHandler
from .retry_handler import retry_handler
from ..utils.logger import setup_logger
from ..handlers.monitoring_handler import NetworkMonitor, OperationType

class AsyncNetworkFileHandler:
    def __init__(self, chunk_size: int = 64 * 1024, timeout: float = 30.0):
        self.logger = setup_logger(__name__)
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.network_path_handler = NetworkPathHandler()
        self.monitor = NetworkMonitor()

    async def copy_file(self, source: str, destination: str, progress_callback: Optional[callable] = None) -> bool:
        try:
            source_size = Path(source).stat().st_size
            copied_size = 0

            # 네트워크 접근 확인
            success, actual_dest = self.network_path_handler.ensure_network_access(destination)
            if not success:
                raise PermissionError(f"네트워크 접근 실패: {actual_dest}")

            operation = self.monitor.start_operation(
                OperationType.FILE_COPY,
                source,
                actual_dest,
                source_size
            )
            
            try:
                start_time = time.time()
                last_update_time = start_time

                async with aiofiles.open(source, 'rb') as src:
                    async with aiofiles.open(actual_dest, 'wb') as dst:
                        while chunk := await src.read(self.chunk_size):
                            await dst.write(chunk)
                            copied_size += len(chunk)
                            
                            current_time = time.time()
                            if current_time - last_update_time >= 1.0:
                                speed = copied_size / (current_time - start_time)
                                self.monitor.update_progress(
                                    operation.operation_id,
                                    copied_size,
                                    speed
                                )
                                last_update_time = current_time

                self.monitor.complete_operation(operation.operation_id, True)
                return True

            except Exception as e:
                self.monitor.complete_operation(operation.operation_id, False, str(e))
                return False

        except Exception as e:
            self.logger.error(f"비동기 파일 복사 실패: {str(e)}")
            return False

    async def ensure_directory(self, path: str) -> bool:
        """
        매핑된 드라이브 경로의 모든 상위 디렉토리를 순차적으로 생성
        """
        try:
            # 네트워크 접근 확인 및 매핑된 드라이브 경로 얻기
            success, mapped_path = self.network_path_handler.ensure_network_access(path)
            if not success:
                raise PermissionError(f"네트워크 접근 실패: {mapped_path}")
            
            self.logger.debug(f"디렉토리 생성 시작: {mapped_path}")
            
            # 경로를 컴포넌트로 분리 (드라이브 경로 사용)
            path_parts = Path(mapped_path).parts
            
            # 드라이브 문자로 시작하는 경우 (Y:\)
            current_path = path_parts[0]  # 드라이브 문자 (예: Y:)
            
            # 순차적으로 디렉토리 생성
            for part in path_parts[1:]:
                current_path = os.path.join(current_path, part)
                if not os.path.exists(current_path):
                    try:
                        os.makedirs(current_path, exist_ok=True)
                        self.logger.info(f"디렉토리 생성됨: {current_path}")
                    except Exception as e:
                        self.logger.error(f"디렉토리 생성 실패: {current_path} - {str(e)}")
                        return False
                else:
                    self.logger.debug(f"이미 존재하는 디렉토리: {current_path}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"디렉토리 생성 실패: {str(e)}")
            return False

    @retry_handler.retry_on_network_error()
    async def copy_with_timeout(self, source: str, destination: str, progress_callback: Optional[callable] = None) -> bool:
        try:
            # 네트워크 접근 확인 및 경로 변환
            success, actual_dest = self.network_path_handler.ensure_network_access(destination)
            if not success:
                raise PermissionError(f"네트워크 접근 실패: {actual_dest}")

            # 대상 디렉토리 생성
            if not await self.ensure_directory(str(Path(actual_dest).parent)):
                raise ValueError(f"대상 디렉토리 생성 실패: {actual_dest}")

            # 타임아웃과 함께 복사 실행
            async with asyncio.timeout(self.timeout):
                return await self.copy_file(source, actual_dest, progress_callback)

        except asyncio.TimeoutError:
            self.logger.error(f"파일 복사 시간 초과 (제한 시간: {self.timeout}초)")
            return False
        except Exception as e:
            self.logger.error(f"파일 복사 실패: {str(e)}")
            return False