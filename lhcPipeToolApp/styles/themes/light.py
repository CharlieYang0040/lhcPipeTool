"""라이트 테마 정의"""
from ..base import SIZES, FONTS

# 라이트 테마 색상 정의
LIGHT_COLORS = {
    'background': '#f5f5f5',
    'surface': '#ffffff',
    'border': '#e0e0e0',
    'text': '#2c2c2c',
    'text_secondary': '#757575',
    'hover': '#eaeaea',
    'selected': '#e3e3e3',
    'pressed': '#d5d5d5',
    'disabled': '#f0f0f0',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
    'info': '#2196f3',
}

def get_light_theme():
    # 기본 라이트 테마 스타일
    # 다크 테마와 동일한 구조를 가지지만 다른 색상 사용
    base_style = f"""
        /* 기본 위젯 스타일 */
        QWidget {{
            background-color: {LIGHT_COLORS['background']};
            color: {LIGHT_COLORS['text']};
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        /* 여기에 다크 테마와 동일한 구조로 라이트 테마 스타일 정의 */
        /* 현재는 다크 테마만 사용하므로 기본 구조만 포함 */
    """

    return base_style
