class EventSystem:
    _observers = {}

    @classmethod
    def subscribe(cls, event_name, callback):
        if event_name not in cls._observers:
            cls._observers[event_name] = []
        cls._observers[event_name].append(callback)

    @classmethod
    def notify(cls, event_name, *args, **kwargs):
        if event_name in cls._observers:
            for callback in cls._observers[event_name]:
                callback(*args, **kwargs)