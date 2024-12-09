"""네트워크 작업 모니터링 핸들러"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import psutil
from ..utils.logger import setup_logger

class OperationType(Enum):
    """작업 유형 정의"""
    FILE_COPY = "file_copy"
    DIRECTORY_CREATE = "directory_create"
    FILE_DELETE = "file_delete"
    NETWORK_CHECK = "network_check"
    DISK_CHECK = "disk_check"

@dataclass
class OperationStatus:
    """작업 상태 정보"""
    operation_id: str
    operation_type: OperationType
    source: str
    destination: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    progress: float = 0.0
    transferred_bytes: int = 0
    total_bytes: int = 0
    retry_count: int = 0
    details: Dict[str, Any] = None

class NetworkMonitor:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.active_operations: Dict[str, OperationStatus] = {}
        self.completed_operations: list[OperationStatus] = []
        
    def start_operation(
        self,
        operation_type: OperationType,
        source: str,
        destination: Optional[str] = None,
        total_bytes: int = 0
    ) -> OperationStatus:
        """
        새로운 작업 모니터링 시작
        
        Args:
            operation_type: 작업 유형
            source: 원본 경로
            destination: 대상 경로
            total_bytes: 전체 바이트 수
        """
        operation_id = f"{operation_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        status = OperationStatus(
            operation_id=operation_id,
            operation_type=operation_type,
            source=source,
            destination=destination,
            start_time=datetime.now(),
            total_bytes=total_bytes,
            details={}
        )
        
        self.active_operations[operation_id] = status
        self.logger.info(f"작업 시작: {operation_type.value} - {source}")
        return status

    def update_progress(
        self,
        operation_id: str,
        transferred_bytes: int,
        current_speed: float = 0.0
    ) -> None:
        """작업 진행률 업데이트"""
        if operation_id not in self.active_operations:
            return
            
        status = self.active_operations[operation_id]
        status.transferred_bytes = transferred_bytes
        
        if status.total_bytes > 0:
            status.progress = (transferred_bytes / status.total_bytes) * 100
            
        status.details.update({
            "current_speed_mbps": current_speed / (1024 * 1024),
            "elapsed_time": (datetime.now() - status.start_time).total_seconds()
        })

    def complete_operation(
        self,
        operation_id: str,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """작업 완료 처리"""
        if operation_id not in self.active_operations:
            return
            
        status = self.active_operations[operation_id]
        status.end_time = datetime.now()
        status.success = success
        status.error_message = error_message
        
        duration = (status.end_time - status.start_time).total_seconds()
        status.details.update({
            "total_duration": duration,
            "average_speed_mbps": (status.transferred_bytes / duration) / (1024 * 1024)
            if duration > 0 else 0
        })
        
        self.completed_operations.append(status)
        del self.active_operations[operation_id]
        
        log_message = (
            f"작업 완료: {status.operation_type.value}\n"
            f"결과: {'성공' if success else '실패'}\n"
            f"소요시간: {duration:.2f}초"
        )
        if error_message:
            log_message += f"\n오류: {error_message}"
            
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)

    def check_system_health(self) -> Dict[str, Any]:
        """시스템 상태 확인"""
        try:
            return {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "active_operations_count": len(self.active_operations),
                "network_io": psutil.net_io_counters()._asdict()
            }
        except Exception as e:
            self.logger.error(f"시스템 상태 확인 실패: {str(e)}")
            return {}

    def get_operation_statistics(self) -> Dict[str, Any]:
        """작업 통계 정보 반환"""
        total_operations = len(self.completed_operations)
        successful_operations = sum(1 for op in self.completed_operations if op.success)
        
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": total_operations - successful_operations,
            "active_operations": len(self.active_operations),
            "average_duration": sum(
                (op.end_time - op.start_time).total_seconds()
                for op in self.completed_operations
            ) / total_operations if total_operations > 0 else 0
        }