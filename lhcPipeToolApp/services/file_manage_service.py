"""파일 관리 서비스"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from ..handlers.network_path_handler import NetworkPathHandler
from ..handlers.async_network_handler import AsyncNetworkFileHandler
from ..handlers.monitoring_handler import NetworkMonitor, OperationType
from ..utils.logger import setup_logger

class FileManageService:
    def __init__(self, version_services, settings_service):
        self.version_services = version_services
        self.settings_service = settings_service
        self.logger = setup_logger(__name__)
        
        # 핸들러 초기화
        self.network_handler = NetworkPathHandler()
        self.async_handler = AsyncNetworkFileHandler()
        self.monitor = NetworkMonitor()

    async def copy_file_to_version(self, source_file: str, version_path: str) -> Optional[str]:
        """파일을 버전 디렉토리로 복사 (비동기)"""
        try:
            if not os.path.exists(source_file):
                raise FileNotFoundError(f"소스 파일을 찾을 수 없습니다: {source_file}")
            
            # 모니터링 시작
            operation = self.monitor.start_operation(
                OperationType.FILE_COPY,
                source_file,
                version_path,
                os.path.getsize(source_file)
            )

            try:
                # 대상 디렉토리 생성 (ensure_network_access는 ensure_directory 내부에서 처리)
                if not await self.async_handler.ensure_directory(version_path):
                    raise PermissionError(f"디렉토리 생성 실패: {version_path}")
                
                # 파일 이름 추출 및 대상 경로 생성
                file_name = os.path.basename(source_file)
                target_file = os.path.join(version_path, file_name)
                
                # 파일 복사 전 경로 확인
                self.logger.debug(f"소스 파일: {source_file}")
                self.logger.debug(f"대상 파일: {target_file}")
                
                # 파일 비동기 복사
                success = await self.async_handler.copy_with_timeout(
                    source_file,
                    target_file,
                    progress_callback=lambda progress: self.monitor.update_progress(
                        operation.operation_id,
                        int(progress * os.path.getsize(source_file) / 100)
                    )
                )

                if success:
                    self.monitor.complete_operation(operation.operation_id, True)
                    self.logger.info(f"파일 복사 완료: {target_file}")
                    return target_file
                else:
                    raise Exception("파일 복사 실패")

            except Exception as e:
                self.monitor.complete_operation(
                    operation.operation_id,
                    False,
                    str(e)
                )
                raise

        except Exception as e:
            self.logger.error(f"파일 복사 실패: {str(e)}")
            raise

    def get_version_path(self, item_type: str, item_id: int, version_number: int) -> str:
        """
        버전 경로 생성
        
        Args:
            item_type: 'project', 'sequence', 'shot' 중 하나
            item_id: 아이템 ID
            version_number: 버전 번호
            
        Returns:
            str: 생성된 버전 경로
            
        Examples:
            project: Y:/Project_TEST/Render/Rogue/v001
            sequence: Y:/Project_TEST/Render/Rogue/Wide/v001
            shot: Y:/Project_TEST/Render/Rogue/Wide/shot002/v001
        """
        try:
            # 기본 출력 경로 가져오기 (예: \\DESKTOP-LHG738J\lighting_share3\Project_TEST\Render)
            base_path = self.settings_service.get_setting('render_output')
            if not base_path:
                raise ValueError("렌더 출력 경로가 설정되지 않았습니다.")
            
            # 네트워크 경로 처리
            success, mapped_path = self.network_handler.ensure_network_access(base_path)
            if not success:
                raise PermissionError(f"네트워크 경로 접근 실패: {mapped_path}")
            
            # 매핑된 드라이브 문자와 기본 경로 분리
            drive_letter = mapped_path.split(':')[0] + ':'
            base_components = base_path.split('\\')[4:]  # Project_TEST/Render 부분 추출
            version_folder = f"v{version_number:03d}"
            
            # 아이템 타입별 경로 구성
            if item_type == "project":
                project = self.version_services["project"].get_project_details(item_id)
                if not project:
                    raise ValueError(f"프로젝트를 찾을 수 없습니다: {item_id}")
                
                path_components = [
                    drive_letter,
                    # *base_components,  # Project_TEST/Render
                    project['name'],   # Rogue
                    version_folder     # v001
                ]
                
            elif item_type == "sequence":
                sequence = self.version_services["sequence"].get_sequence_details(item_id)
                if not sequence:
                    raise ValueError(f"시퀀스를 찾을 수 없습니다: {item_id}")
                
                path_components = [
                    drive_letter,
                    # *base_components,     # Project_TEST/Render
                    sequence['project_name'], # Rogue
                    sequence['name'],     # Wide
                    version_folder        # v001
                ]
                
            elif item_type == "shot":
                shot = self.version_services["shot"].get_shot_details(item_id)
                if not shot:
                    raise ValueError(f"샷을 찾을 수 없습니다: {item_id}")
                
                path_components = [
                    drive_letter,
                    # *base_components,     # Project_TEST/Render
                    shot['project_name'], # Rogue
                    shot['sequence_name'], # Wide
                    shot['name'], # shot002
                    version_folder        # v001
                ]
                
            else:
                raise ValueError(f"잘못된 아이템 타입: {item_type}")
            
            # 경로 구성 및 반환
            version_path = os.path.join(*path_components).replace('\\', '/')
            self.logger.debug(f"생성된 버전 경로: {version_path}")
            return version_path
            
        except Exception as e:
            self.logger.error(f"버전 경로 생성 실패: {str(e)}")
            raise

    def _get_item_details(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """아이템 상세 정보 조회"""
        if item_type not in self.version_services:
            raise ValueError(f"지원하지 않는 아이템 타입: {item_type}")
            
        if item_type == "project":
            return self.version_services[item_type].get_project_details(item_id)
        elif item_type == "sequence":
            return self.version_services[item_type].get_sequence_details(item_id)
        elif item_type == "shot":
            return self.version_services[item_type].get_shot_details(item_id)
            
    def _build_version_path(self, item_type: str, details: Dict[str, Any], version_number: int) -> str:
        """버전 경로 구성"""
        if item_type == "project":
            return f"{details['name']}/v{version_number:03d}"
        elif item_type == "sequence":
            return f"{details['project_name']}/{details['name']}/v{version_number:03d}"
        elif item_type == "shot":
            return f"{details['project_name']}/{details['sequence_name']}/{details['name']}/v{version_number:03d}"
        else:
            raise ValueError(f"잘못된 아이템 타입: {item_type}")
            
    def get_next_version_number(self, item_type: str, item_id: int) -> int:
        """다음 버전 번호 가져오기"""
        try:           
            table_info = {
                "project": ("project_versions", "project_id"),
                "sequence": ("sequence_versions", "sequence_id"),
                "shot": ("versions", "shot_id")
            }
            
            if item_type not in table_info:
                raise ValueError(f"잘못된 아이템 타입: {item_type}")
                
            table, id_column = table_info[item_type]
            
            # 현재 최대 버전 번호 조회
            query = f"SELECT MAX(VERSION_NUMBER) FROM {table} WHERE {id_column} = ?"
            result = self.version_services[item_type].version_model._fetch_one(query, (item_id,))
            
            self.logger.debug(f"최대 버전 번호: {result}")
            return (result['max'] or 0) + 1
            
        except Exception as e:
            self.logger.error(f"다음 버전 번호 조회 실패: {str(e)}")
            raise

    async def process_version_file(
        self, 
        source_file: str, 
        item_type: str, 
        item_id: int,
        version_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """버전 파일 처리"""
        try:
            if version_number is None:
                version_number = self.get_next_version_number(item_type, item_id)
                
            # 버전 경로 생성
            version_path = self.get_version_path(item_type, item_id, version_number)
            
            # 파일 복사
            target_file = await self.copy_file_to_version(source_file, version_path)
            if not target_file:
                raise Exception("파일 복사 실패")
                
            return {
                'source_file': source_file,
                'target_file': target_file,
                'version_number': version_number
            }
            
        except Exception as e:
            self.logger.error(f"버전 파일 처리 실패: {str(e)}")
            raise

    async def process_multiple_files(
        self, 
        files: List[str], 
        item_type: str, 
        item_id: int,
        version_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """여러 파일 동시 처리"""
        try:
            if version_number is None:
                version_number = self.get_next_version_number(item_type, item_id)
                
            version_path = self.get_version_path(item_type, item_id, version_number)
            
            # (source, destination) 튜플 리스트 생성
            files_to_copy = [
                (source_file, os.path.join(version_path, os.path.basename(source_file)))
                for source_file in files
            ]
            
            # 비동기 파일 서비스를 통한 동시 처리
            results = await self.async_handler.process_files(files_to_copy)
            
            # 결과 매핑
            processed_files = []
            for source_file, success in zip(files, results):
                if success:
                    target_file = os.path.join(
                        version_path, 
                        os.path.basename(source_file)
                    )
                    processed_files.append({
                        'source_file': source_file,
                        'target_file': target_file,
                        'version_number': version_number
                    })
                else:
                    self.logger.error(f"파일 처리 실패: {source_file}")
                    
            if not processed_files:
                raise Exception("모든 파일 처리 실패")
                
            return processed_files
            
        except Exception as e:
            self.logger.error(f"다중 파일 처리 실패: {str(e)}")
            raise

    async def create_version(
        self, 
        item_type: str, 
        item_id: int, 
        source_files: List[str],
        version_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """버전 생성"""
        try:
            # 파일 처리
            if len(source_files) == 1:
                file_info = await self.process_version_file(
                    source_files[0], 
                    item_type, 
                    item_id,
                    version_number
                )
                processed_files = [file_info]
            else:
                processed_files = await self.process_multiple_files(
                    source_files, 
                    item_type, 
                    item_id,
                    version_number
                )
                
            version_number = processed_files[0]['version_number']
            
            # 버전 정보 반환
            return {
                'version_number': version_number,
                'files': processed_files
            }
            
        except Exception as e:
            self.logger.error(f"버전 생성 실패: {str(e)}")
            raise