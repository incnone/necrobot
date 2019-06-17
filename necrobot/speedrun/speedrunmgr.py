from necrobot.botbase.necroevent import NEDispatch, NecroEvent
from necrobot.botbase.manager import Manager
from necrobot.util import server
from necrobot.util.singleton import Singleton


class SpeedrunMgr(Manager, metaclass=Singleton):
    """Manager object for the CoNDOR Events server"""
    def __init__(self):
        self.gsheet_id = None
        self._client = None
        NEDispatch().subscribe(self)

    async def initialize(self):
        self._client = server.client

    async def refresh(self):
        self._client = server.client

    async def close(self):
        pass

    def on_botchannel_create(self, channel, bot_channel):
        pass

    async def ne_process(self, ev: NecroEvent):
        if ev.event_type == 'set_speedrun_gsheet':
            pass
