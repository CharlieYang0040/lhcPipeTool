"""입력 컴포넌트 스타일 정의"""
from ..base import COLORS, SIZES, FONTS

def get_input_style():
    return f"""
        /* 기본 라인 에디트 스타일 */
        QLineEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            padding: 4px {SIZES['spacing_medium']}px;
            margin: 1px 0;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
            line-height: {SIZES['font_size']}px;
            selection-background-color: {COLORS['selected']};
        }}

        QLineEdit:hover {{
            border-color: {COLORS['hover']};
        }}

        QLineEdit:focus {{
            border-color: {COLORS['info']};
        }}

        QLineEdit:disabled {{
            background-color: {COLORS['disabled']};
            color: {COLORS['text_secondary']};
        }}

        QLineEdit[readOnly="true"] {{
            background-color: {COLORS['disabled']};
        }}

        /* 텍스트 에디트 스타일 */
        QTextEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            padding: 4px {SIZES['spacing_medium']}px;
            margin: 1px 0;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
            line-height: {SIZES['font_size']}px;
            selection-background-color: {COLORS['selected']};
        }}

        QTextEdit:hover {{
            border-color: {COLORS['hover']};
        }}

        QTextEdit:focus {{
            border-color: {COLORS['info']};
        }}

        /* 콤보 박스 스타일 */
        QComboBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            padding: {SIZES['spacing_medium']}px;
            padding-right: {SIZES['spacing_xlarge']}px;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
            min-width: 6em;
        }}

        QComboBox:hover {{
            border-color: {COLORS['hover']};
        }}

        QComboBox:focus {{
            border-color: {COLORS['info']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: {SIZES['icon_size']}px;
        }}

        QComboBox::down-arrow {{
            image: url(lhcPipeToolApp/resources/icons/ue-arrow-down.svg);
            width: {SIZES['icon_size_small']}px;
            height: {SIZES['icon_size_small']}px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            selection-background-color: {COLORS['selected']};
            outline: none;
        }}

        /* 스핀 박스 스타일 */
        QSpinBox, QDoubleSpinBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            padding: {SIZES['spacing_medium']}px;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: {COLORS['hover']};
        }}

        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {COLORS['info']};
        }}

        /* 체크박스 스타일 */
        QCheckBox {{
            color: {COLORS['text']};
            spacing: {SIZES['spacing_medium']}px;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        QCheckBox::indicator {{
            width: {SIZES['icon_size_small']}px;
            height: {SIZES['icon_size_small']}px;
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius_small']}px;
            background-color: {COLORS['surface']};
        }}

        QCheckBox::indicator:hover {{
            border-color: {COLORS['hover']};
        }}

        QCheckBox::indicator:checked {{
            background-color: {COLORS['info']};
            border-color: {COLORS['info']};
            image: url(lhcPipeToolApp/resources/icons/ue-check.svg);
        }}

        /* 라디오 버튼 스타일 */
        QRadioButton {{
            color: {COLORS['text']};
            spacing: {SIZES['spacing_medium']}px;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        QRadioButton::indicator {{
            width: {SIZES['icon_size_small']}px;
            height: {SIZES['icon_size_small']}px;
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['icon_size_small']}px;
            background-color: {COLORS['surface']};
        }}

        QRadioButton::indicator:hover {{
            border-color: {COLORS['hover']};
        }}

        QRadioButton::indicator:checked {{
            background-color: {COLORS['info']};
            border-color: {COLORS['info']};
            image: url(lhcPipeToolApp/resources/icons/ue-radio-checked.svg);
        }}
    """
