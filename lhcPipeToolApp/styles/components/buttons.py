"""버튼 스타일 정의"""
from ..base import COLORS, SIZES, FONTS

def get_button_style(min_width=80, background_color=COLORS['surface']):
    return f"""
        QPushButton {{
            background-color: {background_color};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            color: {COLORS['text']};
            padding: {SIZES['spacing_medium']}px {SIZES['spacing_large']}px;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
            font-weight: {FONTS['weight_medium']};
            min-width: {min_width}px;
        }}
        
        QPushButton:hover {{
            background-color: {COLORS['hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {COLORS['pressed']};
        }}
        
        QPushButton:disabled {{
            background-color: {COLORS['disabled']};
            color: {COLORS['text_secondary']};
        }}
        
        /* 특수 버튼 스타일 */
        QPushButton[class="primary"] {{
            background-color: {COLORS['info']};
            border-color: {COLORS['info']};
        }}
        
        QPushButton[class="danger"] {{
            background-color: {COLORS['error']};
            border-color: {COLORS['error']};
        }}
    """
