from necrobot.database import condordb
from necrobot.match import matchutil

from necrobot.config import Config
from necrobot.botbase.command import Command, CommandType


class CloseAllMatches(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'closeallmatches')
        self.help_text = 'Close all match rooms. Use `{0} nolog` to close all rooms without writing ' \
                         'logs (much faster, but no record will be kept of room chat).' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Close all match rooms.'

    async def _do_execute(self, cmd: Command):
        log = not(len(cmd.args) == 1 and cmd.args[0].lstrip('-').lower() == 'nolog')

        await self.client.send_message(
            cmd.channel,
            'Closing all match channels...'
        )
        await self.client.send_typing(cmd.channel)

        await matchutil.delete_all_match_channels(log=log)

        await self.client.send_message(
            cmd.channel,
            'Done closing all match channels.'
        )


# class CloseFinished(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'closefinished')
#         self.help_text = 'Close all match rooms with completed matches. Use `{0} nolog` to close ' \
#                          'without writing logs (much faster, but no record will be kept of room chat).' \
#                          .format(self.mention)
#         self.admin_only = True
#
#     async def _do_execute(self, cmd: Command):
#         log = not(len(cmd.args) == 1 and cmd.args[0].lstrip('-').lower() == 'nolog')
#
#         await self.client.send_message(
#             cmd.channel,
#             'Closing all completed match channels...'
#         )
#         await self.client.send_typing(cmd.channel)
#
#         await matchutil.delete_all_completed_match_channels(log=log)  # TODO
#
#         await self.client.send_message(
#             cmd.channel,
#             'Done closing all completed match channels.'
#         )


class GetCurrentEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'get-current-event')
        self.help_text = 'Get the identifier and name of the current CoNDOR event.' \
                         .format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        schema_name = Config.CONDOR_EVENT.lower()
        try:
            event_name = condordb.get_event_name(schema_name)
        except condordb.EventDoesNotExist:
            await self.client.send_message(
                cmd.channel,
                'Error: The current event (`{0}`) does not exist.'.format(schema_name)
            )
            return

        await self.client.send_message(
            cmd.channel,
            '```\n'
            'Current event:\n'
            '    ID: {0}\n'
            '  Name: {1}\n'
            '```'.format(schema_name, event_name)
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
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        schema_name = cmd.args[0].lower()
        try:
            condordb.create_new_event(schema_name=schema_name)
        except condordb.EventAlreadyExists as e:
            error_msg = 'Error: Schema `{0}` already exists.'.format(schema_name)
            if str(e):
                error_msg += ' (It is registered to the event "{0}".)'.format(e)
            await self.client.send_message(
                cmd.channel,
                error_msg
            )
            return
        except condordb.InvalidSchemaName:
            await self.client.send_message(
                cmd.channel,
                'Error: `{0}` is an invalid schema name. (`a-z`, `A-Z`, `0-9`, `_` and `$` are allowed characters.)' \
                .format(schema_name)
            )
            return

        Config.CONDOR_EVENT = schema_name
        Config.write()
        await self.client.send_message(
            cmd.channel,
            'Registered new CoNDOR event `{0}`, and set it to be the bot\'s current event.'.format(schema_name)
        )


class SetCondorEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-condor-event')
        self.help_text = '`{0} schema_name`: Set the bot\'s current event to `schema_name`.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set the bot\'s current CoNDOR event.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        schema_name = cmd.args[0].lower()
        try:
            event_name = condordb.get_event_name(schema_name=schema_name)
        except condordb.EventDoesNotExist:
            await self.client.send_message(
                cmd.channel,
                'Error: Event `{0}` does not exist.'
            )
            return

        Config.CONDOR_EVENT = schema_name
        Config.write()
        event_name_str = ' ({0})'.format(event_name) if event_name is not None else ''
        await self.client.send_message(
            cmd.channel,
            'Set the current CoNDOR event to `{0}`{1}.'.format(schema_name, event_name_str)
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
        event_name = cmd.arg_string
        schema_name = Config.CONDOR_EVENT.lower()

        try:
            condordb.set_event_name(schema_name=schema_name, event_name=event_name)
        except condordb.EventDoesNotExist:
            await self.client.send_message(
                cmd.channel,
                'Error: The current event (`{0}`) does not exist.'
            )
            return

        await self.client.send_message(
            cmd.channel,
            'Set the name of current CoNDOR event (`{0}`) to {1}.'.format(schema_name, event_name)
        )
