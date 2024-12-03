"""프로젝트 관리 서비스"""
from ..models.project import Project
from ..models.sequence import Sequence
from ..models.shot import Shot
from ..models.version_models import ShotVersion, SequenceVersion, ProjectVersion
from ..utils.logger import setup_logger
from ..utils.db_utils import convert_date_format
from ..database.table_manager import TableManager
from .worker_service import WorkerService
from ..utils.event_system import EventSystem

class ProjectService:
    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.project_model = Project(db_connector)
        self.sequence_model = Sequence(db_connector)
        self.shot_model = Shot(db_connector)
        self.logger = setup_logger(__name__)
        self.table_manager = TableManager(db_connector)
        self.worker_service = WorkerService(db_connector)
        self.version_models = {
            "shot_id": ShotVersion(db_connector),
            "sequence_id": SequenceVersion(db_connector),
            "project_id": ProjectVersion(db_connector)
        }
        
    def get_project_structure(self, project_id):
        """프로젝트의 전체 구조 조회"""
        try:
            self.logger.info(f"프로젝트 구조 조회 시작 - Project ID: {project_id}")
            
            project = self.project_model.get_by_id(project_id)
            if not project:
                self.logger.warning(f"프로젝트를 찾을 수 없음 - ID: {project_id}")
                return None

            sequences = self.sequence_model.get_by_project(project_id)
            structure = {
                "project": {
                    "id": project[0],
                    "name": project[1],
                    "path": project[2],
                    "description": project[3],
                    "created_at": project[4]
                },
                "sequences": {}
            }

            for seq in sequences:
                shots = self.shot_model.get_by_sequence(seq[0])
                shot_list = []
                
                for shot in shots:
                    latest_version = self.version_models["shot_id"].get_latest_version(shot[0])
                    shot_info = {
                        "id": shot[0],
                        "name": shot[2],
                        "status": shot[3],
                        "description": shot[4],
                        "created_at": shot[5],
                        "latest_version": latest_version
                    }
                    shot_list.append(shot_info)
                
                structure["sequences"][seq[0]] = {
                    "info": {
                        "id": seq[0],
                        "name": seq[2],
                        "description": seq[3],
                        "created_at": seq[4]
                    },
                    "shots": shot_list
                }

            self.logger.info("프로젝트 구조 조회 완료")
            return structure
            
        except Exception as e:
            self.logger.error(f"프로젝트 구조 조회 중 오류 발생: {str(e)}", exc_info=True)
            return None

    def get_full_project_structure(self):
        """전체 프로젝트 구조와 최신 버전 정보를 가져옵니다."""
        data = self.project_model.get_full_project_structure()
        structure = {}

        for row in data:
            project_id = row['project_id']
            sequence_id = row.get('sequence_id')
            shot_id = row.get('shot_id')

            # 프로젝트 추가
            if project_id not in structure:
                structure[project_id] = {
                    'id': project_id,
                    'name': row['project_name'],
                    'preview_path': row.get('project_preview'),
                    'sequences': {}
                }

            # 시퀀스가 있을 경우 추가
            if sequence_id:
                sequences = structure[project_id]['sequences']
                if sequence_id not in sequences:
                    sequences[sequence_id] = {
                        'id': sequence_id,
                        'name': row['sequence_name'],
                        'preview_path': row.get('sequence_preview'),
                        'shots': {}
                    }

                # 샷이 있을 경우 추가
                if shot_id:
                    shots = sequences[sequence_id]['shots']
                    if shot_id not in shots:
                        shots[shot_id] = {
                            'id': shot_id,
                            'name': row['shot_name'],
                            'preview_path': row.get('shot_preview')
                        }

        return structure

    def create_project(self, name, path=None, description=None):
        """프로젝트 생성"""
        try:
            self.logger.info(f"""프로젝트 생성 시도:
                            이름: {name}
                            경로: {path}
                            설명: {description}
                        """)
            
            # 모델의 create 메서드 호출
            project_id = self.project_model.create(name, path, description)
            if project_id:
                self.db_connector.commit()
                EventSystem.notify('project_updated')  # 이벤트 발생
                
                self.logger.info(f"프로젝트 생성 성공 - ID: {project_id}")
                return project_id
            else:
                raise Exception("프로젝트 생성 실패")
            
        except Exception as e:
            self.db_connector.rollback()
            self.logger.error(f"프로젝트 생성 실패: {str(e)}")
            raise

    def create_sequence(self, name, project_id, level_path=None, level_sequence_path=None, description=None):
        """시퀀스 생성"""
        try:
            self.logger.info(f"""시퀀스 생성 시도:
                            이름: {name}
                            프로젝트 ID: {project_id}
                            레벨 경로: {level_path}
                            레벨 시퀀스 경로: {level_sequence_path}
                            설명: {description}
                        """)

            # 모델의 create 메서드 호출
            sequence_id = self.sequence_model.create(name, project_id, level_path, level_sequence_path, description)
            if sequence_id:
                self.db_connector.commit()
                EventSystem.notify('sequence_updated')  # 이벤트 발생
                
                self.logger.info(f"시퀀스 생성 성공 - ID: {sequence_id}")
                return sequence_id
            else:
                self.db_connector.rollback()
                raise Exception("시퀀스 생성 실패")

        except Exception as e:
            self.logger.error(f"시퀀스 생성 실패: {str(e)}")
            raise

    def create_shot(self, name, sequence_id, status="pending", description=None):
        """샷 생성"""
        try:
            self.logger.info(f"""샷 생성 시도:
                            이름: {name}
                            시퀀스 ID: {sequence_id}
                            상태: {status}
                            설명: {description}
                        """)

            # 모델의 create 메서드 호출
            shot_id = self.shot_model.create(name, sequence_id, description, status)
            if shot_id:
                self.db_connector.commit()
                EventSystem.notify('shot_updated')  # 이벤트 발생
                
                self.logger.info(f"샷 생성 성공 - ID: {shot_id}")
                return shot_id
            else:
                raise Exception("샷 생성 실패")

        except Exception as e:
            self.db_connector.rollback()
            self.logger.error(f"샷 생성 실패: {str(e)}")
            raise

    def delete_project(self, project_id):
        """프로젝트 삭제 (연관된 시퀀스와 샷도 함께 삭제)"""
        # 연관된 시퀀스들 조회
        sequences = self.sequence_model.get_by_project(project_id)
        
        # 각 시퀀스의 샷들 삭제
        for seq in sequences:
            self.delete_sequence(seq[0])
        
        # 프로젝트 삭제
        return self.project_model.delete(project_id)

    def delete_sequence(self, sequence_id):
        """시퀀스 삭제 (연관된 샷도 함께 삭제)"""
        # 연관된 샷들 삭제
        shots = self.shot_model.get_by_sequence(sequence_id)
        for shot in shots:
            self.shot_model.delete(shot[0])
        
        # 시퀀스 삭제
        return self.sequence_model.delete(sequence_id)

    def delete_shot(self, shot_id):
        """샷 삭제"""
        return self.shot_model.delete(shot_id)

    def get_sequence_by_id(self, sequence_id):
        """시퀀스 정보 조회"""
        return self.sequence_model.get_by_id(sequence_id)

    def get_shot_by_id(self, shot_id):
        """샷 정보 조회"""
        return self.shot_model.get_by_id(shot_id)

    def get_all_projects(self):
        """모든 프로젝트 조회"""
        return self.project_model.get_all()

    def get_project_by_name(self, name):
        """프로젝트 이름으로 조회"""
        return self.project_model.get_by_name(name)

    def get_sequence_by_name(self, project_id, name):
        """시퀀스 이름으로 조회"""
        return self.sequence_model.get_by_name(project_id, name)

    def get_shot_by_name(self, sequence_id, name):
        """샷 이름으로 조회"""
        return self.shot_model.get_by_name(sequence_id, name)
        
    def get_version_by_name(self, shot_id, version_number):
        """버전 이름으로 조회"""
        return self.version_models["shot_id"].get_by_name(shot_id, version_number)

    # TODO 언리얼 시퀀서와 json으로 폴더구조 공유 및 생성 기능 추가
    def sync_project_structure(self, root_path):
        """프로젝트 구조 동기화"""
        try:
            self.logger.info(f"프로젝트 구조 동기화 시작 - 루트 경로: {root_path}")
            project_count = 0
            
            for project_dir in root_path.iterdir():
                if not project_dir.is_dir():
                    self.logger.debug(f"디렉토리가 아닌 항목 건너뛰기: {project_dir}")
                    continue
                    
                try:
                    # 프로젝트 업데이트
                    project = self.get_project_by_name(project_dir.name)
                    if not project:
                        self.logger.info(f"동기화 할 프로젝트가 없습니다.")
                    else:
                        project_id = project[0]
                        self.logger.debug(f"기존 프로젝트 발견: {project_dir.name}")
                        # 경로 업데이트
                        self.update_project_path(project_id, str(project_dir))
                    
                    # 시퀀스 동기화
                    self._sync_sequences(project_id, project_dir)
                    
                except Exception as e:
                    self.logger.error(f"프로젝트 처리 중 오류 발생: {project_dir.name} - {str(e)}")
                    continue
                    
            self.logger.info(f"프로젝트 구조 동기화 완료 - 생성된 프로젝트 수: {project_count}")
                
        except Exception as e:
            self.logger.error(f"프로젝트 구조 동기화 중 오류 발생: {str(e)}", exc_info=True)
            raise

    def _sync_sequences(self, project_id, project_dir):
        """시퀀스 동기화"""
        try:
            self.logger.info(f"시퀀스 동기화 시작 - Project ID: {project_id}, 경로: {project_dir}")
            sequence_count = 0
            
            for seq_dir in project_dir.iterdir():
                if not seq_dir.is_dir():
                    self.logger.debug(f"디렉토리가 아닌 항목 건너뛰기: {seq_dir}")
                    continue
                    
                try:
                    sequence = self.get_sequence_by_name(project_id, seq_dir.name)
                    if not sequence:
                        self.logger.info(f"동기화 할 시퀀스가 없습니다.")
                    else:
                        sequence_id = sequence[0]
                        self.logger.debug(f"기존 시퀀스 발견: {seq_dir.name}")
                    
                    # 샷 동기화
                    self._sync_shots(sequence_id, seq_dir)
                    
                except Exception as e:
                    self.logger.error(f"시퀀스 처리 중 오류 발생: {seq_dir.name} - {str(e)}")
                    continue
                    
            self.logger.info(f"시퀀스 동기화 완료 - 생성된 시퀀스 수: {sequence_count}")
                
        except Exception as e:
            self.logger.error(f"시퀀스 동기화 중 오류 발생: {str(e)}", exc_info=True)

    def _sync_shots(self, sequence_id, seq_dir):
        """샷 동기화"""
        try:
            self.logger.info(f"샷 동기화 시작 - Sequence ID: {sequence_id}, 경로: {seq_dir}")
            shot_count = 0
            
            for shot_dir in seq_dir.iterdir():
                if not shot_dir.is_dir():
                    self.logger.debug(f"디렉토리가 아닌 항목 건너뛰기: {shot_dir}")
                    continue
                    
                try:
                    shot = self.get_shot_by_name(sequence_id, shot_dir.name)
                    if not shot:
                        self.logger.info(f"동���화 할 샷이 없습니다.")
                    else:
                        shot_id = shot[0]
                        self.logger.debug(f"기존 샷 발견: {shot_dir.name}")
                    
                    # 버전 동기화
                    self._sync_versions(shot_id, shot_dir)
                    
                except Exception as e:
                    self.logger.error(f"샷 처리 중 오류 발생: {shot_dir.name} - {str(e)}")
                    continue
                    
            self.logger.info(f"샷 동기화 완료 - 생성된 샷 수: {shot_count}")
                
        except Exception as e:
            self.logger.error(f"샷 동기화 중 오류 발생: {str(e)}", exc_info=True)

    def _sync_versions(self, shot_id, shot_dir):
        """샷 내 버전 동기화"""
        try:
            self.logger.info(f"버전 동기화 시작 - Shot ID: {shot_id}, 경로: {shot_dir}")
            version_count = 0
            
            for version_dir in shot_dir.glob('v*'):
                if not version_dir.is_dir():
                    self.logger.debug(f"디렉토리가 아닌 항목 건너뛰기: {version_dir}")
                    continue
                
                try:
                    self.logger.debug(f"버전 디렉토리 처리 중: {version_dir.name}")
                    version_num = int(version_dir.name[1:])
                    self.logger.info(f"버전 번호 추출: {version_num}")
                    
                    # 시스템 워커 ID 가져오기
                    worker_id = self.worker_service.get_or_create_system_worker()
                    
                    # 버전 생성 또는 업데이트
                    version = self.get_version_by_name(shot_id, version_num)
                    if not version:
                        self.logger.info(f"동기화 할 버전이 없습니다.")
                    else:
                        self.logger.debug(f"이미 존재하는 버전 건너뛰기 - Shot ID: {shot_id}, 버전: {version_num}")
                        
                except ValueError:
                    self.logger.error(f"잘못된 버전 디렉토리 이름: {version_dir.name}")
                    continue
                
            self.logger.info(f"버전 동기화 완료 - 생성된 버전 수: {version_count}")
                
        except Exception as e:
            self.logger.error(f"버전 동기화 중 오류 발생: {str(e)}", exc_info=True)

    def update_project_path(self, project_id, path):
        """프로젝트 경로 업데이트"""
        try:
            cursor = self.db_connector.cursor()
            cursor.execute("""
                UPDATE PROJECTS 
                SET PATH = ?
                WHERE ID = ?
            """, (str(path) if path else None, project_id))
            self.db_connector.commit()
            return True
        except Exception as e:
            self.logger.error(f"프로젝트 경로 업데이트 실패: {str(e)}")
            self.db_connector.rollback()
            return False