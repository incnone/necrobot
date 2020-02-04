class CondorEvent(object):
    def __init__(self, schema_name, event_name, deadline_str):
        self.schema_name = schema_name
        self.event_name = event_name
        self.deadline_str = deadline_str
