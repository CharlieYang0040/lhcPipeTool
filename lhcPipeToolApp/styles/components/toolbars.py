"""버튼 스타일 정의"""
from ..base import COLORS, SIZES

def get_toolbar_style():
    return f"""
        QToolBar {{
            background-color: {COLORS['surface']};
            border: none;
            spacing: {SIZES['spacing_small']}px;
            padding: {SIZES['spacing_small']}px;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: {SIZES['border_radius']}px;
            padding: {SIZES['spacing_small']}px;
            color: {COLORS['text']};
        }}

        QToolButton:hover {{
            background-color: {COLORS['hover']};
        }}
        
        QToolButton:pressed {{
            background-color: {COLORS['pressed']};
        }}
        
        QToolButton:disabled {{
            background-color: {COLORS['disabled']};
            color: {COLORS['text_secondary']};
        }}
        
        /* 특수 버튼 스타일 */
        QToolButton[class="primary"] {{
            background-color: {COLORS['info']};
            border-color: {COLORS['info']};
        }}
        
        QToolButton[class="danger"] {{
            background-color: {COLORS['error']};
            border-color: {COLORS['error']};
        }}
    """