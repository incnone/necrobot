import discord
import sys
import typing

from necrobot.test import msgqueue

from necrobot.util import console

from necrobot.config import Config
from necrobot.botbase.command import Command, TestCommand
from necrobot.botbase.manager import Manager
from necrobot.util.singleton import Singleton


class Necrobot(object, metaclass=Singleton):
    def __init__(self):
        self.client = None                      # type: discord.Client
        self.server = None                      # type: discord.Server

        self._main_discord_channel = None       # type: discord.Channel

        self._pm_bot_channel = None             # The special BotChannel for PM command handling
        self._bot_channels = {}                 # Map discord.Channel -> BotChannel
        self._managers = []                     # type: typing.List[Manager]

        self._initted = False                   # type: bool
        self._quitting = False                  # type: bool
        self._load_config_fn = None             # type: typing.Coroutine

    @property
    def all_channels(self):
        """Get a list of all BotChannels"""
        return self._bot_channels.values()

    @property
    def main_channel(self) -> discord.Channel:
        """Get the bot's "main" discord channel"""
        return self._main_discord_channel if self._main_discord_channel is not None else self.server.default_channel

    @property
    def quitting(self) -> bool:
        """True if the bot wants to quit (i.e. if logout() has been called)"""
        return self._quitting

    @property
    def admin_roles(self) -> typing.List[discord.Role]:
        """A list of all admin roles on the server"""
        admin_roles = []
        for rolename in Config.ADMIN_ROLE_NAMES:
            for role in self.server.roles:
                if role.name == rolename:
                    admin_roles.append(role)
        return admin_roles

    @property
    def staff_role(self) -> typing.Optional[discord.Role]:
        return self.find_role(Config.STAFF_ROLE)

    def clean_init(self):
        self.client = None
        self.server = None
        self._main_discord_channel = None
        self._pm_bot_channel = None
        self._bot_channels.clear()
        self._managers.clear()
        self._initted = False
        self._quitting = False
        self._load_config_fn = None

    def ready_client_events(self, client: discord.Client, load_config_fn, on_ready_fn=None):
        """Set the code for event-handling in the discord.Client"""
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

            if Config.testing():
                await msgqueue.send_message(message)

            if message.author.id == self.client.user.id:
                return

            cmd = Command(message)
            await self._execute(cmd)

        @client.event
        async def on_error(event: str, *args, **kwargs):
            """Called when an event raises an uncaught exception"""
            exc_info = sys.exc_info()
            exc_type = exc_info[0].__name__ if exc_info[0] is not None else '<no exception>'
            exc_what = str(exc_info[1]) if exc_info[1] is not None else ''
            console.error(
                'Uncaught exception {exc_type}: {exc_what}'.format(exc_type=exc_type, exc_what=exc_what)
            )

        # @client.event
        # async def on_member_join(member: discord.Member):
        #     """Called when anyone joins the server"""
        #     if not self._initted:
        #         return
        #
        #     await userdb.register_discord_user(member)
        #
        # @client.event
        # async def on_member_update(member_before: discord.Member, member_after: discord.Member):
        #     """Called when anyone updates their discord profile"""
        #     if not self._initted:
        #         return
        #
        #     if member_before.display_name != member_after.display_name:
        #         await userdb.register_discord_user(member_after)

    def set_main_channel(self, discord_channel: discord.Channel) -> None:
        """Sets the bots "main" channel (returned by main_channel)"""
        self._main_discord_channel = discord_channel

    def get_bot_channel(self, discord_channel):
        """Returns the BotChannel corresponding to the given discord.Channel, if one exists"""
        if discord_channel.is_private:
            return self._pm_bot_channel
        else:
            return self._bot_channels[discord_channel]

    def register_bot_channel(self, discord_channel: discord.Channel, bot_channel) -> None:
        """Register a BotChannel"""
        self._bot_channels[discord_channel] = bot_channel
        for mgr in self._managers:
            mgr.on_botchannel_create(discord_channel, bot_channel)

    def unregister_bot_channel(self, discord_channel: discord.Channel) -> None:
        """Unegister a BotChannel"""
        del self._bot_channels[discord_channel]

    def register_pm_channel(self, pm_bot_channel) -> None:
        """Register a BotChannel for PMs"""
        self._pm_bot_channel = pm_bot_channel

    def register_manager(self, manager: Manager) -> None:
        """Register a manager"""
        console.info('Registering a manager of type {0}.'.format(type(manager).__name__))
        self._managers.append(manager)

    def is_admin(self, user: discord.User) -> bool:
        """True if user is a server admin"""
        member = self.get_as_member(user)
        for role in member.roles:
            if role in self.admin_roles:
                return True
        return False

    def find_channel(self, channel_name) -> typing.Optional[discord.Channel]:
        """Returns the channel with the given name on the server, if any"""
        for channel in self.server.channels:
            if channel.name == channel_name:
                return channel
        return None

    def find_channel_with_id(self, channel_id) -> typing.Optional[discord.Channel]:
        """Returns the channel with the given ID on the server, if any"""
        for channel in self.server.channels:
            if int(channel.id) == int(channel_id):
                return channel
        return None

    def find_admin(self, ignore=list()) -> typing.Optional[discord.Member]:
        """Returns a random bot admin (for testing purposes)"""
        for member in self.server.members:
            if member.display_name in ignore or member.id == self.client.user.id:
                continue
            for role in member.roles:
                if role in self.admin_roles:
                    return member
        return None

    def find_member(self, discord_name=None, discord_id=None) -> typing.Optional[discord.Member]:
        """Returns a member with a given username (capitalization ignored)"""
        if discord_name is None and discord_id is None:
            return None

        if discord_name is not None:
            for member in self.server.members:
                if member.display_name.lower() == discord_name.lower() \
                        or member.name.lower() == discord_name.lower():
                    return member
        elif discord_id is not None:
            for member in self.server.members:
                if int(member.id) == int(discord_id):
                    return member

    def find_members(self, username) -> typing.List[discord.Member]:
        """Returns a list of all members with a given username (capitalization ignored)"""
        to_return = []
        for member in self.server.members:
            if member.display_name.lower() == username.lower():
                to_return.append(member)
        return to_return

    def get_as_member(self, user) -> typing.Optional[discord.Member]:
        """Returns the given Discord user as a member of the server"""
        for member in self.server.members:
            if int(member.id) == int(user.id):
                return member
        return None

    def find_role(self, role_name: str) -> typing.Optional[discord.Role]:
        """Finds a discord.Role with the given name, if any"""
        for role in self.server.roles:
            if role.name.lower() == role_name.lower():
                return role
        return None

    async def post_login_init(
        self,
        client: discord.Client,
        server_id: int,
        load_config_fn
    ) -> None:
        """Initializes object; call after client has been logged in to discord"""
        self.client = client
        self._load_config_fn = load_config_fn

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
            console.warning('Could not find the server.')
            exit(1)

        if not self._initted:
            await self._load_config_fn(self)
            self._initted = True
            for manager in self._managers:
                await manager.initialize()
        else:
            await self.refresh()

        console.info(
            '\n'
            '-Logged in---------------\n'
            '   User name: {0}\n'
            ' Server name: {1}\n'
            '-------------------------'.format(self.server.me.display_name, self.server.name)
        )

    async def redo_init(self) -> None:
        """Forcibly re-calls the post_login_init method"""
        await self.post_login_init(self.client, self.server.id, self._load_config_fn)

    async def refresh(self) -> None:
        """Called when post_login_init() is run a second+ time"""
        channel_pairs = {}
        for channel, bot_channel in self._bot_channels.items():
            new_channel = self.find_channel_with_id(channel.id)
            if new_channel is not None:
                channel_pairs[new_channel] = bot_channel
            bot_channel.refresh(new_channel)
        self._bot_channels = channel_pairs

        for manager in self._managers:
            await manager.refresh()

    async def cleanup(self) -> None:
        """Called on shutdown"""
        for manager in self._managers:
            await manager.close()

    async def logout(self) -> None:
        """Log out of discord"""
        self._quitting = True
        await self.cleanup()
        await self.client.logout()

    async def reboot(self) -> None:
        """Log out of discord without cleaning up or setting self._quitting flag"""
        await self.cleanup()
        await self.client.logout()

    async def force_command(self, channel: discord.Channel, author: discord.Member, message_str: str) -> None:
        """Causes the bot to act as if the given author had posted the given message in the given channel, and
        reacts to it as if it were a command.
        
        Warning: This won't work on commands that depend specifically on the discord.Message object, since
        TestCommand cannot fake such an object.
        """
        await self._execute(TestCommand(channel=channel, author=author, message_str=message_str))

    async def _execute(self, cmd) -> None:
        """Execute a command"""
        # Don't care about bad commands
        if cmd.command is None:
            return

        # Handle the command with the appropriate BotChannel
        if cmd.is_private:
            await self._pm_bot_channel.execute(cmd)
        elif cmd.channel in self._bot_channels:
            await self._bot_channels[cmd.channel].execute(cmd)
