from necrobot.util import server
from necrobot.botbase.commandtype import CommandType


class AddCRoWRole(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'addrole')
        self.help_text = "Use `{cmd} crow` to give yourself the CRoW role.".format(cmd=self.mention)

    async def _do_execute(self, cmd):
        await _modify_roles(cmd, add=True)


class RemoveCRoWRole(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'removerole')
        self.help_text = "Use `{cmd} crow` to remove the CRoW role from yourself.".format(cmd=self.mention)

    async def _do_execute(self, cmd):
        await _modify_roles(cmd, add=False)


async def _modify_roles(cmd, add: bool):
    role_map = {
        'crow': 'CRoW Racers',
    }

    if len(cmd.args) == 0:
        await cmd.channel.send(
            'Error: Use `{c} crow` for the CRoW role. (No other roles currently function with this command.)'
        )
        return

    roles_to_add = []
    failed_roles = []
    for rolename in cmd.args:
        if rolename not in role_map:
            failed_roles.append(rolename)
        else:
            role_full_name = role_map[rolename]
            for role in server.guild.roles:
                if role.name.lower() == role_full_name.lower():
                    roles_to_add.append(role)

    if not roles_to_add:
        await cmd.channel.send('Error: Could not find any of the specified roles.')
        return

    if add:
        await cmd.author.add_roles(*roles_to_add)
        confirm_msg = 'Roles added: '
    else:
        await cmd.author.remove_roles(*roles_to_add)
        confirm_msg = 'Roles removed: '

    for role in roles_to_add:
        confirm_msg += '`{rolename}`, '.format(rolename=role.name)
    confirm_msg = confirm_msg[:-2] + '.'

    if failed_roles:
        confirm_msg += ' The following could not be found: '
        for failed_role in failed_roles:
            confirm_msg += '`{rolename}`, '.format(rolename=failed_role)
        confirm_msg = confirm_msg[:-2] + '.'

    await cmd.channel.send(confirm_msg)
