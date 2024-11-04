"""프로젝트 관리 서비스"""
from ..models.project import Project
from ..models.sequence import Sequence
from ..models.shot import Shot
from ..models.version import Version
from ..utils.logger import setup_logger
from pathlib import Path
from ..database.table_manager import TableManager
from .worker_service import WorkerService

class ProjectService:
    def __init__(self, connector):
        self.connector = connector
        self.project_model = Project(connector)
        self.sequence_model = Sequence(connector)
        self.shot_model = Shot(connector)
        self.version_model = Version(connector)
        self.logger = setup_logger(__name__)
        self.table_manager = TableManager(connector)
        self.worker_service = WorkerService(connector)

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
                    latest_version = self.version_model.get_latest_version(shot[0])
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

    def create_project(self, name, path=None, description=None):
        """프로젝트 생성"""
        try:
            self.logger.info(f"""프로젝트 생성 시도:
                이름: {name}
                경로: {path}
                설명: {description}
            """)
            
            # 테이블 생성 확인
            self.table_manager.create_table('projects')
            
            cursor = self.connector.cursor()
            sql = """
                INSERT INTO PROJECTS (NAME, PATH, DESCRIPTION)
                VALUES (?, ?, ?)
                RETURNING ID
            """
            cursor.execute(sql, (name, str(path) if path else None, description))
            project_id = cursor.fetchone()[0]
            self.connector.commit()
            
            self.logger.info(f"프로젝트 생성 성공 - ID: {project_id}")
            return project_id
            
        except Exception as e:
            self.logger.error(f"프로젝트 생성 실패: {str(e)}")
            self.connector.rollback()
            raise

    def create_sequence(self, project_id, name, description=None):
        """시퀀스 생성"""
        try:
            self.logger.info(f"""시퀀스 생성 시도:
                프로젝트 ID: {project_id}
                이름: {name}
                설명: {description}
            """)
            
            # 테이블 생성 확인
            self.table_manager.create_table('sequences')
            
            cursor = self.connector.cursor()
            sql = """
                INSERT INTO SEQUENCES (PROJECT_ID, NAME, DESCRIPTION)
                VALUES (?, ?, ?)
                RETURNING ID
            """
            cursor.execute(sql, (project_id, str(name), description))
            sequence_id = cursor.fetchone()[0]
            self.connector.commit()
            
            self.logger.info(f"시퀀스 생성 성공 - ID: {sequence_id}")
            return sequence_id
            
        except Exception as e:
            self.logger.error(f"시퀀스 생성 실패: {str(e)}")
            self.connector.rollback()
            raise

    def create_shot(self, sequence_id, name, status="pending", description=None):
        """샷 생성"""
        try:
            self.logger.info(f"""샷 생성 시도:
                시퀀스 ID: {sequence_id}
                이름: {name}
                상태: {status}
                설명: {description}
            """)
            
            # 테이블 생성 확인
            self.table_manager.create_table('shots')
            
            cursor = self.connector.cursor()
            sql = """
                INSERT INTO SHOTS (SEQUENCE_ID, NAME, STATUS, DESCRIPTION)
                VALUES (?, ?, ?, ?)
                RETURNING ID
            """
            cursor.execute(sql, (sequence_id, str(name), status, description))
            shot_id = cursor.fetchone()[0]
            self.connector.commit()
            
            self.logger.info(f"샷 생성 성공 - ID: {shot_id}")
            return shot_id
            
        except Exception as e:
            self.logger.error(f"샷 생성 실패: {str(e)}")
            self.connector.rollback()
            raise

    def create_version(self, shot_id, name, version_number, worker_id, status="pending", file_path=None, preview_path=None, render_path=None, comment=None):
        """버전 생성"""
        try:
            self.logger.info(f"버전 생성 시도: shot_id={shot_id}, name={name}")

            # 테이블 생성 확인
            self.table_manager.create_table('versions')

            cursor = self.connector.cursor()
            sql = """
                INSERT INTO VERSIONS (SHOT_ID, NAME, VERSION_NUMBER, WORKER_ID, STATUS, FILE_PATH, PREVIEW_PATH, RENDER_PATH, COMMENT)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING ID
            """
            cursor.execute(sql, (shot_id, str(name), version_number, worker_id, status, file_path, preview_path, render_path, comment))
            version_id = cursor.fetchone()[0]
            self.connector.commit()
            return version_id
        except Exception as e:
            self.logger.error(f"버전 생성 실패: {str(e)}")
            self.connector.rollback()
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
        """샷 정 조회"""
        return self.shot_model.get_by_id(shot_id)

    def get_all_projects(self):
        """모든 프로젝트 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("SELECT * FROM projects")
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"프로젝트 조회 실패: {str(e)}")
            return []

    def get_project_by_name(self, name):
        """프로젝트 이름으로 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"프로젝트 조회 실패: {str(e)}")
            return None

    def get_sequence_by_name(self, project_id, name):
        """시퀀스 이름으로 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("""
                SELECT * FROM sequences 
                WHERE project_id = ? AND name = ?
            """, (project_id, name))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"시퀀스 조회 실패: {str(e)}")
            return None

    def get_shot_by_name(self, sequence_id, name):
        """샷 이름으로 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("""
                SELECT * FROM shots 
                WHERE sequence_id = ? AND name = ?
            """, (sequence_id, name))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"샷 조회 실패: {str(e)}")
            return None
        
    def get_version_by_name(self, shot_id, version_number):
        """버전 이름으로 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("""
                SELECT * FROM versions WHERE shot_id = ? AND version_number = ?
            """, (shot_id, version_number))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"버전 조회 실패: {str(e)}")
            return None

    def get_project_by_path(self, path):
        """경로 프로젝트 조회"""
        try:
            cursor = self.connector.cursor()
            cursor.execute("SELECT * FROM projects WHERE path = ?", (path,))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"프로젝트 조회 실패: {str(e)}")
            return None

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
                    # 프로젝트 생성 ��는 업데이트
                    project = self.get_project_by_name(project_dir.name)
                    if not project:
                        self.logger.info(f"""새 프로젝트 생성 중:
                            이름: {project_dir.name}
                            경로: {project_dir}
                        """)
                        project_id = self.create_project(
                            name=project_dir.name,
                            path=str(project_dir)
                        )
                        project_count += 1
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
                        self.logger.info(f"""새 시퀀스 생성 중:
                            Project ID: {project_id}
                            이름: {seq_dir.name}
                        """)
                        sequence_id = self.create_sequence(
                            project_id=project_id,
                            name=seq_dir.name
                        )
                        sequence_count += 1
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
                        self.logger.info(f"""새 샷 생성 중:
                            Sequence ID: {sequence_id}
                            이름: {shot_dir.name}
                        """)
                        shot_id = self.create_shot(
                            sequence_id=sequence_id,
                            name=shot_dir.name,
                            status="pending"
                        )
                        shot_count += 1
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
                        self.logger.info(f"""새 버전 생성 중:
                            Shot ID: {shot_id}
                            버전 이름: {version_dir.name}
                            버전 번호: {version_num}
                            경로: {version_dir}
                        """)
                        
                        self.version_model.create(
                            version_name=version_dir.name,
                            shot_id=shot_id,
                            version_number=version_num,
                            worker_id=worker_id,
                            file_path=str(version_dir),
                            comment="Auto-imported from filesystem"
                        )
                        version_count += 1
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
            cursor = self.connector.cursor()
            cursor.execute("""
                UPDATE PROJECTS 
                SET PATH = ?
                WHERE ID = ?
            """, (str(path) if path else None, project_id))
            self.connector.commit()
            return True
        except Exception as e:
            self.logger.error(f"프로젝트 경로 업데이트 실패: {str(e)}")
            self.connector.rollback()
            return False