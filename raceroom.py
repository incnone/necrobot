# Class representing a channel in which a race (or several races) will occur.
# The list of all race rooms is managed by RaceManager, which is typically
# responsible for creating such rooms.

import asyncio
import command
import config
import datetime
import discord
import level
import racetime
import textwrap
import time

from race import Race
from racer import Racer

SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
def ordinal(num):
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = SUFFIXES.get(num % 10, 'th')
    return str(num) + suffix

class Enter(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'enter', 'join', 'e')
        self.help_text = 'Enters (registers for) the race. After entering, use `.ready` to indicate you are ready to begin the race. You may use `.join` instead of `.enter` if preferred.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return
        
        new_entry = yield from self._room.race.enter_racer(command.author)
        if new_entry:
            self._room.notify(command.author)
            yield from self._room.write('{0} has entered the race. {1} entrants.'.format(command.author.mention, len(self._room.race.racers)))
        else:
            yield from self._room.write('{0} is already entered.'.format(command.author.mention))     

class Unenter(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'unenter', 'unjoin')
        self.help_text = 'Leaves the race. You may use `.unjoin` instead of `.unenter` if preferred.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return
        
        self._room.dont_notify(command.author)
        success = yield from self._room.race.unenter_racer(command.author)
        if success:
            yield from self._room.write('{0} is no longer entered.'.format(command.author.mention))

class Ready(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'ready', 'r')
        self.help_text = 'Indicates that you are ready to begin the race. The race begins when all entrants are ready.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return
        
        racer = self._room.race.get_racer(command.author)
        if racer:
            success = yield from self._room.race.ready_racer(racer)    #success is True if the racer was unready and now is ready
            if success:
                if len(self._room.race.racers) == 1 and config.REQUIRE_AT_LEAST_TWO_FOR_RACE:
                    yield from self._room.write('Waiting on at least one other person to join the race.')
                else:
                    yield from self._room.write('{0} is ready! {1} remaining.'.format(command.author.mention, self._room.race.num_not_ready))

                yield from self._room.begin_if_ready()

            elif racer.is_ready:
                yield from self._room.write('{0} is already ready!'.format(command.author.mention))
        else:
            yield from self._room.write('{}: Please `.enter` the race before readying.'.format(command.author.mention))
                    
class Unready(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'unready')
        self.help_text = 'Undoes `.ready`.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return
        
        racer = self._room.race.get_racer(command.author)
        if racer:
            success = yield from self._room.race.unready_racer(racer)  #success is True if the racer was ready and now is unready
            #NB: success might be False even in reasonable-use contexts, e.g., if the countdown fails to cancel
            if success:
                yield from self._room.write('{0} is no longer ready.'.format(command.author.mention))
        else:
            yield from self._room.write('{}: Warning: You have not yet entered the race.'.format(command.author.mention))

class Done(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'done', 'finish', 'd')
        self.help_text = 'Indicates you have finished the race goal, and gets your final time. You may instead use `.finish` if preferred.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        racer = self._room.race.get_racer(command.author)
        if racer:
            success = yield from self._room.race.finish_racer(racer) #success is true if the racer was racing and is now finished
            if success:
                num_finished = self._room.race.num_finished
                yield from self._room.write('{0} has finished in {1} place with a time of {2}.'.format(command.author.mention, ordinal(num_finished), racer.time_str))

class Undone(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'undone', 'unfinish')
        self.help_text = 'Undoes an earlier `.done`.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        success = yield from self._room.race.unfinish_racer(self._room.race.get_racer(command.author)) #success is true if the racer was finished and now is not
        #NB: success might be False even in reasonable-use contexts, e.g., if the race became finalized
        if success: 
            yield from self._room.write('{} is no longer done and continues to race.'.format(command.author.mention))

