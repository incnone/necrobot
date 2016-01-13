#TODO intelligent handling of rate limiting
#TODO mod options for races (assist in cleanup)

## Handles bot actions for a single race room

import asyncio
import datetime
import discord
import racetime
import random
import sqlite3
import textwrap
import time

from raceinfo import RaceInfo
from racer import Racer

BOT_COMMAND_PREFIX = '.'                #the prefix used for all bot commands
COUNTDOWN_LENGTH = int(10)              #number of seconds between the final .ready and race start
INCREMENTAL_COUNTDOWN_START = int(5)    #number of seconds at which to start counting down each second in chat
FINALIZE_TIME_MIN = 2                   #minutes after race end to finalize+record race #TODO increase to reasonable value
FINALIZE_WARNING_TIME_SEC = 20          #seconds before finalizing to warn via text
CLEANUP_TIME_MIN = 3                    #minutes of no chatting until the room may be cleaned (only applies if race has been finalized)
REQUIRE_AT_LEAST_TWO_FOR_RACE = True    #if True, then races with only one entrant cannot be started

SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
def ordinal(num):
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = SUFFIXES.get(num % 10, 'th')
    return str(num) + suffix

cmd_help_info = {
    'enter':'`.enter` : Enters (registers for) the race. After entering, use `.ready` to indicate you are ready to begin the race. You may use `.join` instead of `.enter` if preferred.',
    'join':'`.join` : Enters (registers for) the race. After entering, use `.ready` to indicate you are ready to begin the race. You may use `.enter` instead of `.join` if preferred.',
    'unenter':'`.unenter` : Leaves the race. You may use `.unjoin` instead of `.unenter` if preferred.',
    'unjoin':'`.unjoin` : Leaves the race. You may use `.unenter` instead of `.unjoin` if preferred.',
    'ready':'`.ready` : Indicates that you are ready to begin the race. The race begins when all entrants are ready.',
    'unready':'`.unready` : Undoes `.ready`.',
    'done':"`.done` : Indicates you have finished the race goal, and gets your final time. You may instead use `.finish` if preferred.",
    'finish':"`.finish` : Indicates you have finished the race goal, and gets your final time. You may instead use `.done` if preferred.",
    'undone':"`.undone` : Undoes an earlier `.done`.",
    'unfinish':"`.unfinish` : Undoes an earlier `.finish`.",
    'forfeit':"`.forfeit` : Forfeits from the race. You may instead use `.quit` if preferred.",
    'quit':"`.forfeit` : Forfeits from the race. You may instead use `.forfeit` if preferred.",
    'unforfeit':"`.unforfeit` : Undoes an earlier `.forfeit`.",
    'unquit':"`.unquit` : Undoes an earlier `.quit`.",
    'comment':"`.comment [text]` : Adds the text as a comment to your race.",
    'igt':"`.igt [time]` : Adds an in-game-time to your race. [time] takes the form 12:34.56."
    }

RaceStatus = {'uninitialized':0, 'entry_open':1, 'counting_down':2, 'racing':3, 'completed':4, 'finalized':5}
StatusStrs = {'0':'Not initialized.', '1':'Entry open!', '2':'Starting!', '3':'In progress!', '4':'Complete.', '5':'Results Finalized.'}
##    uninitialized   --  initialize() should be called on this object (not called in __init__ because coroutine)
##    entry_open      --  the race is open to new entrants
##    counting_down   --  the racebot is counting down to race start. if people .unready during this time, race reverts to the entry_open state
##    racing          --  the race has begun, and at least one player is still racing
##    race_completed  --  all players have either finished or forfeited. if players .undone during this time, race reverts to the racing state
##    race_finalized  --  all players have finished or forfeited, and the race results are marked as final and can be recorded. no further changes possible.

def status_str(race_status):
    return 'Race Status: {0}'.format(StatusStrs[str(race_status)]);

