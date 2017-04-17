import shlex

from necrobot.util.config import Config
from necrobot.util import console


# Represents a full user command input (e.g. `.make -c Cadence -seed 12345 -custom 4-shrine`)
class Command(object):
    def __init__(self, message):
        self.command = None
        self.args = []      
        self.message = None

        if message.content.startswith(Config.BOT_COMMAND_PREFIX):
            try:
                self.args = shlex.split(message.content)
            except ValueError:
                self.args = message.content.split()
            prefix_len = len(Config.BOT_COMMAND_PREFIX)
            self.command = (self.args.pop(0)[prefix_len:]).lower()
            self.message = message

    @property
    def author(self):
        return self.message.author if self.message else None

    @property
    def server(self):
        return self.message.server if self.message else None

    @property
    def channel(self):
        return self.message.channel if self.message else None

    @property
    def is_private(self):
        return self.message.channel.is_private if self.message else None

    @property
    def arg_string(self):
        cut_len = len(Config.BOT_COMMAND_PREFIX) + len(self.command) + 1
        return self.message.content[cut_len:]


# Abstract base class; a particular command that the bot can interpret, and how to interpret it
# (For instance, racemodule has a CommandType object called make, for the `.make` command.)
class CommandType(object):
    def __init__(self, bot_channel, *args):
        self.command_name_list = args               # the string that calls this command (e.g. 'make')
        self.help_text = 'This command has no help text.'
        self.admin_only = False                     # If true, only botchannel admins can call this command
        self.secret_command = False                 # If true, never shows up on ".help" calls
        self.bot_channel = bot_channel

    @property
    def client(self):
        return self.necrobot.client

    @property
    def necrobot(self):
        return self.bot_channel.necrobot

    @property
    def mention(self):
        return Config.BOT_COMMAND_PREFIX + str(self.command_name_list[0])

    # Returns True if the name can be used to call this command
    def called_by(self, name):
        return name in self.command_name_list

    # If the Command object's command is this object's command, calls the (virtual) method _do_execute on it
    async def execute(self, command):
        if command.command in self.command_name_list and \
                ((not self.admin_only) or self.bot_channel.is_admin(command.author)):
            await self._do_execute(command)

    # Virtual; determine what this CommandType should do with a given Command
    # command: [command.Command]
    async def _do_execute(self, command):
        console.error('Called CommandType._do_execute in the abstract base class.')
        pass
