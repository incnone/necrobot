# Class representing a channel in which a race (or several races) will occur.
# The list of all race rooms is managed by RaceManager, which is typically
# responsible for creating such rooms.

import asyncio
import config
import datetime
import discord
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

raceroom_topic = textwrap.dedent("""\
    [Click for command list]
    `.enter` : Join the race (undo with `.unenter`)
    `.ready` : Tell bot you're ready (undo with `.unready`)
    `.done`  : Finish the race. (undo with `.undone`)
    `.forfeit` : Forfeit the race (undo with `.unforfeit`)
    `.comment` : Add a comment
    `.igt` : Add an in-game time
    """)

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
    'comment':"`.comment text` : Adds  text as a comment to your race.",
    'igt':"`.igt time` : Adds an in-game-time to your race. time takes the form 12:34.56.",
    'rematch':"`.rematch` : If the race is complete, creates a new race with the same rules in a separate room."
    }

class RaceRoom(object):

    def __init__(self, discord_client, race_manager, race_channel, race_info):
        self.client = discord_client           
        self.channel = race_channel                 #The channel in which this race is taking place
        self.creator_id = None                      #Can store a user that created this room. Not used internally.
        self._manager = race_manager                #Used for server-specific calls (e.g. getting all admin roles)
        self._race = Race(self, race_info)  

        self.is_closed = False                      #True if room has been closed
        self._rematch_made = False                  #True once a rematch of this has been made (prevents duplicates)

    # Set up the leaderboard etc. Should be called after creation; code not put into __init__ b/c coroutine
    @asyncio.coroutine
    def initialize(self):
        asyncio.ensure_future(self._race.initialize())
        asyncio.ensure_future(self.client.edit_channel(self.channel, topic=raceroom_topic))
        asyncio.ensure_future(self._monitor_for_cleanup())

    # Write text to the raceroom. Return a Message for the text written
    @asyncio.coroutine
    def write(self, text):
        return self.client.send_message(self.channel, text)

    # Close the channel.
    @asyncio.coroutine
    def close(self):
        self.is_closed = True
        yield from self.client.delete_channel(self.channel)

    # Attempt to read an incoming command
    @asyncio.coroutine
    def parse_message(self, message):      
        # Allow derived classes the opportunity to parse this message first
        success = yield from self._derived_parse_message(message)
        if success:
            return

        args = message.content.split()
        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)

        #.help command
        if command == 'help':
            if len(args) == 1:
                if args[0] in cmd_help_info:
                    yield from (cmd_help_info[args[0].lstrip(config.BOT_COMMAND_PREFIX)])
            else:   
                yield from self.write(textwrap.dedent("""\
                    Command list:
                    Always: `.help` or `.help [command]` for information on a specific command
                    Before the race: `.enter`, `.unenter`, `.ready`, `.unready`
                    During the race: `.done`, `.undone`, `.forfeit`, `.unforfeit`
                    After the race: `.comment [short comment]`, `.igt 12:34.56` 
                    """))

        # Admin commands
        if self._is_race_admin(message.author): 

            ## General TODO here: In principle, usernames can be duplicated, in which case these kick/ban commands are awkward. This could be avoided
            ## by forcing these commands to be used with Discord mentions, which contain user id's. TODO is make this work in a good way.
                
            #.forcecancel : Cancels the race.
            if command == 'forcecancel':
                yield from self._race.cancel()

            #.forceclose: Immediately closes the race (deletes the channel)
            elif command == 'forceclose':
                yield from self.close()

            #.forceforfeit [username1 username2 ...]: Forces all racers with any of the given usernames to forfeit, even if they have already finished.
            #(Note: This does not prevent racers from returning to the race with .unforfeit.)
            elif command == 'forceforfeit' and not self._race.is_before_race:
                for name in args:
                    for r_id in self._race.racers:
                        racer = self._race.racers[r_id]
                        if racer.name.lower() == name.lower():
                            asyncio.ensure_future(self._race.forfeit_racer(racer))

            #.forceforfeitall: Forces all racers still racing to forfeit.
            elif command == 'forceforfeitall' and not self._race.is_before_race:
                for r_id in self._race.racers:
                    racer = self._race.racers[r_id]
                    if racer.is_racing:
                        asyncio.ensure_future(self.forfeit_racer(racer))

            #.kick username: Removes any racer with the given username from the race 
            elif command == 'kick':
                if len(args) == 1:
                    name_to_kick = args[0]
                    for r_id, racer in list(self._racers.items()):
                        if racer.name.lower() == name_to_kick.lower():
                            success = yield from self._race.unenter_racer(racer)
                            if success:
                                yield from self.write('Kicked {} from the race.'.format(racer.name))
                            
        # Commands before the race
        if self._race.is_before_race: 

            # Commands while entry is open
            if self._race.entry_open:
                #.enter and .join : Enter the race
                if command == 'enter' or command == 'join':
                    new_entry = yield from self._race.enter_racer(message.author)
                    if new_entry:
                        yield from self.write('{0} has entered the race. {1} entrants.'.format(message.author.mention, len(self._race.racers)))
                    else:
                        yield from self.write('{0} is already entered.'.format(message.author.mention))

                #.unenter and .unjoin : Leave the race
                elif command == 'unenter' or command == 'unjoin':
                    success = yield from self._race.unenter_racer(message.author)
                    if success:
                        self.write('{0} is no longer entered.'.format(message.author.mention))

            #.ready : Tell bot you are ready to begin
            if command == 'ready':
                racer = self._race.get_racer(message.author)
                if racer:
                    success = yield from self._race.ready_racer(racer)    #success is True if the racer was unready and now is ready
                    if success:
                        if len(self._race.racers) == 1 and config.REQUIRE_AT_LEAST_TWO_FOR_RACE:
                            yield from self.write('Waiting on at least one other person to join the race.')
                        else:
                            yield from self.write('{0} is ready! {1} remaining.'.format(message.author.mention, self._race.num_not_ready))
    
                        all_ready = yield from self._all_racers_ready()
                        if all_ready:
                            if self._admin_ready:
                                yield from self._race.begin_race_countdown()
                            else:
                                yield from self.write('Waiting on an admin to type `.ready`.')
                    elif racer.is_ready:
                        yield from self.write('{0} is already ready!'.format(message.author.mention))
                else:
                    yield from self.write('{}: Please `.enter` the race before readying.'.format(message.author.mention))

            #.unready : Rescind 'ready' status
            elif command == 'unready':
                racer = self._race.get_racer(message.author)
                if racer:
                    success = yield from self._race.unready_racer(racer)  #success is True if the racer was ready and now is unready
                    #NB: success might be False even in reasonable-use contexts, e.g., if the countdown fails to cancel
                    if success:
                        yield from self.write('{0} is no longer ready.'.format(message.author.mention))
                else:
                    yield from self.write('{}: Warning: You have not yet entered the race.'.format(message.author.mention))

        # Commands during the race
        else: 

            #.done and .finish : Finish the race
            if command == 'done' or command == 'finish':
                racer = self._race.get_racer(message.author)
                if racer:
                    success = yield from self._race.finish_racer(racer) #success is true if the racer was racing and is now finished
                    if success:
                        num_finished = self._race.num_finished
                        yield from self.write('{0} has finished in {1} place with a time of {2}.'.format(message.author.mention, ordinal(num_finished), racer.time_str))

            #.undone and .unfinish : Rescind an earlier `.done` command
            elif command == 'undone' or command == 'unfinish':
                success = yield from self._race.unfinish_racer(self._race.get_racer(message.author)) #success is true if the racer was finished and now is not
                #NB: success might be False even in reasonable-use contexts, e.g., if the race became finalized
                if success: 
                    yield from self.write('{} is no longer done and continues to race.'.format(message.author.mention))

            #.forfeit and .quit : Forfeit the race
            elif command == 'forfeit' or command == 'quit':
                success = yield from self._race.forfeit_racer(self._race.get_racer(message.author)) #success is True if the racer was racing and is now forfeit
                if success:
                    yield from self.write('{} has forfeit the race.'.format(message.author.mention))

            #.unforfeit and .unquit : Rescind an earlier `.forfeit` command
            elif command == 'unforfeit' or command == 'unquit':
                success = yield from self._race.unforfeit_racer(self._race.get_racer(message.author)) #success is true if the racer was forfeit and now is not
                #NB: success might be False even in reasonable-use contexts, e.g., if the race became finalized
                if success: 
                    yield from self.write('{} is no longer forfeit and continues to race.'.format(message.author.mention))
                    
            #.igt : Input an in-game time for the race
            elif command == 'igt':
                if len(args) == 1:
                    igt = racetime.from_str(args[0])
                    racer = self._race.get_racer(message.author)
                    if igt != -1 and racer and racer.is_finished:
                        racer.igt = igt
                        asyncio.ensure_future(self._race.update_leaderboard())

            #.comment : Add a comment
            elif command == 'comment':
                racer = self._race.get_racer(message.author)
                if racer:
                    cut_length = len(command) + len(config.BOT_COMMAND_PREFIX) + 1
                    end_length = 255 + cut_length
                    racer.add_comment(message.content[cut_length:end_length])
                    asyncio.ensure_future(self._race.update_leaderboard())

            #.rematch : Create a new race with the same race info
            elif command == 'rematch' and self._race.complete and not self._rematch_made:
                new_race_info = self._race.race_info.copy()
                new_race_channel = yield from self._manager.make_race(new_race_info)
                if new_race_channel:
                    self._rematch_made = True
                    yield from self.write('Rematch created in {}!'.format(new_race_channel.mention))

    # Returns true if all racers are ready
    @asyncio.coroutine
    def _all_racers_ready(self):
        return self._race.num_not_ready == 0 and (not config.REQUIRE_AT_LEAST_TWO_FOR_RACE or len(self._race.racers) > 1)

    # Skeleton method, does nothing. Override to add message-parsing functionality in derived classes.
    @asyncio.coroutine
    def _derived_parse_message(self, message):
        return False

    # Returns whether the admins are ready. Made for overriding.
    @asyncio.coroutine
    def _admin_ready(self):
        return True

    #True if the user has admin permissions for this race
    def _is_race_admin(self, member):
        for role in member.roles:
            if role in self._manager.get_admin_roles():
                return True
        
        return False

    # Checks to see whether the room should be cleaned.
    @asyncio.coroutine
    def _monitor_for_cleanup(self):
        # Pre-race cleanup loop
        while not self.is_closed:
            yield from asyncio.sleep(30) #Wait between check times

            # Pre-race
            if self._race.is_before_race:
                if (not self._race.racers) and self._race.no_entrants_time: #if there are no entrants (and we've stored the last time this was not the case)
                    if time.clock() - self._race.no_entrants_time > config.NO_ENTRANTS_CLEANUP_WARNING_SEC:
                        time_remaining = config.NO_ENTRANTS_CLEANUP_SEC - config.NO_ENTRANTS_CLEANUP_WARNING_SEC
                        yield from self.write('Warning: Race has had zero entrants for some time and will be closed in {} seconds.'.format(time_remaining))
                        yield from asyncio.sleep(time_remaining)
                        if not self._race.racers:
                            yield from self.close()
                            return

            # Post-race
            elif self._race.complete:
                msg_list = yield from self.client.logs_from(self.channel, 1)
                for msg in msg_list:
                    if (datetime.datetime.utcnow() - msg.timestamp).total_seconds() > config.CLEANUP_TIME_SEC:
                        yield from self.close()
                        return               

    @asyncio.coroutine
    def post_result(self, text):
        #TODO: be better (handle bestof and repeat races, not just post individual races)
        asyncio.ensure_future(self._manager.post_result(text))           


