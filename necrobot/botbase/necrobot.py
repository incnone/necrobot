import discord
import sys
from typing import Callable, List, Optional, Union

from necrobot.test import msgqueue

from necrobot.util import server
from necrobot.util import console

# from necrobot.botbase.botchannel import BotChannel
from necrobot.config import Config
from necrobot.botbase.command import Command, TestCommand
from necrobot.botbase.manager import Manager
from necrobot.util.singleton import Singleton


class Necrobot(object, metaclass=Singleton):
    def __init__(self):
        self._pm_bot_channel = None  # .. type: BotChannel
        self._bot_channels = dict()  # .. type: Dict[discord.TextChannel, BotChannel]
        self._managers = list()  # type: List[Manager]

        self._initted = False  # type: bool
        self._load_config_fn = None  # type: Optional[Callable[[], None]]

    @property
    def client(self) -> discord.Client:
        return server.client

    @property
    def server(self) -> discord.Guild:
        return server.guild

    @property
    def all_channels(self):  # -> ValuesView[BotChannel]:
        """Get a list of all BotChannels"""
        return self._bot_channels.values()

    def clean_init(self) -> None:
        self._pm_bot_channel = None
        self._bot_channels.clear()
        self._managers.clear()
        self._initted = False
        self._load_config_fn = None

    def get_bot_channel(self, discord_channel: Union[discord.TextChannel, discord.DMChannel]):  # -> BotChannel:
        """Returns the BotChannel corresponding to the given discord.Channel, if one exists"""
        if isinstance(discord_channel, discord.DMChannel):
            return self._pm_bot_channel
        else:
            return self._bot_channels[discord_channel]

    def register_bot_channel(self, discord_channel: discord.TextChannel, bot_channel) -> None:
        """Register a BotChannel"""
        self._bot_channels[discord_channel] = bot_channel
        for mgr in self._managers:
            mgr.on_botchannel_create(discord_channel, bot_channel)

    def unregister_bot_channel(self, discord_channel: discord.TextChannel) -> None:
        """Unegister a BotChannel"""
        del self._bot_channels[discord_channel]

    def register_pm_channel(self, pm_bot_channel) -> None:
        """Register a BotChannel for PMs"""
        self._pm_bot_channel = pm_bot_channel

    def register_manager(self, manager: Manager) -> None:
        """Register a manager"""
        console.info('Registering a manager of type {0}.'.format(type(manager).__name__))
        self._managers.append(manager)

    async def post_login_init(
            self,
            client: discord.Client,
            server_id: int,
            load_config_fn
    ) -> None:
        """Initializes object; call after client has been logged in to discord"""
        self._load_config_fn = load_config_fn

        # Find the correct server
        the_guild = None  # type: Optional[discord.Guild]
        for s in client.guilds:
            if s.id == server_id:
                the_guild = s

        if the_guild is None:
            console.warning('Could not find guild with ID {guild_id}.'.format(guild_id=server_id))
            exit(1)

        server.init(client, the_guild)

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
            '-------------------------'.format(the_guild.me.display_name, the_guild.name)
        )

    async def redo_init(self) -> None:
        """Forcibly re-calls the post_login_init method"""
        await self.post_login_init(self.client, self.server.id, self._load_config_fn)

    async def refresh(self) -> None:
        """Called when post_login_init() is run a second+ time"""
        channel_pairs = {}
        for channel, bot_channel in self._bot_channels.items():
            new_channel = server.find_channel(channel_id=channel.id)
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
        await self.cleanup()
        await self.client.logout()

    # async def reboot(self) -> None:
    #     await self.cleanup()
    #     await self.client.logout()

    async def force_command(self, channel: discord.TextChannel, author: discord.Member, message_str: str) -> None:
        """Causes the bot to act as if the given author had posted the given message in the given channel, and
        reacts to it as if it were a command.
        
        Warning: This won't work on commands that depend specifically on the discord.Message object, since
        TestCommand cannot fake such an object.
        """
        await self._execute(TestCommand(channel=channel, author=author, message_str=message_str))

    async def _execute(self, cmd: Command) -> None:
        """Execute a command"""
        # Don't care about bad commands
        if cmd.command is None:
            return

        # Handle the command with the appropriate BotChannel
        if cmd.is_private:
            await self._pm_bot_channel.execute(cmd)
        elif cmd.channel in self._bot_channels:
            await self._bot_channels[cmd.channel].execute(cmd)

    def ready_client_events(
            self,
            client: discord.Client,
            load_config_fn: Callable[[], None],
            on_ready_fn: Callable[[], None] = None
    ):
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

        # noinspection PyUnusedLocal
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
