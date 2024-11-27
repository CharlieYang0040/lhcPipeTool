"""프레임 스타일 정의"""
from ..base import COLORS, SIZES

def get_frame_style():
    return f"""
        QFrame {{
            background-color: {COLORS['surface']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            padding: {SIZES['spacing_small']}px;
        }}
    """
