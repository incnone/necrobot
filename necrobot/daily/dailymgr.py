import datetime

# from necrobot.util import console
from necrobot.database import userdb
from necrobot.daily import dailytype

from necrobot.util.singleton import Singleton
from necrobot.botbase.necrobot import Necrobot
from necrobot.daily.daily import DATE_ZERO, Daily
from necrobot.daily.dailytype import DailyType
from necrobot.user.userprefs import UserPrefs
from necrobot.config import Config


class DailyMgr(object, metaclass=Singleton):
    def __init__(self):
        self._leaderboard_channel = self.necrobot.find_channel(Config.DAILY_LEADERBOARDS_CHANNEL_NAME)
        self._cadence_daily = Daily(self, DailyType.cadence)
        self._rotating_daily = Daily(self, DailyType.rotating)

    async def initialize(self):
        pass

    async def refresh(self):
        pass

    async def close(self):
        self._cadence_daily.close()
        self._rotating_daily.close()

    @property
    def client(self):
        return self.necrobot.client

    @property
    def necrobot(self):
        return Necrobot()

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
        for member_id in userdb.get_all_ids_matching_prefs(auto_pref):
            member = self.necrobot.find_member(discord_id=member_id)
            if member is not None:
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