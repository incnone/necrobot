import asyncio
import datetime
from enum import Enum

from necrobot.database import dailydb
from necrobot.race import racetime
from necrobot.daily import dailytype
from necrobot.util import level, seedgen
from necrobot.config import Config

DATE_ZERO = datetime.date(2016, 1, 1)


class DailyUserStatus(Enum):
    unregistered = 0
    registered = 1
    submitted = 2
    closed = 3


# noinspection PyTypeChecker
class Daily(object):
    @staticmethod
    def daily_to_date(daily_number):
        return DATE_ZERO + datetime.timedelta(days=daily_number)

    @staticmethod
    def daily_to_datestr(daily_number):
        return Daily.daily_to_date(daily_number).strftime("%d %B %Y")

    @staticmethod
    def daily_to_shortstr(daily_number):
        return Daily.daily_to_date(daily_number).strftime("%d %b")

    def __init__(self, daily_manager, daily_type):
        self._daily_manager = daily_manager
        self._daily_type = daily_type
        self._daily_update_future = asyncio.ensure_future(self._daily_update())

    def close(self):
        self._daily_update_future.cancel()

    @property
    def daily_type(self):
        return self._daily_type

    @property
    def necrobot(self):
        return self._daily_manager.necrobot

    # Return today's daily number
    @property
    def today_number(self):
        return self._daily_manager.today_number

    # Return the date for today's daily (as a datetime.datetime)
    @property
    def today_date(self):
        return self._daily_manager.today_date

    # Return a datetime.timedelta giving the time until the next daily
    @property
    def time_until_next(self):
        now = datetime.datetime.utcnow()
        tomorrow = datetime.datetime.replace(now + datetime.timedelta(days=1), hour=0, minute=0, second=0)
        return tomorrow - now

    # Returns whether we're in the grace period between daily rollouts
    @property
    def within_grace_period(self):
        utc_now = datetime.datetime.utcnow()
        utc_rollover = utc_now.replace(hour=0, minute=0, second=0)
        return utc_now - utc_rollover <= Config.DAILY_GRACE_PERIOD

    # Returns a string giving the remaining time in the grace period
    @property
    def daily_grace_timestr(self):
        utc_now = datetime.datetime.utcnow()
        utc_grace_end = utc_now.replace(hour=0, minute=0, second=0) + Config.DAILY_GRACE_PERIOD
        return self._format_as_timestr(utc_grace_end - utc_now)

    # Returns a string giving the time until the next daily
    @property
    def next_daily_timestr(self):
        return self._format_as_timestr(self.time_until_next)

    # Returns a string giving the time until the current daily closes
    @property
    def daily_close_timestr(self):
        utc_now = datetime.datetime.utcnow()
        utc_tomorrow = (utc_now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        return self._format_as_timestr(utc_tomorrow - utc_now)

    # Returns a string with the current daily's date and time until the next daily.
    @property
    def daily_time_info_str(self):
        date_str = datetime.datetime.utcnow().strftime("%B %d")
        if self.within_grace_period:
            return 'The {0} daily is currently active. Yesterday\'s daily is still open for submissions, ' \
                   'but will close in {1}.'.format(date_str, self.daily_grace_timestr)
        else:
            return 'The {0} daily is currently active. The next daily will become available in {1}. Today\'s ' \
                   'daily will close in {2}.'.format(date_str, self.next_daily_timestr, self.daily_close_timestr)

    # Returns true if the given daily is still open for submissions.
    def is_open(self, daily_number):
        today = self.today_number
        return today == daily_number or (today == int(daily_number)+1 and self.within_grace_period)

    # Returns the header for the daily leaderboard, given the type
    def leaderboard_header(self, daily_number):
        return "{0} -- {1}".format(
            dailytype.leaderboard_header(self.daily_type, daily_number),
            self.daily_to_datestr(daily_number))

    # Return the text for the daily with the given daily number
    def leaderboard_text(self, daily_number, display_seed=False):
        text = "``` \n"
        text += self.leaderboard_header(daily_number) + '\n'

        if display_seed:
            for row in dailydb.get_daily_seed(daily_id=daily_number, daily_type=self.daily_type.value):
                text += "Seed: {}\n".format(row[0])
                break

        no_entries = True
        rank = int(0)

        prior_result = ''   # detect and handle ties
        rank_to_display = int(1)
        reverse_levelsort = dailytype.character(daily_type=self.daily_type, daily_number=daily_number) == 'Aria'
        daily_times = sorted(
                dailydb.get_daily_times(daily_id=daily_number, daily_type=self.daily_type.value),
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

    # True if the given user has submitted for the given daily
    def has_submitted(self, daily_number, user_id):
        return dailydb.has_submitted_daily(
            discord_id=user_id,
            daily_id=daily_number,
            daily_type=self.daily_type.value)

    # True if the given user has registered for the given daily
    # DB_acc
    def has_registered(self, daily_number, user_id):
        return dailydb.has_registered_daily(
            discord_id=user_id,
            daily_id=daily_number,
            daily_type=self.daily_type.value)

    # Attempts to register the given user for the given daily
    # DB_acc
    def register(self, daily_number, user_id):
        if self.has_registered(daily_number, user_id):
            return False
        else:
            dailydb.register_daily(
                discord_id=user_id,
                daily_id=daily_number,
                daily_type=self.daily_type.value)
            return True

    # Returns the most recent daily for which the user is registered (or 0 if no such)
    # DB_acc
    def registered_daily(self, user_id):
        return dailydb.registered_daily(discord_id=user_id, daily_type=self.daily_type.value)

    # Returns the most recent daily for which the user has submitted (or 0 if no such)
    # DB_acc
    def submitted_daily(self, user_id):
        return dailydb.submitted_daily(discord_id=user_id, daily_type=self.daily_type.value)

    # Attempt to parse args as a valid daily submission, and submits for the daily if sucessful.
    # Returns a string whose content confirms parse, or the empty string if parse fails.
    def parse_submission(self, daily_number, user, args):
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
                    ret_str = 'finished in {}'.format(racetime)

        if not lv == level.LEVEL_NOS:    # parse succeeded
            self.submit_to_daily(daily_number, user, lv, time)
            return ret_str
        else:
            return ''

    # Submit a run to the given daily number
    def submit_to_daily(self, daily_number, user, lv, time):
        dailydb.register_daily(
            discord_id=int(user.id),
            daily_id=daily_number,
            daily_type=self.daily_type.value,
            level=lv,
            time=time)

    # Delete a run from the daily
    def delete_from_daily(self, daily_number, user):
        dailydb.delete_from_daily(
            discord_id=int(user.id),
            daily_id=daily_number,
            daily_type=self.daily_type.value)

    # Return the seed for the given daily number. Create seed if it doesn't already exist.
    def get_seed(self, daily_number):
        for row in dailydb.get_daily_seed(daily_id=daily_number, daily_type=self.daily_type.value):
            return row[0]

        # if we made it here, there was no entry in the table, so make one
        today_seed = seedgen.get_new_seed()
        dailydb.create_daily(
            daily_id=daily_number,
            daily_type=self.daily_type.value,
            seed=today_seed)
        return today_seed

    # Registers the given Message ID in the database for the given daily number
    def register_message(self, daily_number, message_id):
        for _ in dailydb.get_daily_seed(daily_id=daily_number, daily_type=self.daily_type.value):
            # if here, there was an entry in the table, so we will update it
            dailydb.register_daily_message(
                daily_id=daily_number,
                daily_type=self.daily_type.value,
                message_id=message_id)
            return

        # else, there was no entry, so make one
        today_seed = seedgen.get_new_seed()
        dailydb.create_daily(
            daily_id=daily_number,
            daily_type=self.daily_type.value,
            seed=today_seed,
            message_id=message_id)

    # Returns the Discord Message ID for the leaderboard entry for the given daily number
    def get_message_id(self, daily_number):
        return dailydb.get_daily_message_id(daily_id=daily_number, daily_type=self.daily_type.value)

    # Return a DailyUserStatus corresponding to the status of the current daily for the given user
    def user_status(self, user_id, daily_number):
        if not self.is_open(daily_number):
            return DailyUserStatus.closed
        elif self.has_submitted(daily_number, user_id):
            return DailyUserStatus.submitted
        elif self.has_registered(daily_number, user_id):
            return DailyUserStatus.registered
        else:
            return DailyUserStatus.unregistered

    # Coroutine running in the background; after it becomes a new daily, will automatically PM out the seeds to
    # users that have that preference.
    async def _daily_update(self):
        while True:
            await asyncio.sleep(self.time_until_next.total_seconds() + 1)  # sleep until next daily
            await self._daily_manager.on_new_daily(self)
            await asyncio.sleep(120)  # buffer b/c i'm worried for some reason about idk

    # Formats the given timedelta into a string
    @staticmethod
    def _format_as_timestr(td: datetime.timedelta):
        seconds = td.total_seconds()
        hours, rem = divmod(seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        if minutes == 0 and hours == 0:
            return 'under a minute'
        else:
            min_str = 'minute' if minutes == 1 else 'minutes'
            hr_str = 'hour' if hours == 1 else 'hours'
            if hours == 0:
                return '{0} {1}'.format(minutes, min_str)
            else:
                return '{0} {1}, {2} {3}'.format(hours, hr_str, minutes, min_str)
