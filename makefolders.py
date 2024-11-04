import os

def create_test_folders(base_path):
    # 테스트 프로젝트 목록
    project_names = ["warrior_hori", "warrior_wide"]
    
    # 샷 목록
    shot_names = ["Shot001", "Shot002", "Shot003"]

    # 각 프로젝트별 폴더 생성
    for project in project_names:
        project_folder = os.path.join(base_path, project)

        # 각 샷별 폴더 생성
        for shot in shot_names:
            shot_folder = os.path.join(project_folder, shot)
            os.makedirs(shot_folder, exist_ok=True)  # 중복 방지하여 폴더 생성

            # 테스트 파일 생성 (버전 001, 002, 소문자 v)
            for version in range(1, 3):
                version_folder = os.path.join(shot_folder, f"v{version:03d}")
                os.makedirs(version_folder, exist_ok=True)  # 버전별 폴더 생성

                # 이미지 시퀀스 파일 생성 (image_001.exr, image_002.exr)
                for frame in range(1, 3):  # 이미지 시퀀스는 2개만 생성
                    image_file = os.path.join(version_folder, f"image_{frame:03d}.exr")
                    with open(image_file, 'w') as f:
                        f.write(f"Test image sequence for {shot}, version {version}, frame {frame}\n")
    
    print(f"Test folder structure with version and image sequences created at {base_path}")

# 테스트 경로 설정
base_path = r"D:\WORKDATA\lhcPipeTool\TestSequence"
create_test_folders(base_path)
