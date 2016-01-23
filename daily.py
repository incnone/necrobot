#TODO: probably need to deal with async DB access

import asyncio
import datetime
import discord
import sqlite3

import config
import level
import racetime
import seedgen
import userprefs

DATE_ZERO = datetime.date(2016, 1, 1)

def daily_to_date(daily_number):
    return (DATE_ZERO + datetime.timedelta(days=daily_number))

def daily_to_datestr(daily_number):
    return daily_to_date(daily_number).strftime("%d %B %Y")

def daily_to_shortstr(daily_number):
    return daily_to_date(daily_number).strftime("%d %b")

# Formats the given hours, minutes into a string
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

class DailyManager(object):

    def __init__(self, client, db_connection, prefs_manager=None):
        self._client = client
        self._db_conn = db_connection
        self._prefs_manager = prefs_manager
        self._leaderboard_channel = None
        self._spoilerchat_channel = None
        self._last_daily_number = None # The result of self.today_number on the most recent call of auto_pm_seeds()

        for channel in self._client.get_all_channels():
            if channel.name == config.DAILY_LEADERBOARDS_CHANNEL_NAME:
                self._leaderboard_channel = channel

        for channel in self._client.get_all_channels():
            if channel.name == config.DAILY_SPOILERCHAT_CHANNEL_NAME:
                self._spoilerchat_channel = channel        

        asyncio.ensure_future(self._auto_pm_seeds())

    # Coroutine running in the background; after it becomes a new daily, will automatically PM out the seeds to
    # users that have that preference.
    @asyncio.coroutine
    def _auto_pm_seeds():
        self._last_daily_number = self.today_number()
        while True:
            asyncio.sleep(120) #check every two minutes
            today = self.today_number()
            if today != self._last_daily_number:
                # Send the PM's
                auto_pref = userprefs.UserPrefs()
                auto_pref.deliver_seed = True
                today_seed = self.get_seed(today)
                for member in self._prefs_manager.get_all_matching(auto_pref):
                    if self.has_submitted(self._last_daily_number, member.id):
                        self.register(today, member.id)
                        asyncio.ensure_future(self._client.send_message(member, "({0}) Today's Cadence speedrun seed: {1}".format(today_date.strftime("%d %b"), today_seed)))
                    else:
                        asyncio.ensure_future(self._client.send_message(member, "You have not yet submitted for yesterday's daily, so I am not yet sending you today's seed. " \
                                                                                "When you want today's seed, please call `.dailyseed` in the main channel or via PM."))                        

                # Update the last daily number
                self._last_daily_number = self.today_number()


    # Returns a string with the current daily's date and time until the next daily.
    def daily_time_info_str(self):
        date_str = datetime.datetime.utcnow().strftime("%B %d")
        if self.within_grace_period():
            return 'The {0} daily is currently active. Yesterday\'s daily is still open for submissions, but will close in {1}.'.format(date_str, self.daily_grace_timestr())
        else:
            return 'The {0} daily is currently active. The next daily will become available in {1}. Today\'s daily will close in {2}.'.format(date_str, self.next_daily_timestr(), self.daily_close_timestr())

    # Return today's daily number
    def today_number(self):
        utc_today = datetime.datetime.utcnow().date()
        return (utc_today - DATE_ZERO).days

    # Returns whether we're in the grace period between daily rollouts
    def within_grace_period(self):
        utc_now = datetime.datetime.utcnow()
        return (utc_now.time().hour * 60) + utc_now.time().minute <= config.DAILY_GRACE_PERIOD

    # Returns a string giving the remaining time in the grace period
    def daily_grace_timestr(self):
        utc_now = datetime.datetime.utcnow()
        return _format_as_timestr(0, config.DAILY_GRACE_PERIOD - utc_now.hour*60 - utc_now.minute)

    # Returns a string giving the time until the next daily
    def next_daily_timestr(self):
        utc_now = datetime.datetime.utcnow()
        date_str = utc_now.strftime("%B %d")
        return _format_as_timestr(23 - utc_now.hour, 60 - utc_now.minute)  

    # Returns a string giving the time until the current daily closes
    def daily_close_timestr(self):
        utc_now = datetime.datetime.utcnow()
        date_str = utc_now.strftime("%B %d")
        return _format_as_timestr(24 - utc_now.hour, 60 - utc_now.minute)  
        
    # Returns true if the given daily is still open for submissions.
    def is_open(self, daily_number):
        today = self.today_number();
        return today == daily_number or (today == int(daily_number)+1 and self.within_grace_period())

    # Return the text for the daily with the given daily number #DB_acc
    def leaderboard_text(self, daily_number, display_seed=False):
        date_str = daily_to_datestr(daily_number)
        text = "``` \nCadence Speedrun Daily -- {0}\n".format(date_str)

        db_cursor = self._db_conn.cursor()
        params = (daily_number,)

        if display_seed:
            db_cursor.execute("SELECT seed FROM daily_seeds WHERE date=?", params)
            for row in db_cursor:
                text += "Seed: {}\n".format(row[0])
                break
        
        db_cursor.execute("SELECT * FROM daily_races WHERE date=? ORDER BY level DESC, time ASC", params)

        no_entries = True
        rank = int(0)
        
        prior_result = ''   #detect and handle ties
        rank_to_display = int(1)

        for row in db_cursor:
            rank += 1
            no_entries = False
            name = row[1]
            lv = row[3]
            time = row[4]
            result_string = ''
            if lv == 18:
                result_string = racetime.to_str(time)
            else:
                result_string = level.to_str(lv)
                if result_string == '':
                    result_string = "death"
                else:
                    result_string = "death ({0})".format(result_string)

            # update the rank only if we've gotten a different result than the last entrant
            if not result_string == prior_result: #kinda hacky to use a string comparison here, but works for the moment
                rank_to_display = rank

            prior_result = result_string
            
            text += '{0: >3}. {1: <24} {2}\n'.format(rank_to_display, name, result_string)

        if no_entries:
            text += 'No entries yet.\n'

        text += '```'
        return text
    
    # True if the given user has submitted for the given daily #DB_acc          
    def has_submitted(self, daily_number, user_id):
        db_cursor = self._db_conn.cursor()
        params = (daily_number, user_id,)
        db_cursor.execute("SELECT * FROM daily_races WHERE date=? AND playerid=?", params)
        for row in db_cursor:
            return True
        return False

    # True if the given user has registered for the given daily #DB_acc
    def has_registered(self, daily_number, user_id):
        db_cursor = self._db_conn.cursor()
        params = (user_id, daily_number,)
        db_cursor.execute("SELECT * FROM last_daily WHERE playerid=? AND date=?", params)
        for row in db_cursor:
            return True
        return False

    # Attempts to register the given user for the given daily #DB_acc
    def register(self, daily_number, user_id):
        if self.has_registered(daily_number, user_id):
            return False
        else:
            db_cursor = self._db_conn.cursor()
            params = (user_id, daily_number,)
            db_cursor.execute("INSERT INTO last_daily VALUES (?,?)", params)
            self._db_conn.commit()
            return True

    # Returns the most recent daily for which the user is registered (or 0 if no such) #DB_acc
    def registered_daily(self, user_id):
        db_cursor = self._db_conn.cursor()
        params = (user_id,)
        db_cursor.execute("SELECT date FROM last_daily WHERE playerid=? ORDER BY date DESC", params)
        for row in db_cursor:
            return row[0]
        return 0    

    # Returns the most recent daily for which the user has submitted (or 0 if no such) #DB_acc
    def submitted_daily(self, user_id):
        db_cursor = self._db_conn.cursor()
        params = (user_id,)
        db_cursor.execute("SELECT date FROM daily_races WHERE playerid=? ORDER BY date DESC", params)
        for row in db_cursor:
            return row[0]
        return 0

    # Attempt to parse args as a valid daily submission, and submits for the daily if sucessful.  #DB_acc
    # Returns a string whose content confirms parse, or the empty string if parse fails.
    def parse_submission(self, daily_number, user, args, overwrite=False):
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

        if not lv == -1: # parse succeeded
            if overwrite:
                self.delete_from_daily(daily_number, user)

            asyncio.ensure_future(self.submit_to_daily(daily_number, user, lv, time))
            return ret_str
        else:
            return ''
                        
    # Submit a run to the given daily number    #DB_acc
    @asyncio.coroutine
    def submit_to_daily(self, daily_number, user, lv, time):
        db_cursor = self._db_conn.cursor()
        race_params = (daily_number, user.name, user.id, lv, time,)
        db_cursor.execute("INSERT INTO daily_races VALUES (?,?,?,?,?)", race_params)
        self._db_conn.commit()

        #if submitting for today, make spoilerchat visible
        if daily_number == self.today_number():
            read_permit = discord.Permissions.none()
            read_permit.read_messages = True
            yield from self._client.edit_channel_permissions(self._spoilerchat_channel, user, allow=read_permit)
                    
    # Delete a run from the daily #DB_acc
    def delete_from_daily(self, daily_number, user):
        db_cursor = self._db_conn.cursor()
        delete_params = (daily_number, user.id,)
        db_cursor.execute("DELETE FROM daily_races WHERE date=? AND playerid=?", delete_params)
        self._db_conn.commit()
    
    # Return the seed for the given daily number. Create seed if it doesn't already exist. #DB_acc
    @asyncio.coroutine
    def get_seed(self, daily_number):
        db_cursor = self._db_conn.cursor()
        param = (daily_number,)
        db_cursor.execute("SELECT seed FROM daily_seeds WHERE date=?", param)

        for row in db_cursor:
            return row[0]

        #if we made it here, there was no entry in the table, so make one, and make the leaderboard message
        today_seed = seedgen.get_new_seed()
        date_str = daily_to_datestr(daily_number)
        if self._leaderboard_channel:
            text = self.leaderboard_text(daily_number)
            msg = yield from self._client.send_message(self._leaderboard_channel, text)
            values = (daily_number, today_seed, msg.id,)
            db_cursor.execute("INSERT INTO daily_seeds VALUES (?,?,?)", values)
            self._db_conn.commit()

            #update the most recent leaderboard with the seed
            db_cursor.execute("SELECT date FROM daily_seeds ORDER BY date DESC")
            for row in db_cursor:
                if row[0] != self.today_number():
                    asyncio.ensure_future(self.update_leaderboard(row[0], True))
                    break #only do the most recent one that isn't today

            #hide dailyspoilerchat for those users with that preference
            if self._prefs_manager and self._spoilerchat_channel:
                hide_pref = userprefs.UserPrefs()
                hide_pref.hide_spoilerchat = True
                
                members_to_hide_for = self._prefs_manager.get_all_matching(hide_pref)
                for member in members_to_hide_for:
                    read_permit = discord.Permissions.none()
                    read_permit.read_messages = True
                    yield from self._client.edit_channel_permissions(self._spoilerchat_channel, member, deny=read_permit)                

        return today_seed
        
    # Update an existing leaderboard message for the given daily number #DB_acc
    @asyncio.coroutine
    def update_leaderboard(self, daily_number, display_seed=False):
        db_cursor = self._db_conn.cursor()
        params = (daily_number,)
        db_cursor.execute("SELECT * FROM daily_seeds WHERE date=?", params)
        for row in db_cursor: #hack to check non-empty. only ever doing this once.
            if self._leaderboard_channel:
                seed = row[1]
                msg_id = row[2]
                msg_list = yield from self._client.logs_from(self._leaderboard_channel, 10)
                for msg in msg_list:
                    if int(msg.id) == int(msg_id):
                        asyncio.ensure_future(self._client.edit_message(msg, self.leaderboard_text(daily_number, display_seed)))
