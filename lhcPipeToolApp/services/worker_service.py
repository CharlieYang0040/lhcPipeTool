"""작업자 관리 서비스"""
from ..utils.event_system import EventSystem
from ..utils.logger import setup_logger

class WorkerService:
    def __init__(self, worker_model):
        self.worker_model = worker_model
        self.logger = setup_logger(__name__)
        
    def create_worker(self, name, password, department=None):
        """작업자 생성"""
        # 동일한 이름의 작업자가 있는지 확인
        if self.get_worker_by_name(name):
            raise ValueError("이미 존재하는 작업자 이름입니다.")

        try:
            self.logger.info(f"작업자 생성 시도: 이름: {name}, 부서: {department}")

            #모델의 create 메서드 호출
            worker_id = self.worker_model.create(name, password, department=department)
            if worker_id:
                self.worker_model._commit()
                EventSystem.notify('worker_updated') #이벤트 발생

                self.logger.info(f"작업자 생성 성공 - ID: {worker_id}")
                return worker_id
            else:
                raise Exception("작업자 생성 실패")
            
        except Exception as e:
            self.logger.error(f"작업자 생성 실패: {str(e)}", exc_info=True)
            raise

    def get_worker_by_id(self, worker_id):
        """ID로 작업자 정보 조회"""
        return self.worker_model.get_by_id(worker_id)

    def get_worker_by_name(self, name):
        """이름으로 작업자 정보 조회"""
        return self.worker_model.get_by_name(name)

    def get_all_workers(self):
        """모든 작업자 목록 조회"""
        return self.worker_model.get_all()

    def update_worker(self, worker_id, name=None, department=None):
        """작업자 정보 수정"""
        # 이름 변경 시 중복 체크
        if name:
            existing_worker = self.get_worker_by_name(name)
            if existing_worker and existing_worker[0] != worker_id:
                raise ValueError("이미 존재하는 작업자 이름입니다.")
        
        try:
            self.logger.info(f"작업자 정보 수정 시도: ID: {worker_id}, 이름: {name}, 부서: {department}")
            self.worker_model.update(worker_id, name, department)
            self.worker_model._commit()
            EventSystem.notify('worker_updated')
            self.logger.info(f"작업자 정보 수정 성공 - ID: {worker_id}")
        except Exception as e:
            self.logger.error(f"작업자 정보 수정 실패: {str(e)}", exc_info=True)
            self.worker_model._rollback()
            raise ValueError("작업자 정보 수정 실패")

    def delete_worker(self, worker_id):
        """작업자 삭제"""
        try:
            # 작업자가 존재하는지 확인
            worker = self.get_worker_by_id(worker_id)
            if not worker:
                raise ValueError("존재하지 않는 작업자입니다.")
            
            self.worker_model.delete(worker_id)
            self.worker_model._commit()
            EventSystem.notify('worker_updated')
            self.logger.info(f"작업자 삭제 성공 - ID: {worker_id}")
            return True
            
        except Exception as e:
            self.worker_model._rollback()
            raise ValueError(f"작업자 삭제 실패: {str(e)}")

    def get_worker_versions(self, worker_id):
        """작업자의 버전 목록 조회"""
        # TODO: Version 모델과 연동하여 작업자가 작업한 버전 목록 조회
        pass

    def validate_worker_data(self, name):
        """작업자 데이터 유효성 검사"""
        if not name or len(name.strip()) == 0:
            raise ValueError("작업자 이름은 필수입니다.")
        
        return True
    
    def get_or_create_system_worker(self):
        """시스템 워커 ID 조회 또는 생성"""
        try:
            system_worker = self.worker_model.get_by_name('system')
            
            if system_worker:
                worker_id = system_worker[0]
                self.logger.debug(f"기존 시스템 워커 ID 사용: {worker_id}")
                return worker_id
                
            self.logger.info("시스템 워커 생성 중...")
            worker_id = self.worker_model.create('system', department='system')
            if worker_id:
                self.worker_model._commit()
                self.logger.info(f"새 시스템 워커 생성됨 - ID: {worker_id}")
                return worker_id
            else:
                self.worker_model._rollback()
                raise Exception("시스템 워커 생성 실패")
            
        except Exception as e:
            self.logger.error(f"시스템 워커 조회/생성 중 오류: {str(e)}", exc_info=True)
            raise

    def verify_credentials(self, name, hashed_password):
        """작업자 인증"""
        return self.worker_model.verify_credentials(name, hashed_password)

    def reset_password(self, worker_id, new_password):
        """작업자 비밀번호 초기화"""
        try:
            reset_result = self.worker_model.reset_password(worker_id, new_password)
            self.logger.info(f"비밀번호 초기화 결과: {reset_result}")
            if reset_result:
                self.worker_model._commit()
                return True
            else:
                raise Exception("비밀번호 초기화 실패")
        except Exception as e:
            self.logger.error(f"비밀번호 초기화 중 오류: {str(e)}", exc_info=True)
            self.worker_model._rollback()
            raise ValueError(f"비밀번호 초기화 실패: {str(e)}")