import discord

from necrobot.database import dbutil
from necrobot.util import console
from necrobot.util.config import Config


class Necrobot(object):
    instance = None

    def __init__(self):
        if Necrobot.instance is None:
            Necrobot.instance = Necrobot.__Necrobot()

    def __getattr__(self, name):
        return getattr(Necrobot.instance, name)

    class __Necrobot(object):
        # Ctor
        def __init__(self):
            self.client = None                      # the discord.Client object
            self.server = None                      # the discord.Server on which to read commands

            self._pm_bot_channel = None
            self._bot_channels = {}                 # maps discord.Channels onto BotChannels
            self._managers = {}                     # these get refresh() and close() called on them

            self._initted = False
            self._quitting = False

        # Initializes object; call after client has been logged in to discord
        async def post_login_init(self, client, server_id, load_config_fn):
            self.client = client

            # Find the correct server
            try:
                int(server_id)
                id_is_int = True
            except ValueError:
                id_is_int = False

            for s in self.client.servers:
                if id_is_int and s.id == server_id:
                    self.server = s
                elif s.name == server_id:
                    self.server = s

            if self.server is None:
                console.error('Could not find the server.')
                exit(1)

            if not self._initted:
                await load_config_fn(self)
                self._initted = True
            else:
                self.refresh()

            console.info(
                '-Logged in---------------\n'
                '   User name: {0}\n'
                ' Server name: {1}\n'
                '-------------------------'.format(self.server.me.display_name, self.server.name)
            )

        # Called when post_login_init() is run a second+ time
        def refresh(self):
            channel_pairs = {}
            for channel, bot_channel in self._bot_channels.items():
                new_channel = self.find_channel_with_id(channel.id)
                if new_channel is not None:
                    channel_pairs[new_channel] = bot_channel
                bot_channel.refresh(new_channel)
            self._bot_channels = channel_pairs

            for manager in self._managers.values():
                manager.refresh()

        # Called on shutdown
        def cleanup(self):
            for manager in self._managers.values():
                manager.close()
            self._bot_channels.clear()

        # Returns the BotChannel corresponding to the given discord.Channel, if one exists
        def get_bot_channel(self, discord_channel):
            if discord_channel.is_private:
                return self._pm_bot_channel
            else:
                return self._bot_channels[discord_channel]

        # Registration of bot channels
        def register_bot_channel(self, discord_channel, bot_channel):
            self._bot_channels[discord_channel] = bot_channel

        def unregister_bot_channel(self, discord_channel):
            del self._bot_channels[discord_channel]

        def register_pm_channel(self, pm_bot_channel):
            self._pm_bot_channel = pm_bot_channel

        # Registration of managers
        def register_manager(self, name, manager):
            self._managers[name] = manager

        def unregister_manager(self, name):
            del self._managers[name]

        def get_manager(self, name):
            return self._managers[name]

        # True if the bot wants to quit (i.e. if logout() has been called)
        @property
        def quitting(self):
            return self._quitting

        # A list of all admin roles on the server
        @property
        def admin_roles(self):
            admin_roles = []
            for rolename in Config.ADMIN_ROLE_NAMES:
                for role in self.server.roles:
                    if role.name == rolename:
                        admin_roles.append(role)
            return admin_roles

        # True if the dicord.User is a server admin
        def is_admin(self, user):
            member = self.get_as_member(user)
            admin_roles = self.admin_roles
            for role in member.roles:
                if role in admin_roles:
                    return True
            return False

        # Returns the channel with the given name on the server, if any
        def find_channel(self, channel_name):
            for channel in self.server.channels:
                if channel.name == channel_name:
                    return channel
            return None

        # Returns the channel with the given ID on the server, if any
        def find_channel_with_id(self, channel_id):
            for channel in self.server.channels:
                if int(channel.id) == int(channel_id):
                    return channel
            return None

        # Returns a member with a given username (capitalization ignored)
        def find_member(self, discord_name=None, discord_id=None):
            if discord_name is None and discord_id is None:
                return None

            if discord_name is not None:
                for member in self.server.members:
                    if member.display_name.lower() == discord_name.lower():
                        return member
            elif discord_id is not None:
                for member in self.server.members:
                    if int(member.id) == int(discord_id):
                        return member

        # Returns a list of all members with a given username (capitalization ignored)
        def find_members(self, username):
            to_return = []
            for member in self.server.members:
                if member.display_name.lower() == username.lower():
                    to_return.append(member)
            return to_return

        # Returns the given Discord user as a member of the server
        def get_as_member(self, user):
            for member in self.server.members:
                if int(member.id) == int(user.id):
                    return member

    # Coroutines--------------------
        # Log out of discord
        async def logout(self):
            self._quitting = True
            await self.client.logout()

        # Log out of discord, but do not set quitting flag
        async def reboot(self):
            await self.client.logout()

        # Called when anyone joins the server
        @staticmethod
        async def on_member_join(user: discord.User):
            dbutil.register_discord_user(user)

        # Executes a command
        async def execute(self, cmd):
            # Don't execute before init
            if not self._initted:
                return

            # Don't care about bad commands
            if cmd.command is None:
                return

            # Don't reply to self
            if cmd.author == self.client.user:
                return

            # Handle the command with the appropriate BotChannel
            if cmd.is_private:
                await self._pm_bot_channel.execute(cmd)
            elif cmd.channel in self._bot_channels:
                await self._bot_channels[cmd.channel].execute(cmd)
