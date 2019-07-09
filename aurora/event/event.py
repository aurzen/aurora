from datetime import datetime


class Event:
    pass


class TimeEvent:
    def __init__(self, dt_override: datetime = None):
        self.datetime = dt_override or datetime.utcnow()
