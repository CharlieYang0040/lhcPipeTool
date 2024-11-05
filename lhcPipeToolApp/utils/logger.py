import logging
import sys
from pathlib import Path

# 로거 인스턴스를 저장할 딕셔너리
loggers = {}

def setup_logger(name):
    """로거 설정"""
    if name in loggers:
        return loggers[name]
        
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있다면 리턴
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)  # 로그 레벨을 DEBUG로 변경
    
    # 파일 핸들러 설정
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(
        log_dir / "app.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s\n'
        'Location: %(pathname)s:%(lineno)d'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 로거 저장
    loggers[name] = logger
    
    return logger