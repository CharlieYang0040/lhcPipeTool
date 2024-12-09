"""네트워크 경로 처리 핸들러"""
import os
import string
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, Dict
from ..utils.logger import setup_logger

class NetworkPathHandler:
    def __init__(self):
        self.logger = setup_logger(__name__)

    def find_available_drive(self) -> Optional[str]:
        """사용 가능한 드라이브 문자 찾기"""
        try:
            used_drives = set()
            for letter in string.ascii_uppercase:
                if os.path.exists(f"{letter}:"):
                    used_drives.add(f"{letter}:")

            for letter in reversed(string.ascii_uppercase):
                drive = f"{letter}:"
                if drive not in used_drives:
                    return drive
            return None
            
        except Exception as e:
            self.logger.error(f"사용 가능한 드라이브 문자 찾기 실패: {str(e)}")
            return None

    def get_drive_mappings(self) -> Dict[str, str]:
        """현재 시스템의 네트워크 드라이브 매핑 정보 가져오기"""
        try:
            mappings = {}
            result = subprocess.run(['net', 'use'], capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if ':' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        drive = parts[1]
                        unc = parts[2]
                        mappings[drive] = unc
            return mappings
            
        except Exception as e:
            self.logger.error(f"드라이브 매핑 정보 가져오기 실패: {str(e)}")
            return {}

    def map_network_drive(self, unc_path: str) -> Tuple[bool, str]:
        """
        네트워크 드라이브 매핑
        
        Args:
            unc_path: UNC 경로 (예: //server/share/path)
            
        Returns:
            Tuple[bool, str]: (성공 여부, 매핑된 드라이브 경로 또는 오류 메시지)
        """
        try:
            # UNC 경로에서 서버와 공유 폴더만 추출
            path_parts = unc_path.strip('/').split('/')
            if len(path_parts) < 2:
                raise ValueError(f"잘못된 UNC 경로 형식: {unc_path}")
            
            server = path_parts[0]
            share = path_parts[1]
            # UNC 경로 형식으로 변환 (백슬래시 사용)
            share_path = f"\\\\{server}\\{share}"
            
            # 현재 매핑된 드라이브 확인
            current_mappings = self.get_drive_mappings()
            
            # 이미 매핑된 드라이브가 있는지 확인
            for drive, mapped_path in current_mappings.items():
                if mapped_path.lower() == share_path.lower():
                    self.logger.debug(f"이미 매핑된 드라이브 사용: {drive} -> {mapped_path}")
                    # 매핑 성공 시, 전체 경로 반환
                    remaining_path = '/'.join(path_parts[2:]) if len(path_parts) > 2 else ''
                    full_path = f"{drive}/{remaining_path}" if remaining_path else drive
                    return True, full_path
            
            # 매핑된 드라이브가 없으면 새로 매핑
            drive_letter = self.find_available_drive()
            if not drive_letter:
                raise RuntimeError("사용 가능한 드라이브 문자가 없습니다")

            # 공유 폴더까지만 매핑 (올바른 net use 구문)
            command = ['net', 'use', f"{drive_letter}:", share_path]
            
            self.logger.debug(f"새로운 드라이브 매핑 시도: {command}")
            subprocess.run(command, check=True, capture_output=True, text=True)
            
            # 매핑 성공 시, 전체 경로 반환
            remaining_path = '/'.join(path_parts[2:]) if len(path_parts) > 2 else ''
            full_path = f"{drive_letter}:/{remaining_path}" if remaining_path else f"{drive_letter}:"
            
            return True, full_path
            
        except subprocess.CalledProcessError as e:
            error_msg = f"드라이브 매핑 실패: {e.stderr.strip()}"
            self.logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"드라이브 매핑 실패: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def ensure_network_access(self, path: str) -> Tuple[bool, str]:
        """네트워크 경로 접근 보장"""
        try:
            # UNC 경로로 변환
            if path.startswith('\\\\'):
                unc_path = path
            else:
                unc_path = self.normalize_network_path(path)

            # 이미 접근 가능한 경우
            if os.path.exists(unc_path):
                return True, unc_path

            # 서버/공유 경로 추출
            server_share = '\\'.join(unc_path.split('\\')[:4])

            # 드라이브 매핑 시도
            success, result = self.map_network_drive(server_share)
            if success:
                drive_path = path.replace(server_share, f"{result}")
                if os.path.exists(drive_path):
                    return True, drive_path
                    
            return False, f"네트워크 경로 접근 실패: {result}"

        except Exception as e:
            return False, f"네트워크 접근 확인 실패: {str(e)}"

    def normalize_network_path(self, path: str) -> str:
        """네트워크 경로 정규화"""
        try:
            if not path:
                raise ValueError("경로가 비어있습니다.")

            # UNC 경로 형식으로 변환
            path = path.replace(':', '')  # 드라이브 문자 제거
            normalized = path.replace('\\', '/')
            
            # UNC 경로 형식 확인 및 수정
            if not normalized.startswith('//'):
                if normalized.startswith('/'):
                    normalized = f"/{normalized}"
                else:
                    normalized = f"//{normalized}"

            # 중복 슬래시 제거 (UNC 시작 부분 제외)
            while '//' in normalized[2:]:
                normalized = normalized[:2] + normalized[2:].replace('//', '/')

            self.logger.debug(f"경로 정규화 완료: {path} -> {normalized}")
            return normalized

        except Exception as e:
            self.logger.error(f"경로 정규화 실패: {str(e)}")
            raise

    def validate_network_path(self, path: str) -> bool:
        """
        네트워크 경로의 유효성을 검사합니다.
        
        Args:
            path (str): 검사할 네트워크 경로
            
        Returns:
            bool: 경로가 유효하면 True, 그렇지 않으면 False
        """
        try:
            normalized_path = self.normalize_network_path(path)
            path_obj = Path(normalized_path)
            
            # 기본적인 경로 형식 검사
            if not str(path_obj).startswith('//'):
                self.logger.warning(f"잘못된 네트워크 경로 형식: {path}")
                return False

            # 서버와 공유 폴더 이름이 있는지 확인
            parts = str(path_obj).split('/')
            if len(parts) < 4:  # //, server, share, path 최소 4개 부분 필요
                self.logger.warning(f"불완전한 네트워크 경로: {path}")
                return False

            # 경로 존재 여부 확인
            exists = path_obj.exists()
            if not exists:
                self.logger.warning(f"존재하지 않는 네트워크 경로: {path}")
            
            return exists

        except Exception as e:
            self.logger.error(f"경로 유효성 검사 실패: {str(e)}")
            return False

    def create_network_url(self, server: str, share: str, path: str = '') -> str:
        """
        SMB URL 형식의 네트워크 경로를 생성합니다.
        
        Args:
            server (str): 서버 이름
            share (str): 공유 폴더 이름
            path (str, optional): 추가 경로
            
        Returns:
            str: SMB URL 형식의 네트워크 경로
            
        Example:
            >>> handler = NetworkPathHandler()
            >>> handler.create_network_url('server', 'share', 'path/to/file')
            'smb://server/share/path/to/file'
        """
        try:
            # 각 컴포넌트의 유효성 검사
            if not server or not share:
                raise ValueError("서버와 공유 폴더 이름은 필수입니다.")

            # 각 컴포넌트의 앞뒤 슬래시 제거
            server = server.strip('/')
            share = share.strip('/')
            path = path.strip('/')

            # URL 인코딩이 필요한 특수문자 처리
            server = urllib.parse.quote(server)
            share = urllib.parse.quote(share)
            path = urllib.parse.quote(path)

            # URL 조합
            url = f"smb://{server}/{share}"
            if path:
                url = f"{url}/{path}"

            self.logger.debug(f"네트워크 URL 생성: {url}")
            return url

        except Exception as e:
            self.logger.error(f"네트워크 URL 생성 실패: {str(e)}")
            raise

    def create_unc_path(self, server: str, share: str, path: str = '') -> str:
        """
        UNC 경로 생성
        
        Args:
            server: 서버 이름 (예: "DESKTOP-LHG738J")
            share: 공유 폴더 이름 (예: "Project_TEST")
            path: 추가 경로
            
        Returns:
            str: UNC 형식의 경로 (예: "\\DESKTOP-LHG738J\Project_TEST\path")
        """
        try:
            # 각 컴포넌트 정리
            server = server.strip('\\/ ')
            share = share.strip('\\/ ')
            path = path.strip('\\/ ')

            # UNC 경로 조합
            unc_path = f"//{server}/{share}"
            if path:
                unc_path = f"{unc_path}/{path}"

            return unc_path

        except Exception as e:
            self.logger.error(f"UNC 경로 생성 실패: {str(e)}")
            raise