import discord
import shlex

from necrobot.config import Config


class Command(object):
    """Represents a full user command input (e.g. `.make -c Cadence -seed 12345 -custom 4-shrine`)"""
    def __init__(self, message: discord.Message):
        self.command = None
        self.args = []      
        self._message = message
        cut_len = len(Config.BOT_COMMAND_PREFIX) + len(self.command) + 1
        self._arg_string = self._message.content[cut_len:].strip(' ')

        if message is None:
            return

        if message.content.startswith(Config.BOT_COMMAND_PREFIX):
            try:
                self.args = shlex.split(message.content)
            except ValueError:
                self.args = message.content.split()
            prefix_len = len(Config.BOT_COMMAND_PREFIX)
            self.command = (self.args.pop(0)[prefix_len:]).lower()

    @property
    def author(self) -> discord.User or discord.Member:
        return self._message.author

    @property
    def server(self) -> discord.Server:
        return self._message.server

    @property
    def channel(self) -> discord.Channel:
        return self._message.channel

    @property
    def is_private(self) -> bool:
        return self.channel.is_private

    @property
    def content(self) -> str:
        return self._message.content

    @property
    def message(self):
        """Avoid calling this unless absolutely necessary, since it can't be faked by TestCommand."""
        return self._message

    @property
    def arg_string(self) -> str:
        return self._arg_string


class TestCommand(Command):
    """Fakes a Command object"""
    def __init__(self, channel, author, message_str):
        # noinspection PyTypeChecker
        Command.__init__(self, message=None)

        self.command = None
        self.args = []
        self._author = author
        self._channel = channel
        self._message_str = message_str

        if message_str.startswith(Config.BOT_COMMAND_PREFIX):
            try:
                self.args = shlex.split(message_str)
            except ValueError:
                self.args = message_str.split()
            prefix_len = len(Config.BOT_COMMAND_PREFIX)
            self.command = (self.args.pop(0)[prefix_len:]).lower()

    @property
    def author(self) -> discord.User or discord.Member:
        return self._author

    @property
    def server(self) -> discord.Server:
        return self._channel.server

    @property
    def channel(self) -> discord.Channel:
        return self._channel

    @property
    def is_private(self) -> bool:
        return self._channel.is_private

    @property
    def content(self) -> str:
        return self._message_str

    @property
    def message(self):
        return None

    @property
    def arg_string(self) -> str:
        cut_len = len(Config.BOT_COMMAND_PREFIX) + len(self.command) + 1
        return self.content[cut_len:]