class Race(object):

    # NB: Call the coroutine initialize() to set up the room
    def __init__(self, discord_client, race_channel, results_channel, race_info):
        self._client = discord_client           
        self._countdown = int(0)                  #the current countdown (TODO: is this the right implementation? unclear what is best)
        self._racers = dict()                     #a dictionary of racers indexed by user id
        self._results_channel = results_channel   #channel in which to record the race
        self._start_time = float(0)               #system clock time for the beginning of the race
        self._start_datetime = None               #UTC time for the beginning of the race
        self._finalization_timer = None           #Timer object that, when it finishes, causes the race to be finalized
        self._leaderboard = None                  #Message object for the leaderboard
        self._countdown_future = None             #The Future object for the race countdown
        self._finalize_future = None              #The Future object for the finalization countdown
        self.race_info = race_info                #information on the type of race (e.g. seeded, seed, character) -- see RaceInfo for details
        self.channel = race_channel               #the channel in which this race is taking place
        self._status = RaceStatus['uninitialized']#see RaceStatus

    #True if there are no racers in the 'racing' state (NB: returns true before the race has begun)
    def _nobody_racing(self):
        for r_id in self._racers:
            racer = self._racers[r_id]
            if racer.is_racing:
                return
            
    # Returns 'header' text for the race, giving info about the rules etc.
    def _leaderboard_header(self):
        return self.race_info.info_str()

    # Returns a list of racers and their statuses. #TODO: sort forfeits v ready
    def _leaderboard_text(self):
        racer_list = []
        max_name_len = 0
        max_time = 0
        for r_id in self._racers:
            racer = self._racers[r_id]
            max_name_len = max(max_name_len, len(racer.name))
            racer_list.append(racer)
            if racer.is_finished:
                max_time = max(racer.time, max_time)
        max_time += 1

        #Sort racers: (1) Finished racers, by time; (2) Forfeit racers; (3) Racers still racing
        racer_list.sort(key=lambda r: r.time if r.is_finished else (max_time if r.is_forfeit else max_time+1))

        text = ''
        rank = int(0)
        for racer in racer_list:
            rank += 1
            rank_str = '{0: >4} '.format(str(rank) + '.' if racer.is_finished else ' ')
            text += (rank_str + (' ' * (max_name_len - len(racer.name))) + racer.name + ' --- ' + racer.status_str + '\n')
        return text

    # True if the given racer is entered in the race
    def has_racer(self, racer_usr):
        return racer_usr.id in self._racers

    # Returns the given racer if possible
    def get_racer(self, racer_usr):
        if self.has_racer(racer_usr):
            return self._racers[racer_usr.id]
        else:
            return None

    # Returns the number of racers not in the 'ready' state
    def num_not_ready(self):
        num = 0
        for r_name in self._racers:
            if not self._racers[r_name].is_ready:
                num += 1
        return num

    # Return the number of racers in the 'finished' state
    def num_finished(self):
        num = 0
        for r_name in self._racers:
            if self._racers[r_name].is_finished:
                num += 1
        return num        

    #True if the race has started
    @property
    def is_before_race(self):
        return self._status < 3

    # Sets up the leaderboard for the race
    @asyncio.coroutine
    def initialize(self):
        if self._status != RaceStatus['uninitialized']:
            return
        
        self._status = RaceStatus['entry_open']  #see RaceStatus
        self._leaderboard = yield from self._client.send_message(self.channel, '```' + self._leaderboard_header() + status_str(self._status) + '```') 
        yield from self._write('Enter the race with `.enter`, and type `.ready` when ready. Finish the race with `.done` or `.forfeit`. Use `.help` for a command list.')

    # Convenience method for writing text to the raceroom. Typical use is: `yield from self._write(str)`
    @asyncio.coroutine
    def _write(self, text):
        asyncio.ensure_future(self._client.send_message(self.channel, text))

    #Updates the leaderboard
    @asyncio.coroutine
    def _update_leaderboard(self):
        new_leaderboard = '```' + self._leaderboard_header() + status_str(self._status) + '\n'
        new_leaderboard += 'Entrants:\n'
        new_leaderboard += self._leaderboard_text()
        new_leaderboard += '```'

        asyncio.ensure_future(self._client.edit_message(self._leaderboard, new_leaderboard))

    # Attempt to read an incoming command
    @asyncio.coroutine
    def parse_message(self, message):
