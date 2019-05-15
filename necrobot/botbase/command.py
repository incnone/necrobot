import discord
import shlex
from typing import List, Optional, Union

from necrobot.config import Config


class Command(object):
    """Represents a full user command input (e.g. `.make -c Cadence -seed 12345 -custom 4-shrine`)"""
    def __init__(self, message: discord.Message):
        self.command = None         # type: Optional[str]
        self.args = []              # type: List[str]
        self._message = message     # type: discord.Message
        self._arg_string = ''       # type: str

        if message is None:
            return

        if message.content.startswith(Config.BOT_COMMAND_PREFIX):
            try:
                self.args = shlex.split(message.content)
            except ValueError:
                self.args = message.content.split()
            prefix_len = len(Config.BOT_COMMAND_PREFIX)
            self.command = (self.args.pop(0)[prefix_len:]).lower()
            cut_len = len(Config.BOT_COMMAND_PREFIX) + len(self.command) + 1
            self._arg_string = self._message.content[cut_len:].strip(' ')

    @property
    def author(self) -> discord.User or discord.Member:
        return self._message.author

    @property
    def server(self) -> Optional[discord.Guild]:
        return self._message.guild

    @property
    def channel(self) -> discord.TextChannel:
        return self._message.channel

    @property
    def is_private(self) -> bool:
        return isinstance(self.channel, discord.abc.PrivateChannel)

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
        self.args = []                      # type: List[str]
        self._author = author               # type: Union[discord.User, discord.Member]
        self._channel = channel             # type: discord.TextChannel
        self._message_str = message_str     # type: str

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
    def server(self) -> Optional[discord.Guild]:
        return self._channel.guild

    @property
    def channel(self) -> discord.TextChannel:
        return self._channel

    @property
    def is_private(self) -> bool:
        return isinstance(self._channel, discord.abc.PrivateChannel)

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
