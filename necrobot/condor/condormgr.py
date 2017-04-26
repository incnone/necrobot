from necrobot.botbase.necrobot import Necrobot
from necrobot.necroevent.necroevent import NEDispatch, NecroEvent
from necrobot.util.singleton import Singleton


class CondorMgr(object, metaclass=Singleton):
    """Manager object for the CoNDOR Events server"""
    def __init__(self):
        self._notifications_channel = None
        self._client = None
        NEDispatch().subscribe(self)

    async def initialize(self):
        self._notifications_channel = Necrobot().find_channel('bot_notifications')
        self._client = Necrobot().client

    async def refresh(self):
        self._notifications_channel = Necrobot().find_channel('bot_notifications')
        self._client = Necrobot().client

    async def close(self):
        pass

    async def ne_process(self, ev: NecroEvent):
        if self._notifications_channel is None:
            return

        if ev.event_type == 'notify':
            await self._client.send_message(self._notifications_channel, ev.message)
