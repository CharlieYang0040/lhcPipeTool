"""스타일 시스템 초기화"""
from .themes.dark import get_dark_theme
from .themes.light import get_light_theme

def get_theme(theme_name='dark'):
    """테마 스타일시트 반환
    
    Args:
        theme_name (str): 테마 이름 ('dark' 또는 'light')
        
    Returns:
        str: 테마 스타일시트
    """
    themes = {
        'dark': get_dark_theme,
        'light': get_light_theme
    }
    
    return themes.get(theme_name, get_dark_theme)()
