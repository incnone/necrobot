import asyncio
import discord

from necrobot.util import console

from necrobot.botbase.command import Command
from necrobot.botbase.necrobot import Necrobot
from necrobot.config import Config, TestLevel


class CommandType(object):
    execution_id = 0
    execution_id_lock = asyncio.Lock()

    """Abstract base class; a particular command that the bot can interpret, and how to interpret it.
    (For instance, racemodule has a CommandType object called make, for the `.make` command.)
    """
    def __init__(self, bot_channel, *args):
        self.command_name_list = args               # the string that calls this command (e.g. 'make')
        self.help_text = 'This command has no help text.'
        self.admin_only = False                     # If true, only botchannel admins can call this command
        self.testing_command = False                # If true, can only be called if Config.TESTING is not RUN
        self.bot_channel = bot_channel

    @property
    def show_in_help(self) -> bool:
        return not self.testing_command or Config.TESTING <= TestLevel.TEST

    @property
    def client(self) -> discord.Client:
        return self.necrobot.client

    @property
    def necrobot(self) -> Necrobot:
        return self.bot_channel.necrobot

    @property
    def mention(self) -> str:
        return Config.BOT_COMMAND_PREFIX + self.command_name

    @property
    def command_name(self) -> str:
        return str(self.command_name_list[0])

    @property
    def short_help_text(self) -> str:
        """Help text for `.help verbose` calls."""
        if len(self.help_text) > 50:
            return '{0}...'.format(self.help_text[:50].replace('`', ''))
        else:
            return self.help_text

    def called_by(self, name: str) -> bool:
        """
        Parameters
        ----------
        name: str

        Returns
        -------
        bool
            True if the given name can be used to call this command.
        """
        return name in self.command_name_list

    async def execute(self, command: Command):
        """If the Command's command is this object's command, calls the (virtual) method _do_execute on it
        
        Parameters
        ----------
        command: Command
            The command to maybe execute.
        """
        if command.command in self.command_name_list \
                and ((not self.admin_only) or self.bot_channel.is_admin(command.author)) \
                and (not self.testing_command or Config.TESTING <= TestLevel.TEST):
            async with self.execution_id_lock:
                self.execution_id += 1
                this_id = self.execution_id

            console.info(
                'Call {0}: <ID={1}> <Caller={2}> <Channel={3}> <Message={4}>'.format(
                    type(self).__name__,
                    this_id,
                    command.author.name,
                    command.channel.name,
                    command.content
                )
            )
            await self._do_execute(command)
            console.info('Exit {0}: <ID={1}>'.format(type(self).__name__, this_id))

    async def _do_execute(self, command: Command):
        """Pure virtual: determine what this CommandType should do with a given Command.
        
        Parameters
        ----------
        command: Command
            The Command that was called, to be executed.
        """
        console.error('Called CommandType._do_execute in the abstract base class.')
