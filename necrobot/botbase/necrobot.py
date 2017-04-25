import discord

from necrobot.test import msgqueue

from necrobot.database import dbutil
from necrobot.util import console
from necrobot.config import Config, TestLevel
from necrobot.botbase.command import Command, TestCommand


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

        # Events
        def ready_client_events(self, client: discord.Client, load_config_fn, on_ready_fn=None):
            @client.event
            async def on_ready():
                """Called after the client has successfully logged in"""
                await self.post_login_init(
                    client=client,
                    server_id=Config.SERVER_ID,
                    load_config_fn=load_config_fn
                )
                if on_ready_fn is not None:
                    await on_ready_fn(self)

            @client.event
            async def on_message(message: discord.Message):
                """Called whenever a new message is posted in any channel on any server"""
                if not self._initted:
                    return

                cmd = Command(message)
                await self._execute(cmd)

                if Config.TESTING <= TestLevel.TEST:
                    await msgqueue.send_message(message)

            @client.event
            async def on_member_join(member: discord.Member):
                """Called when anyone joins the server"""
                if not self._initted:
                    return

                dbutil.register_discord_user(member)

            @client.event
            async def on_member_update(member_before: discord.Member, member_after: discord.Member):
                """Called when anyone updates their discord profile"""
                if not self._initted:
                    return

                if member_before.display_name != member_after.display_name:
                    dbutil.register_discord_user(member_after)

        async def post_login_init(
            self,
            client: discord.Client,
            server_id: int,
            load_config_fn
        ):
            """Initializes object; call after client has been logged in to discord"""
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
                '\n'
                '-Logged in---------------\n'
                '   User name: {0}\n'
                ' Server name: {1}\n'
                '-------------------------'.format(self.server.me.display_name, self.server.name)
            )

        def refresh(self):
            """Called when post_login_init() is run a second+ time"""
            channel_pairs = {}
            for channel, bot_channel in self._bot_channels.items():
                new_channel = self.find_channel_with_id(channel.id)
                if new_channel is not None:
                    channel_pairs[new_channel] = bot_channel
                bot_channel.refresh(new_channel)
            self._bot_channels = channel_pairs

            for manager in self._managers.values():
                manager.refresh()

        def cleanup(self):
            """Called on shutdown"""
            for manager in self._managers.values():
                manager.close()
            self._bot_channels.clear()

        def get_bot_channel(self, discord_channel):
            """Returns the BotChannel corresponding to the given discord.Channel, if one exists"""
            if discord_channel.is_private:
                return self._pm_bot_channel
            else:
                return self._bot_channels[discord_channel]

        def register_bot_channel(self, discord_channel: discord.Channel, bot_channel):
            """Register a BotChannel"""
            self._bot_channels[discord_channel] = bot_channel

        def unregister_bot_channel(self, discord_channel: discord.Channel):
            """Unegister a BotChannel"""
            del self._bot_channels[discord_channel]

        def register_pm_channel(self, pm_bot_channel):
            """Register a BotChannel for PMs"""
            self._pm_bot_channel = pm_bot_channel

        def register_manager(self, name, manager):
            """Register a manager"""
            self._managers[name] = manager

        def unregister_manager(self, name):
            """Unegister a manager"""
            del self._managers[name]

        def get_manager(self, name):
            """Get a manager"""
            return self._managers[name]

        @property
        def quitting(self):
            """True if the bot wants to quit (i.e. if logout() has been called)"""
            return self._quitting

        @property
        def admin_roles(self):
            """A list of all admin roles on the server"""
            admin_roles = []
            for rolename in Config.ADMIN_ROLE_NAMES:
                for role in self.server.roles:
                    if role.name == rolename:
                        admin_roles.append(role)
            return admin_roles

        def is_admin(self, user: discord.User):
            """True if user is a server admin"""
            member = self.get_as_member(user)
            for role in member.roles:
                if role in self.admin_roles:
                    return True
            return False

        def find_channel(self, channel_name):
            """Returns the channel with the given name on the server, if any"""
            for channel in self.server.channels:
                if channel.name == channel_name:
                    return channel
            return None

        def find_channel_with_id(self, channel_id):
            """Returns the channel with the given ID on the server, if any"""
            for channel in self.server.channels:
                if int(channel.id) == int(channel_id):
                    return channel
            return None

        def find_admin(self, ignore=list()):
            """Returns a random bot admin (for testing purposes)"""
            for member in self.server.members:
                if member.display_name in ignore:
                    continue
                for role in member.roles:
                    if role in self.admin_roles:
                        return member
            return None

        def find_member(self, discord_name=None, discord_id=None):
            """Returns a member with a given username (capitalization ignored)"""
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

        def find_members(self, username):
            """Returns a list of all members with a given username (capitalization ignored)"""
            to_return = []
            for member in self.server.members:
                if member.display_name.lower() == username.lower():
                    to_return.append(member)
            return to_return

        def get_as_member(self, user):
            """Returns the given Discord user as a member of the server"""
            for member in self.server.members:
                if int(member.id) == int(user.id):
                    return member

        def find_role(self, role_name: str) -> discord.Role or None:
            """Finds a discord.Role with the given name, if any"""
            for role in self.server.roles:
                if role.name.lower() == role_name.lower():
                    return role
            return None

        # Coroutines--------------------
        async def logout(self):
            """Log out of discord"""
            self._quitting = True
            await self.client.logout()

        async def reboot(self):
            """Log out of discord without setting self._quitting flag"""
            await self.client.logout()

        async def _execute(self, cmd):
            """Execute a command"""
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

        async def force_command(self, channel: discord.Channel, author: discord.Member, message_str: str):
            await self._execute(TestCommand(channel=channel, author=author, message_str=message_str))
