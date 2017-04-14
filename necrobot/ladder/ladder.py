class Ladder(object):
    def __init__(self, necrobot):
        self.necrobot = necrobot

    def refresh(self):
        pass

    def close(self):
        pass

    @property
    def client(self):
        return self.necrobot.client
