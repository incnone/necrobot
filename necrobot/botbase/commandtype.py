import asyncio
import discord

from necrobot.util import server
from necrobot.util import console

from necrobot.botbase.command import Command
from necrobot.botbase.necrobot import Necrobot
from necrobot.config import Config


class CommandType(object):
    """Abstract base class; a particular command that the bot can interpret, and how to interpret it.
    (For instance, racemodule has a CommandType object called make, for the `.make` command.)
    """
    execution_id = 0
    execution_id_lock = asyncio.Lock()

    def __init__(self, bot_channel, *args):
        self.command_name_list = args               # the string that calls this command (e.g. 'make')
        self.help_text = 'This command has no help text.'
        self.admin_only = False                     # If true, only botchannel admins can call this command
        self.testing_command = False                # If true, can only be called if Config.TESTING is not RUN
        self.bot_channel = bot_channel

    @property
    def show_in_help(self) -> bool:
        """If False, this command type will not show up in the .help list"""
        return not self.testing_command or Config.testing()

    @property
    def client(self) -> discord.Client:
        return server.client

    @property
    def necrobot(self) -> Necrobot:
        return Necrobot()

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

    async def execute(self, command: Command) -> None:
        """If the Command's command is this object's command, calls the (virtual) method _do_execute on it
        
        Parameters
        ----------
        command: Command
            The command to maybe execute.
        """
        if command.command in self.command_name_list \
                and ((not self.admin_only) or self.bot_channel.is_admin(command.author)) \
                and (not self.testing_command or Config.testing()):
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

            try:
                await self._do_execute(command)
                console.info('Exit {0}: <ID={1}>'.format(type(self).__name__, this_id))
            except Exception as e:
                console.warning(
                    'Error exiting {name} <ID={id}>: {error_msg}'.format(
                        name=type(self).__name__,
                        id=this_id,
                        error_msg=repr(e)
                    )
                )
                asyncio.ensure_future(self.client.send_message(
                    command.channel,
                    "Unexpected error while executing command `{mention}`.".format(mention=self.mention)
                ))
                raise

    async def reparse_as(self, new_name: str, command: Command) -> None:
        """Make the bot channel re-execute the given Command with a different command name
        
        Parameters
        ----------
        new_name: str
            The new name to assign to the command
        command: Command
            The command to be reinterpreted
        """
        command.command = new_name
        await self.bot_channel.execute(command)

    async def _do_execute(self, command: Command) -> None:
        """Pure virtual: determine what this CommandType should do with a given Command.
        
        Parameters
        ----------
        command: Command
            The Command that was called, to be executed.
        """
        console.warning('Called CommandType._do_execute in the abstract base class.')
