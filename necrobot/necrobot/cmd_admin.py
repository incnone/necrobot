from necrobot.botbase.command import CommandType
from necrobot.util.config import Config


class Die(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'die')
        self.help_text = 'Tell the bot to log out. [Admin only]'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await self.necrobot.logout()


class Help(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'help')
        self.help_text = 'Help.'

    async def _do_execute(self, command):
        if len(command.args) == 0:
            command_list_text = ''
            for cmd_type in self.bot_channel.command_types:
                if (not cmd_type.secret_command) \
                        and (not cmd_type.admin_only or self.bot_channel.is_admin(command.author)):
                    command_list_text += '`' + cmd_type.mention + '`, '
            command_list_text = command_list_text[:-2]
            await self.necrobot.client.send_message(
                command.channel,
                'Available commands in this necrobot: {0}\n\nType `{1} <command>` for more info about a particular '
                'command.'.format(command_list_text, self.mention))
        elif len(command.args) == 1:
            for cmd_type in self.bot_channel.command_types:
                if cmd_type.called_by(command.args[0]):
                    await self.necrobot.client.send_message(
                        command.channel, '`{0}`: {1}'.format(cmd_type.mention, cmd_type.help_text))
            return None


class Info(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'info')
        self.help_text = "Necrobot version information."

    async def _do_execute(self, cmd):
        await self.bot_channel.client.send_message(
            cmd.channel,
            'Necrobot v-{0} (alpha). Type `.help` for a list of commands.'.format(Config.BOT_VERSION))


class Reboot(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'reboot')
        self.help_text = 'Reboot the necrobot. [Admin only]'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await self.necrobot.reboot()


class Register(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register')
        self.help_text = 'Register your current Discord name as the name to use for the bot.'

    async def _do_execute(self, cmd):
        self.necrobot.register_user(cmd.author)
        await self.necrobot.client.send_message(cmd.channel, 'Registered your name as {0}.'.format(cmd.author.mention))


class RegisterAll(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'registerall')
        self.help_text = 'Register all unregistered users. [Admin only]'
        self.admin_only = True

    async def _do_execute(self, cmd):
        self.necrobot.register_all_users()
        await self.necrobot.client.send_message(cmd.channel, 'Registered all unregistered users.')


class RedoInit(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'redoinit')
        self.help_text = 'Call Necrobot\'s post_login_init method. [Admin only]'
        self.admin_only = True

    async def _do_execute(self, cmd):
        self.necrobot.post_login_init(self.necrobot.server.id)
