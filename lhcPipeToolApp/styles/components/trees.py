"""트리 위젯 스타일 정의"""
from ..base import COLORS, SIZES, FONTS

def get_tree_style():
    return f"""
        /* 기본 트리 위젯 스타일 */
        QTreeWidget {{
            background-color: {COLORS['background']};
            border: none;
            outline: none;
            padding: {SIZES['spacing_small']}px;
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
        }}

        /* 트리 아이템 스타일 */
        QTreeWidget::item {{
            color: {COLORS['text']};
            padding: {SIZES['spacing_medium']}px;
            border-radius: {SIZES['border_radius']}px;
        }}

        QTreeWidget::item:hover {{
            background-color: {COLORS['hover']};
        }}

        QTreeWidget::item:selected {{
            background-color: {COLORS['selected']};
        }}

        QTreeWidget::item:selected:active {{
            background-color: {COLORS['selected']};
        }}

        /* 브랜치(확장/축소) 컨트롤 스타일 */
        QTreeWidget::branch {{
            background: transparent;
            padding-left: {SIZES['spacing_medium']}px;
        }}

        QTreeWidget::branch:has-siblings:!adjoins-item {{
            border-image: url(resources/icons/ue-vline.svg) 0;
        }}

        QTreeWidget::branch:has-siblings:adjoins-item {{
            border-image: url(resources/icons/ue-branch-more.svg) 0;
        }}

        QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {{
            border-image: url(resources/icons/ue-branch-end.svg) 0;
        }}

        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {{
            border-image: none;
            image: url(resources/icons/ue-branch-closed.svg);
        }}

        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {{
            border-image: none;
            image: url(resources/icons/ue-branch-open.svg);
        }}

        /* 커스텀 트리 아이템 위젯 스타일 */
        CustomTreeItemWidget {{
            background: transparent;
            outline: none;
            border: none;
        }}

        CustomTreeItemWidget[selected="true"] {{
            background-color: {COLORS['selected']};
        }}

        CustomTreeItemWidget:hover {{
            background-color: {COLORS['hover']};
        }}

        /* 아이템 내부 위젯 스타일 */
        CustomTreeItemWidget QLabel {{
            color: {COLORS['text']};
            font-family: '{FONTS['family']}';
            font-size: {SIZES['font_size']}px;
            background: transparent;
        }}

        CustomTreeItemWidget QLabel#preview_label {{
            background-color: {COLORS['surface']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
        }}

        /* 스크롤바 스타일 */
        QTreeWidget QScrollBar:vertical {{
            background-color: {COLORS['background']};
            width: {SIZES['spacing_medium']}px;
            margin: 0;
        }}

        QTreeWidget QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: {SIZES['border_radius_small']}px;
            min-height: 20px;
        }}

        QTreeWidget QScrollBar::add-line:vertical,
        QTreeWidget QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}

        QTreeWidget QScrollBar::add-page:vertical,
        QTreeWidget QScrollBar::sub-page:vertical {{
            background: none;
        }}

        /* 헤더 스타일 */
        QTreeWidget QHeaderView::section {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            padding: {SIZES['spacing_medium']}px;
            border: none;
            border-right: {SIZES['border_width']}px solid {COLORS['border']};
            font-weight: {FONTS['weight_medium']};
        }}

        /* 트리 위젯 툴팁 스타일 */
        QTreeWidget QToolTip {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: {SIZES['border_width']}px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            padding: {SIZES['spacing_medium']}px;
        }}
    """
