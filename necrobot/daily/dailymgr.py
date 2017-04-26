from necrobot.util.singleton import Singleton
from necrobot.daily.daily import Daily
from necrobot.daily.dailytype import DailyType


class DailyMgr(object, metaclass=Singleton):
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

    def daily(self, daily_type: DailyType) -> Daily:
        """The Daily for the given DailyType"""
        if daily_type == DailyType.CADENCE:
            return self._cadence_daily
        elif daily_type == DailyType.ROTATING:
            return self._rotating_daily
