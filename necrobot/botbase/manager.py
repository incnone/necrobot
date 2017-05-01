"""Abstract base class"""


class Manager(object):
    async def initialize(self):
        pass

    async def refresh(self):
        pass

    async def close(self):
        pass

    def on_botchannel_create(self, channel, bot_channel):
        pass
