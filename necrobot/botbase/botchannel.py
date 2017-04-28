import discord

from necrobot.botbase import cmd_all
from necrobot.botbase.necrobot import Necrobot

# Represents a discord channel on which the bot can read commands. Holds a list of commands the bot will respond to on
# this channel.


class BotChannel(object):
    def __init__(self):
        self.channel_commands = []     # the list of command.CommandType that can be called on this BotChannel
        self.default_commands = [
            cmd_all.ForceCommand(self),
            cmd_all.Help(self),
            cmd_all.Info(self),
        ]

    @property
    def client(self) -> discord.Client:
        return Necrobot().client

    @property
    def necrobot(self) -> Necrobot:
        return Necrobot()

    @property
    def all_commands(self):
        return self.channel_commands + self.default_commands

    def refresh(self, channel):
        pass

    # Returns whether the user has access to admin commands for this necrobot
    def is_admin(self, discord_member) -> bool:
        return self.necrobot.is_admin(discord_member) or self._virtual_is_admin(discord_member)

    # Override to add more admins
    def _virtual_is_admin(self, discord_member) -> bool:
        return False

    # Attempts to execute the given command (if a command of its type is in channel_commands)
    async def execute(self, command) -> None:
        for cmd_type in self.channel_commands:
            await cmd_type.execute(command)
        for cmd_type in self.default_commands:
            await cmd_type.execute(command)
