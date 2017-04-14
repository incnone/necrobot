from .command import CommandType


# General commands
class LadderRegister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladderregister')
        self.help_text = 'Begin registering yourself for the Necrobot ladder.'

    async def _do_execute(self, cmd):
        pass


class NextRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'next')
        self.help_text = 'Displays upcoming ladder matches.'

    async def _do_execute(self, cmd):
        pass


class Ranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ranked')
        self.help_text = 'Suggest a ranked ladder match with an opponent with `.ranked opponent_name`. Both players ' \
                         'must do this for the match to be made.'

    async def _do_execute(self, cmd):
        pass


class Unranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unranked')
        self.help_text = 'Suggest an unranked ladder match with an opponent with `.ranked opponent_name`. Both ' \
                         'players must do this for the match to be made.'

    async def _do_execute(self, cmd):
        pass


# Matchroom commands
class Confirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'confirm')
        self.help_text = 'Confirm that you agree to the suggested time for this match.'

    async def _do_execute(self, cmd):
        pass


class Postpone(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'postpone')
        self.help_text = 'Postpones the match. An admin can resume with `.forcebeginmatch`.'

    async def _do_execute(self, cmd):
        pass


class Suggest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'suggest')
        self.help_text = 'Suggest a time to schedule a match. Example: `.suggest February 18 17:30` (your local ' \
                         'time; choose a local time with `.timezone`). \n \n' \
                         'General usage is `.schedule localtime`, where `localtime` is a date and time in your ' \
                         'registered timezone. (Use `.timezone` to register a timezone with your account.) ' \
                         '`localtime` takes the form `month date time`, where `month` is the English month ' \
                         'name (February, March, April), `date` is the date number, and `time` is a time ' \
                         '`[h]h:mm`. Times can be given an am/pm rider or this can be left off, e.g., `7:30a` and ' \
                         '`7:30` are interpreted as the same time, as are `15:45` and `3:45p`.'

    async def _do_execute(self, cmd):
        pass


# Admin matchroom commands
class ForceBegin(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-begin')
        self.help_text = 'Force the match to begin now.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        pass


class ForceConfirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-confirm')
        self.help_text = 'Force all racers to confirm the suggested time. You should probably try `.forceupdate` first.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        pass


class ForceReschedule(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-reschedule')
        self.help_text = 'Forces the race to be rescheduled for a specific UTC time. Usage same as `.suggest`, e.g., ' \
                         '`.forcereschedule February 18 2:30p`, except that the timezone is always taken to be UTC. ' \
                         'This command unschedules the match and `.suggests` a new time. Use `.forceconfirm` after ' \
                         'if you wish to automatically have the racers confirm this new time.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        pass


class ForceUnschedule(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-unschedule')
        self.help_text = 'Forces the race to be rescheduled for a specific UTC time. Usage same as `.suggest`, e.g., ' \
                         '`.forcereschedule February 18 2:30p`, except that the timezone is always taken to be UTC. ' \
                         'This command unschedules the match and `.suggests` a new time. Use `.forceconfirm` after ' \
                         'if you wish to automatically have the racers confirm this new time.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        pass
