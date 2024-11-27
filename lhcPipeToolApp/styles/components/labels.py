"""라벨 스타일 정의"""

from ..base import COLORS, SIZES, FONTS

def get_label_style():
    return f"""
        QLabel {{
            background-color: {COLORS['surface']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            color: {COLORS['text']};
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}
    """