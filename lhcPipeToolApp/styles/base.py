"""스타일 기본 변수 정의"""

# 색상 변수
COLORS = {
    # 기본 색상
    'background': '#15151e',          # 메인 배경색
    'surface': '#1a1a24',             # 컴포넌트 배경색
    'border': '#2d2d3d',              # 테두리 색상
    'text': '#e0e0e0',                # 기본 텍스트 색상
    'text_secondary': '#a0a0a0',      # 보조 텍스트 색상
    
    # 상호작용 색상
    'hover': '#363647',               # 호버 상태 색상
    'selected': '#2d2d3d',            # 선택된 상태 색상
    'pressed': '#404052',             # 눌린 상태 색상
    'disabled': '#1f1f2c',            # 비활성화 상태 색상
    
    # 상태 표시 색상
    'success': '#4caf50',             # 성공 상태
    'warning': '#ff9800',             # 경고 상태
    'error': '#f44336',               # 에러 상태
    'info': '#2196f3',                # 정보 상태
}

# 크기 변수
SIZES = {
    # 여백
    'input_height': 25,
    'spacing_tiny': 2,
    'spacing_small': 4,
    'spacing_medium': 8,
    'spacing_large': 12,
    'spacing_xlarge': 16,
    'spacing_xxlarge': 24,
    'spacing_xxxlarge': 32,
    
    # 테두리
    'border_width': 1,
    'border_radius_small': 4,
    'border_radius': 6,
    'border_radius_large': 8,
    
    # 컴포넌트 크기
    'icon_size_small': 16,
    'icon_size': 24,
    'icon_size_large': 32,
    
    # 폰트 크기
    'font_size_small': 10,
    'font_size': 12,
    'font_size_large': 14,
    'font_size_xlarge': 16,
}

# 폰트 설정
FONTS = {
    'family': 'Segoe UI',
    'weight_normal': 400,
    'weight_medium': 500,
    'weight_bold': 700,
}

# Z-index 레이어
LAYERS = {
    'base': 0,
    'above': 1,
    'dropdown': 1000,
    'modal': 2000,
    'tooltip': 3000,
}