##        if not message.channel.id == self.channel.id: #checked in racemgr
##            return
        
        args = message.content.split()
        command = args.pop(0).replace(BOT_COMMAND_PREFIX, '', 1)

        #.help command
        if command == 'help':
            if len(args) == 1:
                if args[0] in cmd_help_info:
                    yield from self._write(cmd_help_info[args[0].lstrip('.')])
            else:   
                yield from self._write(textwrap.dedent("""\
                    Command list:
                    Always: `.help` or `.help [command]` for information on a specific command
                    Before the race: `.enter`, `.unenter`, `.ready`, `.unready`
                    During the race: `.done`, `.undone`, `.forfeit`, `.unforfeit`
                    After the race: `.comment [short comment]`, `.igt 12:34.56` 
                    """))

        # Commands before the race
        if self.is_before_race: 

            #.enter and .join : Enter the race
            if command == 'enter' or command == 'join':
                new_entry = yield from self.enter_racer(message.author)
                if new_entry:
                    yield from self._write('{0} has entered the race. {1} entrants.'.format(message.author.mention, len(self._racers)))
                else:
                    yield from self._write('{0} is already entered.'.format(message.author.mention))

            #.unenter and .unjoin : Leave the race
            elif command == 'unenter' or command == 'unjoin':
                success = yield from self.unenter_racer(message.author)
                if success:
                    self._write('{0} is no longer entered.'.format(message.author.mention))

            #.ready : Tell bot you are ready to begin
            elif command == 'ready':
                racer = self.get_racer(message.author)
                if racer:
                    success = yield from self.ready_racer(racer)    #success is True if the racer was unready and now is ready
                    if success:
                        num_not_ready = self.num_not_ready()
                        if len(self._racers) == 1 and REQUIRE_AT_LEAST_TWO_FOR_RACE:
                            yield from self._write('Waiting on at least one other person to join the race.')
                        else:
                            yield from self._write('{0} is ready! {1} remaining.'.format(message.author.mention, num_not_ready))
    
                        if num_not_ready == 0 and (not REQUIRE_AT_LEAST_TWO_FOR_RACE or len(self._racers) > 1):
                            yield from self.begin_race_countdown()
                    elif racer.is_ready:
                        yield from self._write('{0} is already ready!'.format(message.author.mention))
                else:
                    yield from self._write('{}: Please `.enter` the race before readying.'.format(message.author.mention))

            #.unready : Rescind 'ready' status
            elif command == 'unready':
                racer = self.get_racer(message.author)
                if racer:
                    success = yield from self.unready_racer(racer)  #success is True if the racer was ready and now is unready
                    #NB: success might be False even in reasonable-use contexts, e.g., if the countdown fails to cancel
                    if success:
                        yield from self._write('{0} is no longer ready.'.format(message.author.mention))
                else:
                    yield from self._write('{}: Warning: You have not yet entered the race.'.format(message.author.mention))

        # Commands during the race
        else: 

            #.done and .finish : Finish the race
            if command == 'done' or command == 'finish':
                success = yield from self.finish_racer(message.author) #success is true if the racer was racing and is now finished
                if success:
                    racer = self.get_racer(message.author)
                    if racer:
                        num_finished = self.num_finished()
                        yield from self._write('{0} has finished in {1} place with a time of {2}.'.format(message.author.mention, ordinal(num_finished), racer.time_str))

            #.undone and .unfinish : Rescind an earlier `.done` command
            elif command == 'undone' or command == 'unfinish':
                success = yield from self.unfinish_racer(message.author) #success is true if the racer was finished and now is not
                #NB: success might be False even in reasonable-use contexts, e.g., if the race became finalized
                if success: 
                    yield from self._write('{} is no longer done and continues to race.'.format(message.author.mention))

            #.forfeit and .quit : Forfeit the race
            elif command == 'forfeit' or command == 'quit':
                success = yield from self.forfeit_racer(message.author) #success is True if the racer was racing and is now forfeit
                if success:
                    yield from self._write('{} has forfeit the race.'.format(message.author.mention))

            #.unforfeit and .unquit : Rescind an earlier `.forfeit` command
            elif command == 'unforfeit' or command == 'unquit':
                success = yield from self.unforfeit_racer(message.author) #success is true if the racer was forfeit and now is not
                #NB: success might be False even in reasonable-use contexts, e.g., if the race became finalized
                if success: 
                    yield from self._write('{} is no longer forfeit and continues to race.'.format(message.author.mention))
                    
            #.igt : Input an in-game time for the race
            elif command == 'igt':
                igt = racetime.from_str(args[0])
                racer = self.get_racer(message.author)
                if igt != -1 and racer and racer.is_finished:
                    racer.igt = igt
                    asyncio.ensure_future(self._update_leaderboard())

            #.comment : Add a comment
            elif command == 'comment':
                racer = self.get_racer(message.author)
                if racer:
                    cut_length = len(command) + 2
                    end_length = 255 + cut_length
                    racer.add_comment(message.content[cut_length:end_length])
                    asyncio.ensure_future(self._update_leaderboard())
                

    # Begins the race. Called by the countdown.
    @asyncio.coroutine
    def begin_race(self):
        for r_id in self._racers:
            if not self._racers[r_id].begin_race():
                print("{} isn't ready while calling race.begin_race -- unexpected error.".format(racer.name))

        self._start_time = time.clock()
        self._start_datetime = datetime.datetime.utcnow()
        yield from self._write('GO!')
        self._status = RaceStatus['racing']
        asyncio.ensure_future(self._update_leaderboard())

    # Begin the race countdown and transition race state from 'entry_open' to 'counting_down'
    @asyncio.coroutine
    def begin_race_countdown(self):
        if self._status == RaceStatus['entry_open']:
            self._status = RaceStatus['counting_down']
            self._countdown_future = asyncio.ensure_future(self.race_countdown())
            asyncio.ensure_future(self._update_leaderboard())

    # Checks to see if all racers have either finished or forfeited. If so, ends the race.
    # Return True if race was ended.
    @asyncio.coroutine
    def _check_for_race_end(self):
        for r_id in self._racers:
            if not self._racers[r_id].is_done_racing:
                return False

        yield from self._end_race()
        return True

    # Ends the race, and begins a countdown until the results are 'finalized' (record results, and racers can no longer `.undone`, `.comment`, etc)
    @asyncio.coroutine
    def _end_race(self):
        if self._status == RaceStatus['racing']:
            self._status = RaceStatus['completed']
            self._finalize_future = asyncio.ensure_future(self.finalization_countdown())

    # Countdown coroutine to be wrapped in self._countdown_future.
    # Warning: Do not call this -- use begin_countdown instead.
    @asyncio.coroutine
    def race_countdown(self):
        countdown_timer = COUNTDOWN_LENGTH
        yield from asyncio.sleep(1) #Pause before countdown
        
        yield from self._write('The race will begin in {0} seconds.'.format(countdown_timer))
        while countdown_timer > 0:
            if countdown_timer <= INCREMENTAL_COUNTDOWN_START:
                yield from self._write('{}'.format(countdown_timer))
            yield from asyncio.sleep(1) #sleep for a second
            countdown_timer -= 1

        #Begin the race. At this point, ignore cancel() requests
        try:
            yield from self.begin_race()
        except CancelledError:
            if self._status != RaceStatus['racing']:
                yield from self.begin_race()

    # Countdown coroutine to be wrapped in self._finalize_future.
    # Warning: Do not call this -- use end_race instead.
    @asyncio.coroutine
    def finalization_countdown(self):
        asyncio.ensure_future(self._update_leaderboard())

        yield from asyncio.sleep(3) # Waiting for a short time feels good UI-wise
        yield from self._write('The race is over. Results will be recorded in {} minutes. Until then, you may comment with `.comment [text]` or add an in-game-time with `.igt [time]`.'.format(FINALIZE_TIME_MIN))
        yield from asyncio.sleep( (60*FINALIZE_TIME_MIN) - FINALIZE_WARNING_TIME_SEC)
        yield from self._write('Results will be recorded in {} seconds.'.format(FINALIZE_WARNING_TIME_SEC))
        yield from asyncio.sleep(FINALIZE_WARNING_TIME_SEC)

        yield from self.finalize_race()
            
    # Finalizes the race
    def finalize_race(self):
            self._status = RaceStatus['finalized']
            asyncio.ensure_future(self.record())
            asyncio.ensure_future(self.monitor_for_cleanup())
            yield from self._write('Results recorded. This channel will be automatically closed when it becomes silent.')

    # Attempt to cancel the race countdown -- transition race state from 'counting_down' to 'entry_open'
    # Returns False only if there IS a countdown, AND we failed to cancel it
    @asyncio.coroutine
    def cancel_countdown(self):
        if self._status == RaceStatus['counting_down']:
            self._countdown_future.cancel()
            yield from self._countdown_future
            if self._countdown_future.cancelled():
                self._countdown_future = None
                self._status = RaceStatus['entry_open']
                asyncio.ensure_future(self._update_leaderboard())
                yield from self._write('Countdown cancelled.')
                return True
            else:
                return False
        return True

    # Attempt to cancel finalization and restart race -- transition race state from 'completed' to 'racing'
    # Returns False only if race IS completed, AND we failed to restart it
    @asyncio.coroutine
    def cancel_finalization(self):
        if self._status == RaceStatus['completed']:
            self._finalize_future.cancel()
            yield from self._finalize_future
            if self._finalize_future.cancelled():
                self._finalize_future = None
                self._status = RaceStatus['racing']
                asyncio.ensure_future(self._update_leaderboard())
                yield from self._write('Race end cancelled -- unfinished racers may continue!')
                return True
            else:
                return False
        return True

    # Enters the given discord User in the race
    @asyncio.coroutine
    def enter_racer(self, racer_usr):
        if self._status == RaceStatus['entry_open'] and not self.has_racer(racer_usr):
            racer = Racer(racer_usr.name, racer_usr.id)
            self._racers[racer_usr.id] = racer
            asyncio.ensure_future(self._update_leaderboard())
            return True
        else:
            print('c')
            return False

    # Unenters the given discord User in the race
    @asyncio.coroutine
    def unenter_racer(self, racer_usr):
        if self.has_racer(racer_usr):
            del self._racers[racer_usr.id]
            asyncio.ensure_future(self._update_leaderboard())

    # Puts the given Racer in the 'ready' state
    @asyncio.coroutine
    def ready_racer(self, racer):
        if racer.ready():
            asyncio.ensure_future(self._update_leaderboard())
            return True
        else:
            return False

    # Attempt to put the given Racer in the 'unready' state if they were ready
    @asyncio.coroutine
    def unready_racer(self, racer):
        # See if we can cancel a countdown. If cancel_countdown() returns False,
        # then there is a countdown and we failed to cancel it, so racer cannot be made unready.
        if self.cancel_countdown() and racer.unready(): 
            asyncio.ensure_future(self._update_leaderboard())
            return True
        else:
            return False

    # Puts the given Racer in the 'finished' state and gets their time
    @asyncio.coroutine
    def finish_racer(self, racer_usr):
        if self._status != RaceStatus['racing']:
            return False
        
        finish_time = time.clock()
        racer = self.get_racer(racer_usr)
        if racer and racer.finish(int(100*(finish_time - self._start_time))):
            asyncio.ensure_future(self._check_for_race_end())
            asyncio.ensure_future(self._update_leaderboard())
            return True
        return False

    # Attempt to put the given Racer in the 'racing' state if they were finished
    @asyncio.coroutine
    def unfinish_racer(self, racer_usr):
        if self._status == RaceStatus['finalized']:
            return False
        
        racer = self.get_racer(racer_usr)
        # See if we can cancel a (possible) finalization. If cancel_finalization() returns False,
        # then there is a finalization and we failed to cancel it, so racer cannot be made unready.
        if self.cancel_finalization() and racer and racer.unfinish():
            asyncio.ensure_future(self._update_leaderboard())
            return True
        return False

    # Puts the given Racer in the 'forfeit' state
    @asyncio.coroutine
    def forfeit_racer(self, racer_usr):
        if self._status != RaceStatus['racing']:
            return False
        
        racer = self.get_racer(racer_usr)
        if racer and racer.forfeit():
            asyncio.ensure_future(self._check_for_race_end())
            asyncio.ensure_future(self._update_leaderboard())
            return True
        return False

    # Attempt to put the given Racer in the 'racing' state if they had forfeit
    @asyncio.coroutine
    def unforfeit_racer(self, racer_usr):
        if self._status == RaceStatus['finalized']:
            return False
        
        racer = self.get_racer(racer_usr)
        # See if we can cancel a (possible) finalization. If cancel_finalization() returns False,
        # then there is a finalization and we failed to cancel it, so racer cannot be made unready.
        if self.cancel_finalization() and racer and racer.unforfeit():
            asyncio.ensure_future(self._update_leaderboard())
            return True
        return False

    # Record the race in the database, and post results to the race_results channel
    @asyncio.coroutine
    def record(self):
        time_str = ''
        if self._start_datetime:
            time_str = self._start_datetime.strftime("%d %B %Y, UTC %H:%M")
        if self._results_channel:
            asyncio.ensure_future(self._client.send_message(self._results_channel, 'Race begun at {0}:\n```{1}{2}```'.format(time_str, self._leaderboard_header(), self._leaderboard_text())))

        db_conn = sqlite3.connect('data/races.db')
        db_cur = db_conn.cursor()
        db_cur.execute("SELECT raceid FROM race_data ORDER BY raceid DESC")
        new_raceid = 0
        for row in db_cur:
            new_raceid = row[0] + 1
            break

        race_params = (new_raceid,
                       self._start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                       self.race_info.character[:255],
                       self.race_info.descriptor[:255],
                       self.race_info.seeded,
                       self.race_info.seed,
                       self.race_info.sudden_death,
                       self.race_info.flagplant,)          
        db_cur.execute("INSERT INTO race_data VALUES (?,?,?,?,?,?,?,?)", race_params)

        racer_list = []
        max_time = 0
        for r_id in self._racers:
            racer = self._racers[r_id]
            racer_list.append(racer)
            if racer.is_finished:
                max_time = max(racer.time, max_time)
        max_time += 1

        racer_list.sort(key=lambda r: r.time if r.is_finished else max_time)

        rank = 0
        for racer in racer_list:
            rank += 1
            racer_params = (new_raceid, racer.id, racer.name, racer.is_finished, racer.time, rank, racer.igt, racer.comment[:255])
            db_cur.execute("INSERT INTO racer_data VALUES (?,?,?,?,?,?,?,?)", racer_params)      


    # After recording, we monitor the channel for chat; after no one chats for long enough, close the channel.
    @asyncio.coroutine
    def monitor_for_cleanup(self):
        while True:
            yield from asyncio.sleep(60) #Wait between check times
            msg_list = yield from self._client.logs_from(self.channel, 1)
            for msg in msg_list:
                if (datetime.datetime.utcnow() - msg.timestamp).total_seconds() > 60*CLEANUP_TIME_MIN:
                    yield from self.close()
                    return
    
    # Close the channel.
    @asyncio.coroutine
    def close(self):
        yield from self._client.delete_channel(self.channel)
            

