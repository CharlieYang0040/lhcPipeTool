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
        self._current_worker = None
        
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
        
    @property
    def current_worker(self):
        return self._current_worker
        
    @current_worker.setter
    def current_worker(self, worker):
        # worker가 올바른 형식인지 확인
        if isinstance(worker, dict) and 'id' in worker:
            self._current_worker = worker
        else:
            print("Invalid worker format:", worker)  # 로그를 추가하여 디버깅
            raise ValueError("Invalid worker format. Expected a dictionary with an 'id' field.")
