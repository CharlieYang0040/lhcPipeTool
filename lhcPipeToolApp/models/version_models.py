"""버전 모델들"""
from .base_version_model import BaseVersionModel

class ShotVersion(BaseVersionModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.table_name = "VERSIONS"
        self.item_type = "shot"

class SequenceVersion(BaseVersionModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.table_name = "SEQUENCE_VERSIONS"
        self.item_type = "sequence"

class ProjectVersion(BaseVersionModel):
    def __init__(self, db_connector):
        super().__init__(db_connector)
        self.table_name = "PROJECT_VERSIONS"
        self.item_type = "project"