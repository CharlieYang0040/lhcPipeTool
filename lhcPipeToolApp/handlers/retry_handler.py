"""재시도 메커니즘 핸들러"""
import time
from functools import wraps
from typing import Callable, Any, Type, Union, Tuple
from ..utils.logger import setup_logger

class RetryHandler:
    def __init__(self):
        self.logger = setup_logger(__name__)

    def retry_on_network_error(
        self,
        retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (
            FileNotFoundError,
            PermissionError,
            TimeoutError,
            ConnectionError
        )
    ) -> Callable:
        """
        네트워크 작업 실패 시 재시도하는 데코레이터
        
        Args:
            retries (int): 최대 재시도 횟수
            delay (float): 초기 대기 시간(초)
            backoff (float): 대기 시간 증가 배율
            exceptions (Exception | tuple): 재시도할 예외 유형
            
        Returns:
            Callable: 데코레이터 함수
            
        Example:
            @retry_handler.retry_on_network_error(retries=3, delay=1.0)
            def copy_file(self, source: str, destination: str):
                # 파일 복사 로직
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                current_delay = delay
                
                for attempt in range(retries):
                    try:
                        return func(*args, **kwargs)
                    
                    except exceptions as e:
                        last_exception = e
                        retry_count = attempt + 1
                        
                        if retry_count == retries:
                            self.logger.error(
                                f"최대 재시도 횟수 도달 ({retries}회) - "
                                f"함수: {func.__name__}, "
                                f"마지막 오류: {str(e)}"
                            )
                            raise last_exception
                        
                        self.logger.warning(
                            f"작업 실패 (시도 {retry_count}/{retries}) - "
                            f"함수: {func.__name__}, "
                            f"오류: {str(e)}, "
                            f"다음 시도까지 대기 시간: {current_delay}초"
                        )
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                
                if last_exception:
                    raise last_exception
                    
            return wrapper
        return decorator


# 사용 편의를 위한 전역 인스턴스
retry_handler = RetryHandler()