class Forfeit(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forfeit', 'quit')
        self.help_text = 'Forfeits from the race. You may use `.quit` instead of `.forfeit` if preferred.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        success = yield from self._room.race.forfeit_racer(self._room.race.get_racer(command.author)) #success is True if the racer was racing and is now forfeit
        if success:
            yield from self._room.write('{} has forfeit the race.'.format(command.author.mention))

        if len(command.args) > 0:
            racer = self._room.race.get_racer(command.author)
            if racer:
                cut_length = len(command.command) + len(config.BOT_COMMAND_PREFIX) + 1
                end_length = 255 + cut_length
                racer.add_comment(command.message.content[cut_length:end_length])
                asyncio.ensure_future(self._room.update_leaderboard())            

class Unforfeit(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'unforfeit', 'unquit')
        self.help_text = 'Undoes an earlier `.forfeit`.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        success = yield from self._room.race.unforfeit_racer(self._room.race.get_racer(command.author)) #success is true if the racer was forfeit and now is not
        #NB: success might be False even in reasonable-use contexts, e.g., if the race became finalized
        if success: 
            yield from self._room.write('{} is no longer forfeit and continues to race.'.format(command.author.mention))
                    
class Comment(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'comment')
        self.help_text = 'Adds text as a comment to your race.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        racer = self._room.race.get_racer(command.author)
        if racer:
            cut_length = len(command.command) + len(config.BOT_COMMAND_PREFIX) + 1
            end_length = 255 + cut_length
            racer.add_comment(command.message.content[cut_length:end_length])
            asyncio.ensure_future(self._room.update_leaderboard())

class Death(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'death')
        self.help_text = 'Marks your race as having died at a given level, e.g., `{} 3-2`.'.format(self.mention)
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        if len(command.args) == 1:
            lvl = level.from_str(command.args[0])
            racer = self._room.race.get_racer(command.author)
            if lvl != -1 and racer:
                yield from self._room.race.forfeit_racer(self._room.race.get_racer(command.author))
                racer.level = lvl
                asyncio.ensure_future(self._room.update_leaderboard())

class Igt(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'igt')
        self.help_text = 'Adds an in-game-time to your race, e.g. `{} 12:34.56.`'.format(self.mention)
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        if len(command.args) == 1:
            igt = racetime.from_str(command.args[0])
            racer = self._room.race.get_racer(command.author)
            if igt != -1 and racer and racer.is_done_racing:
                racer.igt = igt
                asyncio.ensure_future(self._room.update_leaderboard())

class Rematch(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'rematch')
        self.help_text = 'If the race is complete, creates a new race with the same rules in a separate room.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            yield from self._room.write('{}: Maybe we should do this race first.'.format(command.author.mention))
        elif self._room.race.complete:
            yield from self._room.make_rematch()
        else:
            yield from self._room.write('{}: The current race has not yet ended!'.format(command.author.mention))

class DelayRecord(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'delayrecord')
        self.help_text = 'If the race is complete, delays recording of the race for some extra time.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.complete:
            return
        
        if not self._room.race.delay_record:
            self._room.race.delay_record = True
            yield from self._room.write('Delaying recording for an extra {} seconds.'.format(config.FINALIZE_TIME_SEC))
        else:
            yield from self._room.write('Recording is already delayed.')
                    
class Notify(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'notify')
        self.help_text = 'If a rematch of this race is made, you will be @mentioned at the start of its channel. Use `.notify off` to cancel this.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):        
        if len(command.args) == 1 and command.args[0] == 'off':
            self._room.dont_notify(command.author)
            yield from self._room.write('{0}: You will not be alerted when a rematch begins.'.format(command.author.mention))
        elif len(command.args) == 0 or len(command.args) == 1 and command.args[1] == 'on':
            self._room.notify(command.author)
            yield from self._room.write('{0}: You will be alerted when a rematch begins.'.format(command.author.mention))      

class Time(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'time')
        self.help_text = 'Get the current race time.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            yield from self._room.write('The race hasn\'t started.')
        elif self._room.race.complete:
            yield from self._room.write('The race is over.')
        else:
            yield from self._room.write('The current race time is {}.'.format(self._room.race.current_time_str))

