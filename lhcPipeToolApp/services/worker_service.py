"""작업자 관리 서비스"""
from ..models.worker import Worker
from ..utils.logger import setup_logger

class WorkerService:
    def __init__(self, connector):
        self.worker_model = Worker(connector)
        self.logger = setup_logger(__name__)
        
    def create_worker(self, name, email=None, department=None):
        """작업자 생성"""
        # 동일한 이름의 작업자가 있는지 확인
        existing_worker = self.get_worker_by_name(name)
        if existing_worker:
            raise ValueError("이미 존재하는 작업자 이름입니다.")
        
        return self.worker_model.create(name, department=department)

    def get_worker_by_id(self, worker_id):
        """ID로 작업자 정보 조회"""
        return self.worker_model.get_by_id(worker_id)

    def get_worker_by_name(self, name):
        """이름으로 작업자 정보 조회"""
        return self.worker_model.get_by_name(name)

    def get_all_workers(self):
        """모든 작업자 목록 조회"""
        return self.worker_model.get_all()

    def update_worker(self, worker_id, name=None, email=None, department=None):
        """작업자 정보 수정"""
        # 이름 변경 시 중복 체크
        if name:
            existing_worker = self.get_worker_by_name(name)
            if existing_worker and existing_worker[0] != worker_id:
                raise ValueError("이미 존재하는 작업자 이름입니다.")
        
        return self.worker_model.update(worker_id, name, email, department)

    def delete_worker(self, worker_id):
        """작업자 삭제"""
        try:
            # 작업자가 존재하는지 확인
            worker = self.get_worker_by_id(worker_id)
            if not worker:
                raise ValueError("존재하지 않는 작업자입니다.")
            
            # TODO: 작업자와 연관된 버전이 있는지 확인
            # versions = self.get_worker_versions(worker_id)
            # if versions:
            #     raise ValueError("버전이 존재하는 작업자는 삭제할 수 없습니다.")
            
            cursor = self.worker_model.connector.cursor()
            cursor.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
            self.worker_model.connector.commit()
            return True
            
        except Exception as e:
            self.worker_model.connector.rollback()
            raise ValueError(f"작업자 삭제 실패: {str(e)}")

    def get_worker_versions(self, worker_id):
        """작업자의 버전 목록 조회"""
        # TODO: Version 모델과 연동하여 작업자가 작업한 버전 목록 조회
        pass

    def validate_worker_data(self, name, email=None):
        """작업자 데이터 유효성 검사"""
        if not name or len(name.strip()) == 0:
            raise ValueError("작업자 이름은 필수입니다.")
            
        if email and '@' not in email:
            raise ValueError("유효하지 않은 이메일 형식입니다.")
        
        return True
    
    def get_or_create_system_worker(self):
        """시스템 워커 ID 조회 또는 생성"""
        try:
            cursor = self.worker_model.connector.cursor()
            cursor.execute("SELECT id FROM workers WHERE name = 'system'")
            result = cursor.fetchone()
            
            if result:
                worker_id = result[0]
                self.logger.debug(f"기존 시스템 워커 ID 사용: {worker_id}")
                return worker_id
                
            self.logger.info("시스템 워커 생성 중...")
            cursor.execute("""
                INSERT INTO workers (name, department)
                VALUES ('system', 'system')
                RETURNING id
            """)
            worker_id = cursor.fetchone()[0]
            self.worker_model.connector.commit()
            self.logger.info(f"새 시스템 워커 생성됨 - ID: {worker_id}")
            return worker_id
            
        except Exception as e:
            self.logger.error(f"시스템 워커 조회/생성 중 오류: {str(e)}", exc_info=True)
            raise