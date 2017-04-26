from necrobot.botbase.commandtype import CommandType
from necrobot.config import Config


class ForceCommand(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'force')
        self.help_text = '`{0} user command`: Simulate the user entering the given command in the current channel.' \
            .format(self.mention)
        self.testing_command = True
        self.admin_only = True

    @property
    def show_in_help(self):
        return False

    async def _do_execute(self, cmd):
        if len(cmd.args) < 2:
            await self.client.send_message(
                cmd.channel,
                'Not enough arguments for `{0}`.'.format(self.mention)
            )
            return

        username = cmd.args[0]
        user = self.necrobot.find_member(discord_name=username)
        if user is None:
            await self.client.send_message(
                cmd.channel,
                "Couldn't find the user `{0}`.".format(username)
            )
            return

        message_content = cmd.arg_string[(len(username) + 1):]
        await self.necrobot.force_command(channel=cmd.channel, author=user, message_str=message_content)


class Help(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'help')
        self.help_text = 'Help.'

    @property
    def show_in_help(self):
        return False

    async def _do_execute(self, cmd):
        args = cmd.args
        # List commands
        if len(args) == 0:
            command_list_text = ''
            cmds_to_show = []
            for cmd_type in self.bot_channel.all_commands:
                if cmd_type.show_in_help \
                        and (not cmd_type.admin_only or self.bot_channel.is_admin(cmd.author)) \
                        and (not cmd_type.testing_command or Config.testing()):
                    cmds_to_show.append(cmd_type)

            if not cmds_to_show:
                await self.client.send_message(
                    cmd.channel,
                    'No commands available in this channel.'
                )
                return

            cmds_to_show = sorted(
                cmds_to_show,
                key=lambda c: ('_' if not c.admin_only else '') + c.command_name
            )
            cutoff = 1900 // len(cmds_to_show)
            for cmd_type in cmds_to_show:
                this_cmd_text = '\n`{2}{0}` -- {1}'.format(
                    cmd_type.mention,
                    cmd_type.short_help_text,
                    '[A] ' if cmd_type.admin_only else ''
                )
                command_list_text += this_cmd_text[:cutoff]

            await self.client.send_message(
                cmd.channel,
                'Command list: {0}\n\nUse `{1} command` for more info about a '
                'particular command.'.format(command_list_text, self.mention)
            )

        # Get help text for a particular command
        elif len(args) == 1:
            for cmd_type in self.bot_channel.all_commands:
                if cmd_type.called_by(args[0]):
                    alias_str = ''
                    for alias in cmd_type.command_name_list[1:]:
                        alias_str += '`{alias}`, '.format(alias=Config.BOT_COMMAND_PREFIX + alias)
                    if alias_str:
                        alias_str = '(Aliases: {})'.format(alias_str[:-2])
                    await self.client.send_message(
                        cmd.channel, '`{cmd_name}`: {admin}{help_text} {aliases}'.format(
                            cmd_name=cmd_type.mention,
                            help_text=cmd_type.help_text,
                            admin='[Admin only] ' if cmd_type.admin_only else '',
                            aliases=alias_str
                        )
                    )


class Info(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'info')
        self.help_text = 'Necrobot version information.'

    @property
    def show_in_help(self):
        return False

    async def _do_execute(self, cmd):
        debug_str = ''
        if Config.debugging():
            debug_str = ' (DEBUG)'
        elif Config.testing():
            debug_str = ' (TEST)'

        await self.client.send_message(
            cmd.channel,
            'Necrobot v-{0}{1}. Type `.help` for a list of commands.'.format(
                Config.BOT_VERSION,
                debug_str
            )
        )
