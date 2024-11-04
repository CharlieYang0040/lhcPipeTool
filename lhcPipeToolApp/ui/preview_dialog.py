"""버전 프리뷰 다이얼로그"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                              QPushButton, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import cv2
import numpy as np
from pathlib import Path

class PreviewDialog(QDialog):
    def __init__(self, preview_path, parent=None):
        super().__init__(parent)
        self.preview_path = Path(preview_path)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Version Preview")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        
        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 프리뷰 표시 레이블
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        scroll_area.setWidget(self.preview_label)
        
        # 닫기 버튼
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.load_preview()
        
    def load_preview(self):
        """프리뷰 파일 로드"""
        if not self.preview_path.exists():
            self.preview_label.setText("Preview file not found!")
            return
            
        if self.preview_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            self.load_image()
        elif self.preview_path.suffix.lower() in ['.mp4', '.mov']:
            self.load_video_thumbnail()
            
    def load_image(self):
        """이미지 파일 로드"""
        pixmap = QPixmap(str(self.preview_path))
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)
        
    def load_video_thumbnail(self):
        """비디오 썸네일 추출"""
        try:
            cap = cv2.VideoCapture(str(self.preview_path))
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # OpenCV BGR을 RGB로 변환
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                
                # QImage로 변환
                q_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                
                # 크기 조정 및 표시
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText("Failed to load video thumbnail!")
        except Exception as e:
            self.preview_label.setText(f"Error loading video: {e}")