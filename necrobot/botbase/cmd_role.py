from necrobot.util import server
from necrobot.botbase.commandtype import CommandType


class AddCRoWRole(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'addrole')
        self.help_text = "Add yourself to a CRoW role. Use `{cmd} crow4` for the 4pm role, and `{cmd} crow11` " \
                         "for the 11pm role.".format(cmd=self.mention)

    async def _do_execute(self, cmd):
        await _modify_roles(self, cmd, add=True)


class RemoveCRoWRole(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'removerole')
        self.help_text = "Remove yourself from a CRoW role. Use `{cmd} crow4` for the 4pm role, and `{cmd} crow11` " \
                         "for the 11pm role.".format(cmd=self.mention)

    async def _do_execute(self, cmd):
        await _modify_roles(self, cmd, add=False)


async def _modify_roles(cmdtype: CommandType, cmd, add: bool):
    role_map = {
        'crow4': 'CRoW Racers 4pm',
        'crow11': 'CRoW Racers 11pm'
    }

    if len(cmd.args) == 0:
        await cmdtype.client.send_message(
            cmd.channel,
            'Error: Use `{c} crow4` for the 4pm role, and `{c} crow11` " \
                     "for the 11pm role.'.format(c=cmdtype.mention)
        )
        return

    roles_to_add = []
    failed_roles = []
    for rolename in cmd.args:
        if rolename not in role_map:
            failed_roles.append(rolename)
        else:
            role_full_name = role_map[rolename]
            for role in server.server.roles:
                if role.name.lower() == role_full_name.lower():
                    roles_to_add.append(role)

    if not roles_to_add:
        await cmdtype.client.send_message('Error: Could not find any of the specified roles.')
        return

    if add:
        await cmdtype.client.add_roles(cmd.author, *roles_to_add)
        confirm_msg = 'Roles added: '
    else:
        await cmdtype.client.remove_roles(cmd.author, *roles_to_add)
        confirm_msg = 'Roles removed: '

    for role in roles_to_add:
        confirm_msg += '`{rolename}`, '.format(rolename=role.name)
    confirm_msg = confirm_msg[:-2] + '.'

    if failed_roles:
        confirm_msg += ' The following could not be found: '
        for failed_role in failed_roles:
            confirm_msg += '`{rolename}`, '.format(rolename=failed_role)
        confirm_msg = confirm_msg[:-2] + '.'

    await cmdtype.client.send_message(cmd.channel, confirm_msg)
