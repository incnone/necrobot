import datetime
import logging
from . import dailytype
from .dailytype import DailyType
from .daily import DATE_ZERO
from .daily import Daily
from ..user.userprefs import UserPrefs
from ..util.config import Config


class DailyManager(object):
    def __init__(self, necrobot):
        logging.getLogger('discord').info('Initializing new DailyManager object.')
        self.necrobot = necrobot
        self._leaderboard_channel = self.necrobot.find_channel(Config.DAILY_LEADERBOARDS_CHANNEL_NAME)
        self._cadence_daily = Daily(self, DailyType.cadence)
        self._rotating_daily = Daily(self, DailyType.rotating)

    def refresh(self):
        pass

    def close(self):
        self._cadence_daily.close()
        self._rotating_daily.close()

    @property
    def client(self):
        return self.necrobot.client

    # Return the number for today's daily (days since DATE_ZERO)
    @property
    def today_number(self):
        return (self.today_date - DATE_ZERO).days

    # Return the date for today's daily (as a datetime.datetime)
    @property
    def today_date(self):
        return datetime.datetime.utcnow().date()

    def daily(self, daily_type):
        if daily_type == DailyType.cadence:
            return self._cadence_daily
        elif daily_type == DailyType.rotating:
            return self._rotating_daily

    # Do whatever UI things need to be done when a new daily happens
    async def on_new_daily(self, daily):
        # Make the leaderboard message
        text = daily.leaderboard_text(self.today_number, display_seed=False)
        msg = await self.client.send_message(self._leaderboard_channel, text)
        daily.register_message(self.today_number, msg.id)

        # Update yesterday's leaderboard with the seed
        await self.update_leaderboard(self.today_number - 1, daily.daily_type, display_seed=True)

        # PM users with the daily_alert preference
        auto_pref = UserPrefs()
        auto_pref.daily_alert = True
        for member in self.necrobot.prefs_manager.get_all_matching(auto_pref):
            daily.register(self.today_number, member.id)
            await self.client.send_message(
                member,
                "({0}) Today's {2} speedrun seed: {1}".format(
                    self.today_date.strftime("%d %b"),
                    daily.get_seed(self.today_number),
                    dailytype.character(daily.daily_type, self.today_number)))

    # Update an existing leaderboard message for the given daily number
    async def update_leaderboard(self, daily_number, daily_type, display_seed=False):
        daily = self.daily(daily_type)
        msg_id = daily.get_message_id(daily_number)

        # If no message, make one
        if not msg_id:
            text = daily.leaderboard_text(daily_number, display_seed)
            msg = await self.client.send_message(self._leaderboard_channel, text)
            daily.register_message(daily_number, msg.id)
        else:
            async for msg in self.client.logs_from(self._leaderboard_channel, limit=10):
                if int(msg.id) == msg_id:
                    await self.client.edit_message(msg, daily.leaderboard_text(daily_number, display_seed))
