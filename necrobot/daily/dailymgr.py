from necrobot.util.singleton import Singleton
from necrobot.botbase.manager import Manager
from necrobot.daily.daily import Daily
from necrobot.daily.dailytype import DailyType


class DailyMgr(Manager, metaclass=Singleton):
    def __init__(self):
        self._cadence_daily = Daily(DailyType.CADENCE)
        self._rotating_daily = Daily(DailyType.ROTATING)

    async def initialize(self):
        pass

    async def refresh(self):
        pass

    async def close(self):
        self._cadence_daily.close()
        self._rotating_daily.close()

    def on_botchannel_create(self, channel, bot_channel):
        pass

    def daily(self, daily_type: DailyType) -> Daily:
        """The Daily for the given DailyType"""
        if daily_type == DailyType.CADENCE:
            return self._cadence_daily
        elif daily_type == DailyType.ROTATING:
            return self._rotating_daily
