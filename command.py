## Represents a user-entered command

import asyncio
import clparse
import config
   
# Represents a full user command input (e.g. `.make -c Cadence -seed 12345 -custom 4-shrine`)
class Command(object):
    def __init__(self, message):   
        self.command = None
        self.args = []      
        self.message = None

        if message.content.startswith(config.BOT_COMMAND_PREFIX):
            self.args = message.content.split()
            prefix_len = len(config.BOT_COMMAND_PREFIX)
            self.command = self.args.pop(0)[prefix_len:]
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

# Abstract base class; a particular command that the bot can interpret, and how to interpret it
# (For instance, racemodule has a CommandType object called make, for the `.make` command.)
class CommandType(object):
    def __init__(self, cmd_str):
        self.command = cmd_str              # the string that calls this command (e.g. 'make')
        help_text = 'Error: this command has no help text.'

    @property
    def mention(self):
        return config.BOT_COMMAND_PREFIX + self.command

    # If the Command object's command is this object's command, calls the (virtual) method _do_execute on it
    @asyncio.coroutine
    def execute(self, command):
        if command.command == self.command:
            yield from self._do_execute(command)
            
    # Overwrite this to determine what this CommandType should do with a given Command
    @asyncio.coroutine
    def _do_execute(self, command):
        print('Error: called CommandType._do_execute in the abstract base class.')
        pass

# Abstract base class; a module that can be attached to the Necrobot
class Module(object):
    def __init__(self):
        self.command_types = []

    # Brief information string on what kind of module this is.
    # Overwrite this
    @property
    def infostr(self):
        return 'Unknown module.'

    # Attempts to execute the given command (if a command of its type is in command_types)
    @asyncio.coroutine
    def execute(self, command):
        for cmd_type in self.command_types:
            yield from cmd_type.execute(command)

    # Get the help text for the given command, if a command of its type is in command_list
    # Otherwise, returns None
    def help_text(self, command):
        for cmd_type in self.command_types:
            if cmd_type.command == command.command:
                return cmd_type.help_text
        return None
