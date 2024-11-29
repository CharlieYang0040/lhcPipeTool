"""설정 관리 서비스"""
from ..utils.logger import setup_logger

class SettingsService:
    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.logger = setup_logger(__name__)
        
    def get_setting(self, key):
        """설정값 조회"""
        try:
            cursor = self.db_connector.cursor()
            cursor.execute(
                "SELECT SETTING_VALUE FROM settings WHERE SETTING_KEY = ?",
                (key,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"설정 조회 실패 ({key}): {str(e)}")
            return None
            
    def set_setting(self, key, value):
        """설정값 저장/수정"""
        try:
            cursor = self.db_connector.cursor()
            cursor.execute("""
                UPDATE OR INSERT INTO settings (SETTING_KEY, SETTING_VALUE, UPDATED_AT)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                MATCHING (SETTING_KEY)
            """, (key, value))
            self.db_connector.commit()
            return True
        except Exception as e:
            self.logger.error(f"설정 저장 실패 ({key}): {str(e)}")
            return False
            
    def get_all_settings(self):
        """모든 설정값 조회"""
        try:
            cursor = self.db_connector.cursor()
            cursor.execute("SELECT SETTING_KEY, SETTING_VALUE FROM settings")
            return dict(cursor.fetchall())
        except Exception as e:
            self.logger.error(f"전체 설정 조회 실패: {str(e)}")
            return {}
