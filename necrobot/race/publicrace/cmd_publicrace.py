# Commands specific to publicrace.RaceRoom (and its derived classes)

from necrobot.botbase.commandtype import CommandType
from necrobot.config import Config


class DelayRecord(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'delayrecord')
        self.help_text = 'If the race is complete, delays recording of the race for some extra time.'

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is None or (not self.bot_channel.last_begun_race.complete):
            return

        if not self.bot_channel.last_begun_race.delay_record:
            self.bot_channel.last_begun_race.delay_record = True
            await self.bot_channel.write('Delaying recording for an extra {} seconds.'.format(Config.FINALIZE_TIME_SEC))
        else:
            await self.bot_channel.write('Recording is already delayed.')


class Notify(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'notify')
        self.help_text = 'If a rematch of this race is made, you will be @mentioned at the start of its necrobot. ' \
                         'Use `.notify off` to cancel this.'

    async def _do_execute(self, command):
        if len(command.args) == 1 and command.args[0] == 'off':
            self.bot_channel.dont_notify(command.author)
            await self.bot_channel.write(
                '{0}: You will not be alerted when a rematch begins.'.format(command.author.mention))
        elif len(command.args) == 0 or (len(command.args) == 1 and command.args[1] == 'on'):
            self.bot_channel.notify(command.author)
            await self.bot_channel.write(
                '{0}: You will be alerted when a rematch begins.'.format(command.author.mention))


class Unnotify(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unnotify')
        self.help_text = 'You will not be notified on a race remake.'

    async def _do_execute(self, command):
        self.bot_channel.dont_notify(command.author)
        await self.bot_channel.write(
            '{0}: You will not be alerted when a rematch begins.'.format(command.author.mention))


class Missing(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'missing')
        self.help_text = 'List users that were notified but have not yet entered.'

    async def _do_execute(self, command):
        if self.bot_channel.current_race.before_race:
            unentered_usernames = ''
            unready_usernames = ''
            for user in self.bot_channel.mentioned_users:
                user_entered = False
                for racer in self.bot_channel.current_race.racers:
                    if int(racer.member.id) == int(user.id):
                        user_entered = True
                        break
                if not user_entered:
                    unentered_usernames += user.display_name + ', '
            for racer in self.bot_channel.current_race.racers:
                if not racer.is_ready:
                    unready_usernames += racer.member.display_name + ', '

            unentered_usernames = unentered_usernames[:-2] if unentered_usernames else 'Nobody!'
            unready_usernames = unready_usernames[:-2] if unready_usernames else 'Nobody!'

            await self.bot_channel.write(
                'Unentered: {0}. \nUnready: {1}.'.format(unentered_usernames, unready_usernames))
        elif self.bot_channel.current_race.during_race:
            racing_usernames = ''
            for racer in self.bot_channel.current_race.racers:
                if racer.is_racing:
                    racing_usernames += racer.member.display_name + ', '
            racing_usernames = racing_usernames[:-2] if racing_usernames else 'Nobody!'
            await self.bot_channel.write(
                'Still racing: {0}.'.format(racing_usernames))


class Shame(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'shame')
        self.help_text = ''

    @property
    def show_in_help(self):
        return False

    async def _do_execute(self, command):
        await self.bot_channel.write('Shame on you {0}!'.format(command.author.display_name))


class Poke(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'poke')
        self.help_text = 'If only one, or fewer than 1/4, of the racers are unready, this command @mentions them.'

    async def _do_execute(self, command):
        await self.bot_channel.poke()


class ForceCancel(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forcecancel')
        self.help_text = 'Cancels the race.'
        self.admin_only = True

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is not None:
            await self.bot_channel.last_begun_race.cancel()
        else:
            await self.bot_channel.close()


class ForceClose(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forceclose')
        self.help_text = 'Cancel the race, and close the necrobot.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.close()


class Kick(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'kick')
        self.help_text = 'Remove a racer from the race. (They can still re-enter with `.enter`.)'
        self.admin_only = True

    async def _do_execute(self, command):
        names_to_kick = [n.lower() for n in command.args]
        await self.bot_channel.current_race.kick_racers(names_to_kick)


class Rematch(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'rematch', 're', 'rm')
        self.help_text = 'If the race is complete, creates a new race with the same rules in a separate room.'

    async def _do_execute(self, command):
        if self.bot_channel.current_race.complete:
            await self.bot_channel.make_rematch()
        elif not self.bot_channel.current_race.before_race:
            await self.bot_channel.write('{}: The current race has not yet ended!'.format(command.author.mention))
