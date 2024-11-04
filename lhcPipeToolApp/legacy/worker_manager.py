# worker_manager.py

class WorkerManager:
    def __init__(self, file_manager):
        self.file_manager = file_manager

    def add_version(self, sequence_name, shot_name, version, worker):
        """샷에 새로운 버전과 작업자 정보 추가하고 파일에 저장"""
        shot_file = self.file_manager.get_shot_version_file(sequence_name, shot_name)
        data = self.file_manager.load_json(shot_file)
        
        if "versions" not in data:
            data["versions"] = []

        data["versions"].append({"version": version, "worker": worker})
        self.file_manager.save_json(shot_file, data)

    def add_worker(self, worker_name):
        """workers.json에 새로운 작업자를 추가"""
        worker_file = self.file_manager.get_worker_file()
        data = self.file_manager.load_json(worker_file)
        
        if "workers" not in data:
            data["workers"] = []

        if worker_name not in data["workers"]:
            data["workers"].append(worker_name)
        
        self.file_manager.save_json(worker_file, data)

    def get_workers(self):
        """workers.json에서 작업자 목록을 불러오기"""
        worker_file = self.file_manager.get_worker_file()
        data = self.file_manager.load_json(worker_file)
        return data.get("workers", [])
