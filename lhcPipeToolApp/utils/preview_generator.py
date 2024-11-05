"""프리뷰 생성기"""
import cv2
import glob
import re
from pathlib import Path
from .logger import setup_logger

class PreviewGenerator:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.max_size = 4096  # 최대 이미지 크기
        
    def create_preview(self, file_path):
        """파일로부터 프리뷰 이미지 생성"""
        try:
            self.logger.debug(f"프리뷰 생성 시작 - file_path: {file_path}")
            
            if not file_path:
                self.logger.warning("파일 경로가 비어있음")
                return None
                
            # 파일 경로 처리
            file_path = Path(file_path)
            preview_path = file_path.parent / f"{file_path.stem}_preview.png"
            
            # 이미지 시퀀스 확인
            if self._is_sequence(str(file_path)):
                img = self._handle_sequence(file_path)
            else:
                img = self._handle_video(file_path)
                
            if img is None:
                return None
                
            # 이미지 크기 조정
            img = self._resize_image(img)
            
            # 프리뷰 저장
            cv2.imwrite(str(preview_path), img)
            self.logger.info(f"프리뷰 생성 완료: {preview_path}")
            
            return str(preview_path)
            
        except Exception as e:
            self.logger.error(f"프리뷰 생성 실패: {str(e)}", exc_info=True)
            return None
            
    def _is_sequence(self, file_path):
        """이미지 시퀀스 패턴 확인"""
        sequence_pattern = re.compile(r'.*?(?:%0\d+d|\#{1,4}|\$F\d+).*?')
        return bool(sequence_pattern.match(file_path))
        
    def _handle_sequence(self, file_path):
        """이미지 시퀀스 처리"""
        try:
            self.logger.debug("이미지 시퀀스 파일 처리")
            
            # 시퀀스 패턴 매칭
            patterns = [
                (r'%0\d+d', r'\d+'),  # %04d 형식
                (r'\#{1,4}', r'\d+'),  # #### 형식
                (r'\$F\d+', r'\d+')    # $F4 형식
            ]
            
            file_str = str(file_path)
            sequence_files = []
            
            for pattern, num_pattern in patterns:
                if re.search(pattern, file_str):
                    search_pattern = re.sub(pattern, num_pattern, file_str)
                    sequence_files = sorted(glob.glob(search_pattern))
                    break
                    
            if not sequence_files:
                raise ValueError("시퀀스 파일을 찾을 수 없습니다.")
                
            self.logger.debug(f"첫 번째 시퀀스 파일: {sequence_files[0]}")
            img = cv2.imread(sequence_files[0])
            
            if img is None:
                raise ValueError("이미지를 읽을 수 없습니다.")
                
            return img
            
        except Exception as e:
            self.logger.error(f"시퀀스 처리 실패: {str(e)}")
            return None
            
    def _handle_video(self, file_path):
        """비디오 파일 처리"""
        try:
            self.logger.debug("비디오 파일 처리")
            cap = cv2.VideoCapture(str(file_path))
            
            if not cap.isOpened():
                raise ValueError("비디오 파일을 열 수 없습니다.")
                
            # 중간 프레임 추출
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            middle_frame = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, img = cap.read()
            cap.release()
            
            if not ret:
                raise ValueError("프레임을 읽을 수 없습니다.")
                
            return img
            
        except Exception as e:
            self.logger.error(f"비디오 처리 실패: {str(e)}")
            return None
            
    def _resize_image(self, img):
        """이미지 크기 조정"""
        try:
            height, width = img.shape[:2]
            
            if width > self.max_size or height > self.max_size:
                if width > height:
                    new_width = self.max_size
                    new_height = int(height * (self.max_size / width))
                else:
                    new_height = self.max_size
                    new_width = int(width * (self.max_size / height))
                    
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                
            return img
            
        except Exception as e:
            self.logger.error(f"이미지 크기 조정 실패: {str(e)}")
            return None