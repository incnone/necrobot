import discord
from .necrobot import Necrobot

# Represents a discord channel on which the bot can read commands. Holds a list of commands the bot will respond to on
# this necrobot.


class BotChannel(object):
    # necrobot: a necrobot.Necrobot object (the necrobot this is a necrobot for)
    def __init__(self):
        self.command_types = []     # the list of command.CommandType that can be called on this necrobot

    def refresh(self, channel):
        pass

    @property
    def client(self) -> discord.Client:
        return Necrobot().client

    @property
    def necrobot(self) -> Necrobot:
        return Necrobot()

    # Returns whether the user has access to admin commands for this necrobot
    def is_admin(self, discord_member) -> bool:
        return self.necrobot.is_admin(discord_member) or self._virtual_is_admin(discord_member)

    # Override to add more admins
    def _virtual_is_admin(self, discord_member) -> bool:
        return False

    # Attempts to execute the given command (if a command of its type is in command_types)
    async def execute(self, command):
        for cmd_type in self.command_types:
            await cmd_type.execute(command)
