import asyncio
import datetime
import pytz
from necrobot.util import server


DO_AUTOMATCHING = False
AUTOMATCH_WEEKDAY = 4  # Friday (0=Monday, 6=Sunday)
AUTOMATCH_HOUR = 12  # Noon UTC


class Ladder(object):
    def __init__(self):
        self._ladder_automatch_future = asyncio.ensure_future(self._wait_and_automatch())

    def refresh(self):
        pass

    def close(self):
        self._ladder_automatch_future.cancel()

    @property
    def client(self):
        return guild.client

    async def _wait_and_automatch(self):
        if not DO_AUTOMATCHING:
            return

        utcnow_dt = datetime.datetime.utcnow()
        today_date = utcnow_dt.date()
        automatch_date = today_date + datetime.timedelta(days=((AUTOMATCH_WEEKDAY - today_date.weekday()) % 7))
        automatch_dt = pytz.utc.localize(
            datetime.datetime.combine(automatch_date, datetime.time(hour=AUTOMATCH_HOUR)))
        time_until_automatch = automatch_dt - utcnow_dt

        await asyncio.sleep(time_until_automatch)
        await self._make_automatches()

    async def _make_automatches(self):
        pass