class Missing(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'missing')
        self.help_text = 'List users that were notified but have not yet entered.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        missing_usernames = ''
        for user in self._room.mentioned_users:
            user_entered = False
            for racer in self._room.race.racers.values():
                if int(racer.member.id) == int(user.id):
                    user_entered = True
                    break
            if not user_entered:
                missing_usernames += user.name + ', '
        if missing_usernames:
            yield from self._room.write('Missing: {0}.'.format(missing_usernames[:-2]))
        else:
            yield from self._room.write('No one missing!')

class Shame(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'shame')
        self.help_text = ''
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        yield from self._room.write('Shame on you {0}!'.format(command.author))

class Poke(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'poke')
        self.help_text = 'If only one, or fewer than 1/4, of the racers are unready, this command @mentions them.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return
        
        ready_racers = []
        unready_racers = []
        for racer in self._room.race.racers.values():
            if racer.is_ready:
                ready_racers.append(racer)
            else:
                unready_racers.append(racer)

        num_unready = len(unready_racers)
        quorum = (num_unready == 1) or (3*num_unready <= len(ready_racers))

        if ready_racers and quorum:
            alert_string = ''
            for racer in unready_racers:
                alert_string += racer.member.mention + ', '
            yield from self._room.write('Poking {0}.'.format(alert_string[:-2]))

