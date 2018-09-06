"""
Represents a discord channel on which the bot can read commands. Holds a list of commands the bot will respond to on
this channel.
"""

import discord

from necrobot.botbase import cmd_all
from necrobot.util import server


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
        return server.client

    @property
    def all_commands(self):
        return self.channel_commands + self.default_commands

    def refresh(self, channel: discord.Channel) -> None:
        """Called on Necrobot.refresh()
        
        Parameters
        ----------
        channel
            The discord.Channel that now points to this BotChannel
        """
        pass

    def is_admin(self, discord_member: discord.Member) -> bool:
        """Whether the user can access admin commands for this channel"""
        return server.is_admin(discord_member) or self._virtual_is_admin(discord_member)

    async def execute(self, command) -> None:
        """Attempts to execute the given command (if a command of its type is in channel_commands)"""
        for cmd_type in self.channel_commands:
            await cmd_type.execute(command)
        for cmd_type in self.default_commands:
            await cmd_type.execute(command)

    def _virtual_is_admin(self, discord_member: discord.Member) -> bool:
        """Override this to add channel-specific admins."""
        return False
