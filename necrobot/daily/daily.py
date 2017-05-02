import asyncio
import datetime
import discord
from enum import Enum

from necrobot.botbase import server
from necrobot.database import dailydb, userdb
from necrobot.daily import dailytype
from necrobot.util import level, seedgen, racetime
from necrobot.user import userlib

from necrobot.config import Config
from necrobot.daily.dailytype import DailyType
from necrobot.botbase.necrobot import Necrobot
from necrobot.user.userprefs import UserPrefs
from necrobot.util import timestr

DATE_ZERO = datetime.date(2016, 1, 1)


class DailyUserStatus(Enum):
    unregistered = 0
    registered = 1
    submitted = 2
    closed = 3


class Daily(object):
    """
    Represents a kind of speedrun daily, e.g. the Cadence daily, or the Rotating-char daily. (Is not anchored to
    a particular day.)
    """

    @staticmethod
    def daily_to_date(daily_number: int) -> datetime.date:
        return DATE_ZERO + datetime.timedelta(days=daily_number)

    @staticmethod
    def daily_to_datestr(daily_number: int) -> str:
        return Daily.daily_to_date(daily_number).strftime("%d %B %Y")

    @staticmethod
    def daily_to_shortstr(daily_number: int) -> str:
        return Daily.daily_to_date(daily_number).strftime("%d %b")

    def __init__(self, daily_type: DailyType):
        self._daily_type = daily_type
        self._daily_update_future = asyncio.ensure_future(self._daily_update())
        self._leaderboard_channel = server.find_channel(channel_name=Config.DAILY_LEADERBOARDS_CHANNEL_NAME)

    def close(self):
        self._daily_update_future.cancel()

    @property
    def client(self) -> discord.Client:
        return server.client

    @property
    def daily_type(self) -> DailyType:
        """The type of this Daily"""
        return self._daily_type

    @property
    def necrobot(self):
        return Necrobot()

    @property
    def today_number(self) -> int:
        """The number for today's daily (days since DATE_ZERO)"""
        return (self.today_date - DATE_ZERO).days

    @property
    def today_date(self) -> datetime.date:
        """The date for today's daily"""
        return datetime.datetime.utcnow().date()

    @property
    def time_until_next(self) -> datetime.timedelta:
        """The time until the next daily begins"""
        now = datetime.datetime.utcnow()
        tomorrow = datetime.datetime.replace(now + datetime.timedelta(days=1), hour=0, minute=0, second=0)
        return tomorrow - now

    # Returns whether we're in the grace period between daily rollouts
    @property
    def within_grace_period(self) -> bool:
        """Whether we're in the grace period after a new daily begins, but before the old has stopped accepting
        submissions"""
        utc_now = datetime.datetime.utcnow()
        utc_rollover = utc_now.replace(hour=0, minute=0, second=0)
        return utc_now - utc_rollover <= Config.DAILY_GRACE_PERIOD

    @property
    def daily_grace_timestr(self) -> str:
        """The remaining time in the grace period"""
        utc_now = datetime.datetime.utcnow()
        utc_grace_end = utc_now.replace(hour=0, minute=0, second=0) + Config.DAILY_GRACE_PERIOD
        return self._format_as_timestr(utc_grace_end - utc_now)

    @property
    def next_daily_timestr(self) -> str:
        """Time until the next daily"""
        return self._format_as_timestr(self.time_until_next)

    @property
    def daily_close_timestr(self) -> str:
        """Time until the current daily closes"""
        utc_now = datetime.datetime.utcnow()
        utc_tomorrow = (utc_now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        return self._format_as_timestr(utc_tomorrow - utc_now)

    @property
    def daily_time_info_str(self) -> str:
        """Current daily's date and time until next daily"""
        date_str = datetime.datetime.utcnow().strftime("%B %d")
        if self.within_grace_period:
            return 'The {0} daily is currently active. Yesterday\'s daily is still open for submissions, ' \
                   'but will close in {1}.'.format(date_str, self.daily_grace_timestr)
        else:
            return 'The {0} daily is currently active. The next daily will become available in {1}. Today\'s ' \
                   'daily will close in {2}.'.format(date_str, self.next_daily_timestr, self.daily_close_timestr)

    def is_open(self, daily_number: int) -> bool:
        """True if the given daily is still accepting submissions"""
        today = self.today_number
        return today == daily_number or (today == int(daily_number)+1 and self.within_grace_period)

    def leaderboard_header(self, daily_number: int) -> str:
        """The header for the leaderboard"""
        return "{0} -- {1}".format(
            dailytype.leaderboard_header(self.daily_type, daily_number),
            self.daily_to_datestr(daily_number))

    async def leaderboard_text(self, daily_number: int, display_seed=False):
        """The text (results) for the leaderboard"""
        text = "``` \n"
        text += self.leaderboard_header(daily_number) + '\n'

        if display_seed:
            for row in await dailydb.get_daily_seed(daily_id=daily_number, daily_type=self.daily_type.value):
                text += "Seed: {}\n".format(row[0])
                break

        no_entries = True
        rank = int(0)

        prior_result = ''   # detect and handle ties
        rank_to_display = int(1)
        reverse_levelsort = dailytype.character(daily_type=self.daily_type, daily_number=daily_number) == 'Aria'
        daily_times = sorted(
                await dailydb.get_daily_times(daily_id=daily_number, daily_type=self.daily_type.value),
                key=lambda x: level.level_sortval(int(x[1]), reverse=reverse_levelsort),
                reverse=True)

        for row in daily_times:
            name = row[0]
            lv = row[1]
            time = row[2]
            if lv == level.LEVEL_FINISHED:
                result_string = racetime.to_str(time)
            elif lv == level.LEVEL_NOS:
                continue
            else:
                result_string = level.to_str(lv)
                if result_string == '':
                    result_string = "death"
                else:
                    result_string = "death ({0})".format(result_string)

            rank += 1
            no_entries = False

            # update the rank only if we've gotten a different result than the last entrant
            if result_string != prior_result:   # kinda hacky to use a string comparison here, but works
                rank_to_display = rank

            prior_result = result_string

            text += '{0: >3}. {1: <24} {2}\n'.format(rank_to_display, name, result_string)

        if no_entries:
            text += 'No entries yet.\n'

        text += '```'
        return text

    async def has_submitted(self, daily_number: int, user_id: int) -> bool:
        """True if the given user has submitted for the given daily"""
        return await dailydb.has_submitted_daily(
            user_id=user_id,
            daily_id=daily_number,
            daily_type=self.daily_type.value)

    async def has_registered(self, daily_number: int, user_id: int) -> bool:
        """True if the given user has registered for the given daily"""
        return await dailydb.has_registered_daily(
            user_id=user_id,
            daily_id=daily_number,
            daily_type=self.daily_type.value)

    async def register(self, daily_number: int, user_id: int) -> bool:
        """Attempts to register the given user for the given daily
        
        Returns
        -------
        bool
            True if the registration was successful
        """
        if await self.has_registered(daily_number, user_id):
            return False
        else:
            user = await userlib.get_user(user_id=user_id, register=True)

            await dailydb.register_daily(
                user_id=user.user_id,
                daily_id=daily_number,
                daily_type=self.daily_type.value)
            return True

    async def registered_daily(self, user_id: int) -> int:
        """Returns the most recent daily for which the user is registered (or 0 if no such)"""
        return await dailydb.registered_daily(user_id=user_id, daily_type=self.daily_type.value)

    async def submitted_daily(self, user_id: int) -> int:
        """Returns the most recent daily for which the user has submitted (or 0 if no such)"""
        return await dailydb.submitted_daily(user_id=user_id, daily_type=self.daily_type.value)

    async def parse_submission(self, daily_number: int, user_id: int, args: list) -> str:
        """Attempt to parse args as a valid daily submission, and submits for the daily if sucessful.

        Returns
        -------
            A string whose content confirms parse, or the empty string if parse fails.
        """
        lv = level.LEVEL_NOS
        time = -1
        ret_str = ''
        if len(args) > 0:
            if args[0] == 'death':
                if len(args) == 2:
                    lv = level.from_str(args[1])
                    if not lv == level.LEVEL_NOS:
                        ret_str = 'died on {}'.format(args[1])
                else:
                    lv = level.LEVEL_UNKNOWN_DEATH
                    ret_str = 'died'
            else:
                time = racetime.from_str(args[0])
                if not time == -1:
                    lv = level.LEVEL_FINISHED
                    ret_str = 'finished in {}'.format(racetime.to_str(time))

        if not lv == level.LEVEL_NOS:    # parse succeeded
            await self.submit_to_daily(daily_number, user_id, lv, time)
            return ret_str
        else:
            return ''

    async def submit_to_daily(self, daily_number: int, user_id: int, lv: int, time: int) -> None:
        """Submit a run to the given daily number"""
        await dailydb.register_daily(
            user_id=user_id,
            daily_id=daily_number,
            daily_type=self.daily_type.value,
            level=lv,
            time=time)

    async def delete_from_daily(self, daily_number: int, user_id: int) -> None:
        """Delete a run from the daily"""
        await dailydb.delete_from_daily(
            user_id=user_id,
            daily_id=daily_number,
            daily_type=self.daily_type.value)

    async def get_seed(self, daily_number: int) -> int:
        """Return the seed for the given daily number. (Creates seed if it doesn't already exist.)"""
        for row in await dailydb.get_daily_seed(daily_id=daily_number, daily_type=self.daily_type.value):
            return row[0]

        # if we made it here, there was no entry in the table, so make one
        today_seed = seedgen.get_new_seed()
        await dailydb.create_daily(
            daily_id=daily_number,
            daily_type=self.daily_type.value,
            seed=today_seed)
        return today_seed

    async def register_message(self, daily_number: int, message_id: int) -> None:
        """Registers the given Message ID in the database for the given daily number"""
        for _ in await dailydb.get_daily_seed(daily_id=daily_number, daily_type=self.daily_type.value):
            # if here, there was an entry in the table, so we will update it
            await dailydb.register_daily_message(
                daily_id=daily_number,
                daily_type=self.daily_type.value,
                message_id=message_id)
            return

        # else, there was no entry, so make a new daily
        today_seed = seedgen.get_new_seed()
        await dailydb.create_daily(
            daily_id=daily_number,
            daily_type=self.daily_type.value,
            seed=today_seed,
            message_id=message_id)

    async def get_message_id(self, daily_number) -> int:
        """Returns the Discord Message ID for the leaderboard entry for the given daily number"""
        return await dailydb.get_daily_message_id(daily_id=daily_number, daily_type=self.daily_type.value)

    async def user_status(self, user_id: int, daily_number: int) -> DailyUserStatus:
        """Return a DailyUserStatus corresponding to the status of the current daily for the given user"""
        if not self.is_open(daily_number):
            return DailyUserStatus.closed
        elif await self.has_submitted(daily_number, user_id):
            return DailyUserStatus.submitted
        elif await self.has_registered(daily_number, user_id):
            return DailyUserStatus.registered
        else:
            return DailyUserStatus.unregistered

    async def update_leaderboard(self, daily_number: int, display_seed: bool = False) -> None:
        """Update an existing leaderboard message for the given daily number"""
        msg_id = await self.get_message_id(daily_number)

        # If no message, make one
        if not msg_id:
            text = await self.leaderboard_text(daily_number, display_seed)
            msg = await self.client.send_message(self._leaderboard_channel, text)
            await self.register_message(daily_number, msg.id)
        else:
            async for msg in self.client.logs_from(self._leaderboard_channel, limit=10):
                if int(msg.id) == msg_id:
                    await self.client.edit_message(msg, await self.leaderboard_text(daily_number, display_seed))

    async def on_new_daily(self) -> None:
        """Run when a new daily happens"""
        # Make the leaderboard message
        text = await self.leaderboard_text(self.today_number, display_seed=False)
        msg = await self.client.send_message(self._leaderboard_channel, text)
        await self.register_message(self.today_number, msg.id)

        # Update yesterday's leaderboard with the seed
        await self.update_leaderboard(self.today_number - 1, display_seed=True)

        # PM users with the daily_alert preference
        auto_pref = UserPrefs(daily_alert=True, race_alert=None)
        for member_id in await userdb.get_all_discord_ids_matching_prefs(auto_pref):
            member = server.find_member(discord_id=member_id)
            if member is not None:
                await self.register(self.today_number, member.id)
                await self.client.send_message(
                    member,
                    "({0}) Today's {2} speedrun seed: {1}".format(
                        self.today_date.strftime("%d %b"),
                        await self.get_seed(self.today_number),
                        dailytype.character(self.daily_type, self.today_number)))

    async def _daily_update(self) -> None:
        """Call DailyManager's on_new_daily coroutine when this daily rolls over"""
        while True:
            await asyncio.sleep(self.time_until_next.total_seconds() + 1)  # sleep until next daily
            await self.on_new_daily()
            await asyncio.sleep(120)  # buffer b/c i'm worried for some reason about idk

    @staticmethod
    def _format_as_timestr(td: datetime.timedelta) -> str:
        """Format the given timedelta into a string"""
        if td < datetime.timedelta(minutes=1):
            return 'under a minute'
        else:
            return timestr.timedelta_to_str(td)
