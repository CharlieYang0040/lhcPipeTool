"""버전 서비스"""
from .base_version_service import BaseVersionService

class ShotVersionService(BaseVersionService):
    def __init__(self, db_connector, logger):
        super().__init__(db_connector, logger)
        self.table_name = "VERSIONS"
        
    def get_foreign_key(self):
        return "shot_id"

class SequenceVersionService(BaseVersionService):
    def __init__(self, db_connector, logger):
        super().__init__(db_connector, logger)
        self.table_name = "SEQUENCE_VERSIONS"
        
    def get_foreign_key(self):
        return "sequence_id"

class ProjectVersionService(BaseVersionService):
    def __init__(self, db_connector, logger):
        super().__init__(db_connector, logger)
        self.table_name = "PROJECT_VERSIONS"
        
    def get_foreign_key(self):
        return "project_id"