class ForceCancel(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forcecancel')
        self.help_text = 'Cancels the race.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            yield from self._room.race.cancel()

class ForceClose(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forceclose')
        self.help_text = 'Cancel the race, and close the channel.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            yield from self._room.close()

class ForceForfeit(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forceforfeit')
        self.help_text = 'Force the given racer to forfeit the race (even if they have finished).'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author) and not self._room.race.is_before_race:
            for name in command.args:
                for racer in self._room.race.racers.values():
                    if racer.name.lower() == name.lower():
                        asyncio.ensure_future(self._room.race.forfeit_racer(racer))

class ForceForfeitAll(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forceforfeitall')
        self.help_text = 'Force all unfinished racers to forfeit the race.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author) and not self._room.race.is_before_race:
            for racer in self._room.race.racers.values():
                if racer.is_racing:
                    asyncio.ensure_future(self._room.race.forfeit_racer(racer))
                        
class Kick(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'kick')
        self.help_text = 'Remove a racer from the race. (They can still re-enter with `.enter`.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            names_to_kick = [n.lower() for n in command.args]
            for racer in self._room.race.racers.values():
                if racer.name.lower() in names_to_kick:
                    success = yield from self._room.race.unenter_racer(racer)
                    if success:
                        yield from self._room.write('Kicked {} from the race.'.format(racer.name))
                                
class RaceRoom(command.Module):

    def __init__(self, race_module, race_channel, race_info):
        self.channel = race_channel                 #The channel in which this race is taking place
        self.creator = None                         #Can store a user that created this room. Not used internally.
        self.is_closed = False                      #True if room has been closed
        self.race = Race(self, race_info)           #The current race
        self.admin_ready = True

        self._rm = race_module           
        self._rematch_made = False                  #True once a rematch of this has been made (prevents duplicates)
        self._mention_on_rematch = []               #A list of users that should be @mentioned when a rematch is created
        self.mentioned_users = []                  #A list of users that were @mentioned when this race started

        self.command_types = [command.DefaultHelp(self),
                              Enter(self),
                              Unenter(self),
                              Ready(self),
                              Unready(self),
                              Done(self),
                              Undone(self),
                              Forfeit(self),
                              Unforfeit(self),
                              Comment(self),
                              Death(self),
                              Igt(self),
                              Rematch(self),
                              DelayRecord(self),
                              Notify(self),
                              Time(self),
                              Missing(self),
                              Shame(self),
                              Poke(self),
                              ForceCancel(self),
                              ForceClose(self),
                              ForceForfeit(self),
                              ForceForfeitAll(self),
                              Kick(self)]

    @property
    def infostr(self):
        return 'Race'

    @property
    def client(self):
        return self._rm.client

    # Notifies the given user on a rematch
    def notify(self, user):
        if not user in self._mention_on_rematch:
            self._mention_on_rematch.append(user)

    # Removes notifications for the given user on rematch
    def dont_notify(self, user):
        self._mention_on_rematch = [u for u in self._mention_on_rematch if u != user]

    # Set up the leaderboard etc. Should be called after creation; code not put into __init__ b/c coroutine
    @asyncio.coroutine
    def initialize(self, users_to_mention=[]):
        asyncio.ensure_future(self.race.initialize())
        asyncio.ensure_future(self.client.edit_channel(self.channel, topic=self.race.leaderboard))
        asyncio.ensure_future(self._monitor_for_cleanup())

        #send @mention message
        mention_text = ''
        for user in users_to_mention:
            mention_text += user.mention + ' '
            self.mentioned_users.append(user)
        if mention_text:
            asyncio.ensure_future(self.client.send_message(self.channel, 'Alerting users: ' + mention_text))

    # Write text to the raceroom. Return a Message for the text written
    @asyncio.coroutine
    def write(self, text):
        return self.client.send_message(self.channel, text)

    # A string to add to the race details (used for private races; empty in base class)
    def format_rider(self):
        return ''

    #Updates the leaderboard
    @asyncio.coroutine
    def update_leaderboard(self):
        asyncio.ensure_future(self.client.edit_channel(self.channel, topic=self.race.leaderboard))        

    # Close the channel.
    @asyncio.coroutine
    def close(self):
        self.is_closed = True
        yield from self.client.delete_channel(self.channel)

    # Returns true if all racers are ready
    @property
    def all_racers_ready(self):
        return self.race.num_not_ready == 0 and (not config.REQUIRE_AT_LEAST_TWO_FOR_RACE or len(self.race.racers) > 1)

    # Begins the race if ready. (Writes a message if all racers are ready but an admin is not.)
    # Returns true on success
    @asyncio.coroutine
    def begin_if_ready(self):
        if self.all_racers_ready:
            if self.admin_ready:
                yield from self.race.begin_race_countdown()
                return True
            else:
                yield from self.write('Waiting on an admin to type `.ready`.')
                return False

    # Makes a rematch of this race in a new room, if one has not already been made
    @asyncio.coroutine
    def make_rematch(self):
        if not self._rematch_made:
            self._rematch_made = True
            new_race_info = self.race.race_info.copy()
            new_race_channel = yield from self._rm.make_race(new_race_info, mention=self._mention_on_rematch, suppress_alerts=True)
            if new_race_channel:
                yield from self.write('Rematch created in {}!'.format(new_race_channel.mention))
##                yield from self._rm.client.send_message(self._rm.main_channel, 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(new_race_channel.mention, new_race_info.format_str()))
            else:
                self._rematch_made = False

    #True if the user has admin permissions for this race
    def is_race_admin(self, member):
        admin_roles = self._rm.necrobot.admin_roles
        for role in member.roles:
            if role in admin_roles:
                return True
        
        return False

    # Checks to see whether the room should be cleaned.
    @asyncio.coroutine
    def _monitor_for_cleanup(self):
        # Pre-race cleanup loop
        while not self.is_closed:
            yield from asyncio.sleep(30) #Wait between check times

            # Pre-race
            if self.race.is_before_race:
                if (not self.race.racers) and self.race.no_entrants_time: #if there are no entrants (and we've stored the last time this was not the case)
                    if time.clock() - self.race.no_entrants_time > config.NO_ENTRANTS_CLEANUP_WARNING_SEC:
                        time_remaining = config.NO_ENTRANTS_CLEANUP_SEC - config.NO_ENTRANTS_CLEANUP_WARNING_SEC
                        yield from self.write('Warning: Race has had zero entrants for some time and will be closed in {} seconds.'.format(time_remaining))
                        yield from asyncio.sleep(time_remaining)
                        if not self.race.racers:
                            yield from self.close()
                            return

            # Post-race
            elif self.race.complete:
                msg_list = yield from self.client.logs_from(self.channel, 1)
                for msg in msg_list:
                    if (datetime.datetime.utcnow() - msg.timestamp).total_seconds() > config.CLEANUP_TIME_SEC:
                        yield from self.close()
                        return               

    ## TODO: more intelligent result posting
    @asyncio.coroutine
    def post_result(self, text):
        asyncio.ensure_future(self.client.send_message(self._rm.results_channel, text))
