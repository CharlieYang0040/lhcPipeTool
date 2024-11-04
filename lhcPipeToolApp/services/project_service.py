"""프로젝트 관리 서비스"""
from ..models.project import Project
from ..models.sequence import Sequence
from ..models.shot import Shot
from ..utils.logger import setup_logger
from pathlib import Path
from ..database.table_manager import TableManager

class ProjectService:
    def __init__(self, connector):
        self.connector = connector
        self.project_model = Project(connector)
        self.sequence_model = Sequence(connector)
        self.shot_model = Shot(connector)
        self.logger = setup_logger(__name__)
        self.table_manager = TableManager(connector)

    def create_project(self, name, path=None):
        """프로젝트 생성"""
        try:
            self.logger.info(f"프로젝트 생성 시도: name={name}, path={path}")
            
            # 테이블이 없을 경우 생성
            if not self.table_manager.create_table('projects'):
                # 테이블이 이미 존재하면 컬럼 추가 시도
                self.table_manager.add_path_columns()
                self.table_manager.add_description_columns()
            
            cursor = self.connector.cursor()
            sql = """
                INSERT INTO PROJECTS (NAME, PATH)
                VALUES (?, ?)
                RETURNING ID
            """
            cursor.execute(sql, (name, str(path) if path else None))
            project_id = cursor.fetchone()[0]
            self.connector.commit()
            return project_id
        except Exception as e:
            self.logger.error(f"프로젝트 생성 실패: {str(e)}")
            self.connector.rollback()
            raise

    def get_project_structure(self, project_id):
        """프로젝트의 전체 구조 조회"""
        project = self.project_model.get_by_id(project_id)
        if not project:
            return None

        sequences = self.sequence_model.get_by_project(project_id)
        structure = {
            "project": project,
            "sequences": {}
        }

        for seq in sequences:
            shots = self.shot_model.get_by_sequence(seq[0])
            structure["sequences"][seq[0]] = {
                "info": seq,
                "shots": shots
            }

        return structure

    def create_sequence(self, project_id, name):
        """시퀀스 생성"""
        try:
            self.logger.info(f"시퀀스 생성 시도: project_id={project_id}, name={name}")
            
            # 테이블 생성 확인
            self.table_manager.create_table('sequences')
            
            cursor = self.connector.cursor()
            sql = """
                INSERT INTO SEQUENCES (PROJECT_ID, NAME)
                VALUES (?, ?)
                RETURNING ID
            """
            cursor.execute(sql, (project_id, str(name)))
            sequence_id = cursor.fetchone()[0]
            self.connector.commit()
            return sequence_id
        except Exception as e:
            self.logger.error(f"시퀀스 생성 실패: {str(e)}")
            self.connector.rollback()
            raise

    def create_shot(self, sequence_id, name, status="pending", description=None):
        """샷 생성"""
        try:
            self.logger.info(f"샷 생성 시도: sequence_id={sequence_id}, name={name}")
            
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
            return shot_id
        except Exception as e:
            self.logger.error(f"샷 생성 실패: {str(e)}")
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
            for project_dir in root_path.iterdir():
                if not project_dir.is_dir():
                    continue
                    
                # 프로젝트 생성 또는 업데이트
                project = self.get_project_by_name(project_dir.name)
                if not project:
                    project_id = self.create_project(project_dir.name)
                else:
                    project_id = project[0]
                
                # 시퀀스 동기화
                self._sync_sequences(project_id, project_dir)
                
        except Exception as e:
            self.logger.error(f"프로젝트 구조 동기화 실패: {str(e)}")
            raise

    def _sync_sequences(self, project_id, project_dir):
        """시퀀스 동기화"""
        for seq_dir in project_dir.iterdir():
            if not seq_dir.is_dir():
                continue
                
            sequence = self.get_sequence_by_name(project_id, seq_dir.name)
            if not sequence:
                sequence_id = self.create_sequence(project_id, seq_dir.name)
            else:
                sequence_id = sequence[0]
                
            # 샷 동기화
            self._sync_shots(sequence_id, seq_dir)

    def _sync_shots(self, sequence_id, seq_dir):
        """샷 동기화"""
        for shot_dir in seq_dir.iterdir():
            if not shot_dir.is_dir():
                continue
                
            shot = self.get_shot_by_name(sequence_id, shot_dir.name)
            if not shot:
                self.create_shot(sequence_id, shot_dir.name)

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