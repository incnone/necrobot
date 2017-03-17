# Represents a discord channel on which the bot can read commands. Holds a list of commands the bot will respond to on
# this channel.


class BotChannel(object):
    # necrobot: a necrobot.Necrobot object (the necrobot this is a channel for)
    def __init__(self, necrobot):
        self.necrobot = necrobot
        self.command_types = []     # the list of command.CommandType that can be called on this channel

    def refresh(self, channel):
        pass

    @property
    def client(self):
        return self.necrobot.client

    # Returns whether the user has access to admin commands for this channel
    def is_admin(self, discord_member):
        return self.necrobot.is_admin(discord_member) or self._virtual_is_admin(discord_member)

    # Attempts to execute the given command (if a command of its type is in command_types)
    async def execute(self, command):
        for cmd_type in self.command_types:
            await cmd_type.execute(command)

    # Override to add more admins
    def _virtual_is_admin(self, discord_member):
        return False
