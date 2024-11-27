"""테이블 스타일 정의"""
from ..base import COLORS, SIZES, FONTS

def get_table_style():
    return f"""
        /* 기본 테이블 스타일 */
        QTableWidget {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            gridline-color: {COLORS['border']};
            border: none;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        /* 테이블 헤더 스타일 */
        QHeaderView::section {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            padding: {SIZES['spacing_medium']}px;
            border: none;
            border-right: {SIZES['border_width']}px solid {COLORS['border']};
            border-bottom: {SIZES['border_width']}px solid {COLORS['border']};
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
            font-weight: {FONTS['weight_medium']};
        }}

        /* 코너 위젯 스타일 수정 */
        QTableCornerButton::section {{
            background-color: {COLORS['surface']};
            border: none;
            border-bottom: {SIZES['border_width']}px solid {COLORS['border']};
            border-right: {SIZES['border_width']}px solid {COLORS['border']};
        }}

        /* 테이블 셀 스타일 */
        QTableWidget::item {{
            padding: {SIZES['spacing_medium']}px;
            border-bottom: {SIZES['border_width']}px solid {COLORS['border']};
        }}

        /* 행 전체 호버 효과 */
        QTableWidget QTableCornerButton::section:hover,
        QTableWidget::item:hover,
        QTableWidget::item:!selected:hover {{
            background-color: {COLORS['hover']};
        }}

        /* 전체 행 선택 스타일 */
        QTableWidget::item:selected {{
            background-color: {COLORS['selected']};
            color: {COLORS['text']};
        }}

        /* 선택된 행의 호버 효과 */
        QTableWidget::item:selected:hover {{
            background-color: {COLORS['selected']};
        }}

        /* 테이블 스크롤바 스타일 */
        QTableWidget QScrollBar:vertical {{
            background-color: {COLORS['background']};
            width: {SIZES['spacing_medium']}px;
            margin: 0;
        }}

        QTableWidget QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: {SIZES['border_radius_small']}px;
            min-height: 20px;
        }}

        QTableWidget QScrollBar::add-line:vertical,
        QTableWidget QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}

        QTableWidget QScrollBar::add-page:vertical,
        QTableWidget QScrollBar::sub-page:vertical {{
            background: none;
        }}

        QTableWidget QScrollBar:horizontal {{
            background-color: {COLORS['background']};
            height: {SIZES['spacing_medium']}px;
            margin: 0;
        }}

        QTableWidget QScrollBar::handle:horizontal {{
            background-color: {COLORS['border']};
            border-radius: {SIZES['border_radius_small']}px;
            min-width: 20px;
        }}

        QTableWidget QScrollBar::add-line:horizontal,
        QTableWidget QScrollBar::sub-line:horizontal {{
            width: 0;
            background: none;
        }}

        QTableWidget QScrollBar::add-page:horizontal,
        QTableWidget QScrollBar::sub-page:horizontal {{
            background: none;
        }}

        /* 빈 테이블 메시지 스타일 */
        QTableWidget QLabel {{
            color: {COLORS['text_secondary']};
            font-size: {SIZES['font_size']}px;
        }}

        /* 정렬 표시자 스타일 */
        QHeaderView::down-arrow {{
            image: url(resources/icons/ue-arrow-down.svg);
            width: {SIZES['icon_size_small']}px;
            height: {SIZES['icon_size_small']}px;
            margin-left: {SIZES['spacing_small']}px;
        }}

        QHeaderView::up-arrow {{
            image: url(resources/icons/ue-arrow-up.svg);
            width: {SIZES['icon_size_small']}px;
            height: {SIZES['icon_size_small']}px;
            margin-left: {SIZES['spacing_small']}px;
        }}

        /* 선택 시 점선 테두리 제거 */
        QTableWidget::item:focus {{
            border: none;
            outline: none;
        }}

        QTableWidget:focus {{
            outline: none;
        }}
    """
