import discord
import shlex

from necrobot.config import Config


class Command(object):
    """Represents a full user command input (e.g. `.make -c Cadence -seed 12345 -custom 4-shrine`)"""
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
    def author(self) -> discord.User or discord.Member:
        return self.message.author if self.message else None

    @property
    def server(self) -> discord.Server:
        return self.message.server if self.message else None

    @property
    def channel(self) -> discord.Channel:
        return self.message.channel if self.message else None

    @property
    def is_private(self) -> bool:
        return self.message.channel.is_private if self.message else None

    @property
    def arg_string(self) -> str:
        cut_len = len(Config.BOT_COMMAND_PREFIX) + len(self.command) + 1
        return self.message.content[cut_len:]
