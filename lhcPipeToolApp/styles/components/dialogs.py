"""다이얼로그 스타일 정의"""
from ..base import COLORS, SIZES, FONTS

def get_dialog_style():
    return f"""
        /* 기본 다이얼로그 스타일 */
        QDialog {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
        }}

        /* 다이얼로그 내부 위젯 스타일 */
        QDialog QLabel {{
            color: {COLORS['text']};
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        QDialog QLineEdit, QDialog QTextEdit, QDialog QComboBox {{
            background-color: {COLORS['surface']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            color: {COLORS['text']};
            padding: {SIZES['spacing_medium']}px;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        /* 콤보박스 특수 스타일 */
        QDialog QComboBox {{
            padding-right: {SIZES['spacing_xlarge']}px;
        }}

        QDialog QComboBox::drop-down {{
            border: none;
            width: {SIZES['spacing_xlarge']}px;
        }}

        QDialog QComboBox::down-arrow {{
            image: url(resources/icons/ue-arrow-down.svg);
            width: {SIZES['icon_size_small']}px;
            height: {SIZES['icon_size_small']}px;
        }}

        QDialog QComboBox QAbstractItemView {{
            background-color: {COLORS['surface']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            selection-background-color: {COLORS['selected']};
        }}

        /* 그룹박스 스타일 */
        QDialog QGroupBox {{
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            margin-top: {SIZES['spacing_large']}px;
            padding-top: {SIZES['spacing_large']}px;
            font-weight: {FONTS['weight_medium']};
        }}

        QDialog QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 {SIZES['spacing_medium']}px;
            color: {COLORS['text']};
        }}

        /* 스크롤바 스타일 */
        QDialog QScrollBar:vertical {{
            background-color: {COLORS['background']};
            width: {SIZES['spacing_medium']}px;
            margin: 0;
        }}

        QDialog QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: {SIZES['border_radius_small']}px;
            min-height: 20px;
        }}

        QDialog QScrollBar::add-line:vertical,
        QDialog QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}

        QDialog QScrollBar::add-page:vertical,
        QDialog QScrollBar::sub-page:vertical {{
            background: none;
        }}

        /* 메시지박스 스타일 */
        QMessageBox {{
            background-color: {COLORS['background']};
        }}

        QMessageBox QLabel {{
            color: {COLORS['text']};
            font-size: {SIZES['font_size']}px;
        }}

        /* 탭 위젯 스타일 (Settings Dialog 등에서 사용) */
        QDialog QTabWidget::pane {{
            border: {SIZES['border_width']}px solid {COLORS['border']};
            background-color: {COLORS['surface']};
        }}

        QDialog QTabBar::tab {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            padding: {SIZES['spacing_medium']}px {SIZES['spacing_large']}px;
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-bottom: none;
            border-top-left-radius: {SIZES['border_radius']}px;
            border-top-right-radius: {SIZES['border_radius']}px;
        }}

        QDialog QTabBar::tab:selected {{
            background-color: {COLORS['selected']};
        }}

        QDialog QTabBar::tab:hover:!selected {{
            background-color: {COLORS['hover']};
        }}
    """
