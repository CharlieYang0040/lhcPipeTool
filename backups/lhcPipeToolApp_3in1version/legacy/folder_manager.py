# folder_manager.py

import os
from PySide6.QtWidgets import QTreeWidgetItem

class FolderManager:
    def __init__(self, base_path):
        self.base_path = base_path
    
    def load_projects(self, tree_widget):
        """프로젝트별로 시퀀스/샷 로드"""
        tree_widget.clear()  # 기존 트리 비우기
        if os.path.exists(self.base_path):
            projects = os.listdir(self.base_path)
            for project in projects:
                project_path = os.path.join(self.base_path, project)
                if os.path.isdir(project_path):
                    project_item = QTreeWidgetItem([project])
                    tree_widget.addTopLevelItem(project_item)
                    self.load_sequences(project_item, project_path)
    
    def load_sequences(self, project_item, project_path):
        """시퀀스 로드"""
        sequences = os.listdir(project_path)
        for sequence in sequences:
            sequence_path = os.path.join(project_path, sequence)
            if os.path.isdir(sequence_path):
                sequence_item = QTreeWidgetItem([sequence])
                project_item.addChild(sequence_item)
                self.load_shots(sequence_item, sequence_path)
    
    def load_shots(self, sequence_item, sequence_path):
        """샷 로드"""
        shots = os.listdir(sequence_path)
        for shot in shots:
            shot_path = os.path.join(sequence_path, shot)
            if os.path.isdir(shot_path):
                shot_item = QTreeWidgetItem([shot])
                sequence_item.addChild(shot_item)
