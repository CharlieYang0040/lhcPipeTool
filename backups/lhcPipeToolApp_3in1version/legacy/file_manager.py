# file_manager.py

import os
import json

class FileManager:
    def __init__(self, base_path):
        self.base_path = base_path

    def load_json(self, file_path):
        """JSON 파일을 읽어오는 함수"""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}

    def save_json(self, file_path, data):
        """JSON 파일에 데이터를 저장하는 함수"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_project_version_file(self):
        return os.path.join(self.base_path, "version.json")
    
    def get_sequence_version_file(self, sequence_name):
        return os.path.join(self.base_path, sequence_name, "version.json")
    
    def get_shot_version_file(self, sequence_name, shot_name):
        return os.path.join(self.base_path, sequence_name, shot_name, "version.json")
    
    def get_worker_file(self):
        """TestSequence 바깥의 workers.json 경로 반환"""
        return os.path.join(os.path.dirname(self.base_path), "workers.json")
