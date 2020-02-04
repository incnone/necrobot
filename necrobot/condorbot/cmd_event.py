import necrobot.exception
from botbase.command import Command
from botbase.commandtype import CommandType
from condorbot.condormgr import CondorMgr
from match import matchdb, matchutil
from util.parse import dateparse


class ScrubDatabase(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'scrubdatabase')
        self.help_text = 'Deletes matches without a current channel and with no played races from the database.'
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        await matchdb.scrub_unchanneled_unraced_matches()
        matchutil.invalidate_cache()
        await cmd.channel.send(
            'Database scrubbed.'
        )


class Deadline(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'deadline')
        self.help_text = 'Get the deadline for scheduling matches.'
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        if not CondorMgr().has_event:
            await cmd.channel.send(
                'Error: No league set.'
            )
            return

        deadline_str = CondorMgr().deadline_str

        if deadline_str is None:
            await cmd.channel.send(
                'No deadline is set for the current league.'
            )
            return

        try:
            deadline = dateparse.parse_datetime(deadline_str)
        except necrobot.exception.ParseException as e:
            await cmd.channel.send(str(e))
            return

        await cmd.channel.send(
            'The current league deadline is "{deadline_str}". As of now, this is '
            '{deadline:%b %d (%A) at %I:%M %p} (UTC).'
            .format(
                deadline_str=deadline_str,
                deadline=deadline
            )
        )


class RegisterCondorEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register-condor-event')
        self.help_text = '`{0} schema_name`: Create a new CoNDOR event in the database, and set this to ' \
                         'be the bot\'s current event.' \
            .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Create a new CoNDOR event.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        schema_name = cmd.args[0].lower()
        try:
            await CondorMgr().create_event(schema_name=schema_name)
        except necrobot.exception.LeagueAlreadyExists as e:
            await cmd.channel.send(
                'Error: Schema `{0}`: {1}'.format(schema_name, e)
            )
            return
        except necrobot.exception.InvalidSchemaName:
            await cmd.channel.send(
                'Error: `{0}` is an invalid schema name. (`a-z`, `A-Z`, `0-9`, `_` and `$` are allowed characters.)'
                .format(schema_name)
            )
            return

        await cmd.channel.send(
            'Registered new CoNDOR event `{0}`, and set it to be the bot\'s current event.'.format(schema_name)
        )


class SetCondorEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setevent')
        self.help_text = '`{0} schema_name`: Set the bot\'s current event to `schema_name`.' \
            .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set the bot\'s current CoNDOR event.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        schema_name = cmd.args[0].lower()
        try:
            await CondorMgr().set_event(schema_name=schema_name)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: Event `{0}` does not exist.'.format(schema_name)
            )
            return

        event_name = CondorMgr().event_name
        league_name_str = ' ({0})'.format(event_name) if event_name is not None else ''
        await cmd.channel.send(
            'Set the current CoNDOR event to `{0}`{1}.'.format(schema_name, league_name_str)
        )


class SetDeadline(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setdeadline')
        self.help_text = '`{0} time`: Set a deadline for scheduling matches (e.g. "friday 12:00"). The given time ' \
                         'will be interpreted in UTC.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set match scheduling deadline.'

    async def _do_execute(self, cmd: Command):
        if not CondorMgr().has_event:
            await cmd.channel.send(
                'Error: No league set.'
            )
            return

        try:
            deadline = dateparse.parse_datetime(cmd.arg_string)
        except necrobot.exception.ParseException as e:
            await cmd.channel.send(str(e))
            return

        await CondorMgr().set_deadline(cmd.arg_string)
        await cmd.channel.send(
            'Set the current league\'s deadline to "{deadline_str}". As of now, this is '
            '{deadline:%b %d (%A) at %I:%M %p (%Z)}.'
            .format(
                deadline_str=cmd.arg_string,
                deadline=deadline
            )
        )


class SetEventName(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-event-name')
        self.help_text = '`{0} event_name`: Set the name of bot\'s current event. Note: This does not ' \
                         'change or create a new event! Use `.register-condor-event` and `.set-condor-event`.' \
            .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Change current event\'s name.'

    async def _do_execute(self, cmd: Command):
        if not CondorMgr().has_event:
            await cmd.channel.send(
                'Error: No league set.'
            )
            return

        await CondorMgr().set_event_name(cmd.arg_string)
        await cmd.channel.send(
            'Set the name of current CoNDOR event (`{0}`) to {1}.'.format(CondorMgr().schema_name, cmd.arg_string)
        )
