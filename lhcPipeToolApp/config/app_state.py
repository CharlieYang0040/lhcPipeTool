class AppState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._current_item_type = None
        self._current_item_id = None
        
    @property
    def current_item_type(self):
        return self._current_item_type
        
    @current_item_type.setter
    def current_item_type(self, value):
        if value not in ["shot", "sequence", "project"]:
            raise ValueError("Invalid item type")
        self._current_item_type = value
        
    @property
    def current_item_id(self):
        return self._current_item_id
        
    @current_item_id.setter
    def current_item_id(self, value):
        self._current_item_id = value