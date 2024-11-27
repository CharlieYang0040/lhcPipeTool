"""다크 테마 정의"""
from ..components.buttons import get_button_style
from ..components.dialogs import get_dialog_style
from ..components.tables import get_table_style
from ..components.trees import get_tree_style
from ..components.inputs import get_input_style
from ..base import COLORS, SIZES, FONTS

def get_dark_theme():
    # 기본 어플리케이션 스타일
    base_style = f"""
        /* 기본 위젯 스타일 */
        QWidget {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        /* 메인윈도우 스타일 */
        QMainWindow {{
            background-color: {COLORS['background']};
        }}

        /* 스플리터 스타일 */
        QSplitter {{
            background-color: {COLORS['background']};
        }}

        QSplitter::handle {{
            background-color: {COLORS['border']};
        }}

        QSplitter::handle:horizontal {{
            width: {SIZES['border_width']}px;
        }}

        QSplitter::handle:vertical {{
            height: {SIZES['border_width']}px;
        }}

        /* 메뉴바 스타일 */
        QMenuBar {{
            background-color: {COLORS['surface']};
            border-bottom: {SIZES['border_width']}px solid {COLORS['border']};
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: {SIZES['spacing_medium']}px {SIZES['spacing_large']}px;
        }}

        QMenuBar::item:selected {{
            background-color: {COLORS['hover']};
        }}

        /* 메뉴 스타일 */
        QMenu {{
            background-color: {COLORS['surface']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            padding: {SIZES['spacing_small']}px 0px;
        }}

        QMenu::item {{
            padding: {SIZES['spacing_medium']}px {SIZES['spacing_xlarge']}px;
            padding-right: {SIZES['spacing_xxlarge']}px;
        }}

        QMenu::item:selected {{
            background-color: {COLORS['hover']};
        }}

        QMenu::separator {{
            height: {SIZES['border_width']}px;
            background-color: {COLORS['border']};
            margin: {SIZES['spacing_small']}px 0px;
        }}

        /* 상태바 스타일 */
        QStatusBar {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border-top: {SIZES['border_width']}px solid {COLORS['border']};
        }}

        QStatusBar QLabel {{
            padding: {SIZES['spacing_medium']}px;
        }}

        /* 툴바 스타일 */
        QToolBar {{
            background-color: {COLORS['surface']};
            border-bottom: {SIZES['border_width']}px solid {COLORS['border']};
            spacing: {SIZES['spacing_small']}px;
        }}

        QToolBar::separator {{
            background-color: {COLORS['border']};
            width: {SIZES['border_width']}px;
            margin: 0px {SIZES['spacing_small']}px;
        }}

        /* 도구 팁 스타일 */
        QToolTip {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            padding: {SIZES['spacing_medium']}px;
            border-radius: {SIZES['border_radius']}px;
        }}
    """

    # 모든 컴포넌트 스타일 통합
    return f"""
        {base_style}
        {get_button_style()}
        {get_dialog_style()}
        {get_table_style()}
        {get_tree_style()}
        {get_input_style()}
    """
