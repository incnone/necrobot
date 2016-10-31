from enum import Enum
import asyncio
import datetime

from . import dailytype
from ..race import racetime
from ..util import level, seedgen
from ..util.config import Config

DATE_ZERO = datetime.date(2016, 1, 1)


class DailyUserStatus(Enum):
    unregistered = 0
    registered = 1
    submitted = 2
    closed = 3


def daily_to_date(daily_number):
    return DATE_ZERO + datetime.timedelta(days=daily_number)


def daily_to_datestr(daily_number):
    return daily_to_date(daily_number).strftime("%d %B %Y")


def daily_to_shortstr(daily_number):
    return daily_to_date(daily_number).strftime("%d %b")


class Daily(object):
    def __init__(self, daily_manager, daily_type):
        self._daily_manager = daily_manager
        self._daily_type = daily_type
        asyncio.ensure_future(self._daily_update())

    @property
    def daily_type(self):
        return self._daily_type

    @property
    def necrobot(self):
        return self._daily_manager.necrobot

    @property
    def necrodb(self):
        return self.necrobot.necrodb

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
        return (utc_now.time().hour * 60) + utc_now.time().minute <= Config.DAILY_GRACE_PERIOD

    # Returns a string giving the remaining time in the grace period
    @property
    def daily_grace_timestr(self):
        utc_now = datetime.datetime.utcnow()
        return self._format_as_timestr(0, Config.DAILY_GRACE_PERIOD - utc_now.hour * 60 - utc_now.minute)

    # Returns a string giving the time until the next daily
    @property
    def next_daily_timestr(self):
        utc_now = datetime.datetime.utcnow()
        return self._format_as_timestr(23 - utc_now.hour, 60 - utc_now.minute)

    # Returns a string giving the time until the current daily closes
    @property
    def daily_close_timestr(self):
        utc_now = datetime.datetime.utcnow()
        return self._format_as_timestr(24 - utc_now.hour, 60 - utc_now.minute)

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
            daily_to_datestr(daily_number))

    # Return the text for the daily with the given daily number
    def leaderboard_text(self, daily_number, display_seed=False):
        text = "``` \n"
        text += self.leaderboard_header(daily_number) + '\n'

        params = (daily_number, self.daily_type.value)

        if display_seed:
            for row in self.necrodb.get_daily_seed(params):
                text += "Seed: {}\n".format(row[0])
                break

        no_entries = True
        rank = int(0)

        prior_result = ''   # detect and handle ties
        rank_to_display = int(1)

        for row in self.necrodb.get_daily_times(params):
            name = row[0]
            lv = row[1]
            time = row[2]
            if lv == 18:
                result_string = racetime.to_str(time)
            elif lv == -1:
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
        params = (user_id, daily_number, self.daily_type.value)
        return self.necrodb.has_submitted_daily(params)

    # True if the given user has registered for the given daily
    # DB_acc
    def has_registered(self, daily_number, user_id):
        params = (user_id, daily_number, self.daily_type.value)
        return self.necrodb.has_registered_daily(params)

    # Attempts to register the given user for the given daily
    # DB_acc
    def register(self, daily_number, user_id):
        if self.has_registered(daily_number, user_id):
            return False
        else:
            params = (user_id, daily_number, self.daily_type.value, -1, -1)
            self.necrodb.register_daily(params)
            return True

    # Returns the most recent daily for which the user is registered (or 0 if no such)
    # DB_acc
    def registered_daily(self, user_id):
        params = (user_id, self.daily_type.value)
        for row in self.necrodb.registered_daily(params):
            return row[0]
        return 0

    # Returns the most recent daily for which the user has submitted (or 0 if no such)
    # DB_acc
    def submitted_daily(self, user_id):
        params = (user_id, self.daily_type.value,)
        for row in self.necrodb.submitted_daily(params):
            if row[1] != -1:
                return row[0]
        return 0

    # Attempt to parse args as a valid daily submission, and submits for the daily if sucessful.
    # Returns a string whose content confirms parse, or the empty string if parse fails.
    def parse_submission(self, daily_number, user, args):
        lv = -1
        time = -1
        ret_str = ''
        if len(args) > 0:
            if args[0] == 'death':
                if len(args) == 2:
                    lv = level.from_str(args[1])
                    if not lv == -1:
                        ret_str = 'died on {}'.format(args[1])
                else:
                    lv = 0
                    ret_str = 'died'
            else:
                time = racetime.from_str(args[0])
                if not time == -1:
                    lv = 18
                    ret_str = 'finished in {}'.format(racetime.to_str(time))

        if not lv == -1:    # parse succeeded
            self.submit_to_daily(daily_number, user, lv, time)
            return ret_str
        else:
            return ''

    # Submit a run to the given daily number
    def submit_to_daily(self, daily_number, user, lv, time):
        params = (user.id, daily_number, self.daily_type.value, lv, time,)
        self.necrodb.register_daily(params)

    # Delete a run from the daily
    def delete_from_daily(self, daily_number, user):
        params = (-1, user.id, daily_number, self.daily_type.value)
        self.necrodb.delete_from_daily(params)

    # Return the seed for the given daily number. Create seed if it doesn't already exist.
    def get_seed(self, daily_number):
        params = (daily_number, self.daily_type.value)

        for row in self.necrodb.get_daily_seed(params):
            return row[0]

        # if we made it here, there was no entry in the table, so make one
        today_seed = seedgen.get_new_seed()
        values = (daily_number, self.daily_type.value, today_seed, 0,)
        self.necrodb.create_daily(values)
        return today_seed

    # Registers the given Message ID in the database for the given daily number
    def register_message(self, daily_number, message_id):
        params = (daily_number, self.daily_type.value)
        for _ in self.necrodb.get_daily_seed(params):
            # if here, there was an entry in the table, so we will update it
            values = (message_id, daily_number, self.daily_type.value)
            self.necrodb.update_daily(values)
            return

        # else, there was no entry, so make one
        today_seed = seedgen.get_new_seed()
        values = (daily_number, self.daily_type.value, today_seed, message_id,)
        self.necrodb.create_daily(values)

    # Returns the Discord Message ID for the leaderboard entry for the given daily number
    def get_message_id(self, daily_number):
        params = (daily_number, self.daily_type.value)
        for row in self.necrodb.get_daily_message_id(params):
            return int(row[0])
        return None

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

    # Formats the given hours, minutes into a string
    @staticmethod
    def _format_as_timestr(hours, minutes):
        while minutes >= 60:
            minutes -= 60
            hours += 1

        if minutes == 0 and hours == 0:
            return 'under a minute'
        else:
            min_str = 'minute' if minutes == 1 else 'minutes'
            hr_str = 'hour' if hours == 1 else 'hours'
            return '{0} {1}, {2} {3}'.format(hours, hr_str, minutes, min_str)
