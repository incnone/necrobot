import asyncio
import discord
import random

import command

PROTECTED_ROLENAMES = ['Necrobot']
ROLES_COLORS = {\
'teal':discord.Color.teal(),
'dank_teal':discord.Color.dark_teal(),
'green':discord.Color.green(),
'dank_green':discord.Color.dark_green(),
'blue':discord.Color.blue(),
'dank_blue':discord.Color.dark_blue(),
'purple':discord.Color.purple(),
'dank_purple':discord.Color.dark_purple(),
'magenta':discord.Color.magenta(),
'dank_magenta':discord.Color.dark_magenta(),
'gold':discord.Color.gold(),
'dank_gold':discord.Color.dark_gold(),
'orange':discord.Color.orange(),
'dank_orange':discord.Color.dark_orange(),
'red':discord.Color.red(),
'dank_red':discord.Color.dark_red(),
'lighter_grey':discord.Color.lighter_grey(),
'dank_grey':discord.Color.dark_grey(),
'light_grey':discord.Color.light_grey(),
'danker_grey':discord.Color.darker_grey() \
}

@asyncio.coroutine
def color_user(member, client, server):
    protected_colors = []
    for role in server.roles:
        if role.name in PROTECTED_ROLENAMES:
            protected_colors.append(role.colour)            

    for role in member.roles:
        if role.name in ROLES_COLORS.keys():
            yield from client.remove_roles(member, role)
            protected_colors.append(role.colour)

    new_colorname = get_random_colorname(protected_colors)
    role_to_use = None
    for role in server.roles:
        if role.name == new_colorname:
            role_to_use = role

    if role_to_use == None:
        role_to_use = yield from client.create_role(server, name=new_colorname, color=ROLES_COLORS[new_colorname], hoist=False)

    yield from client.add_roles(member, role_to_use)

def get_random_colorname(protected_colors):
    allowed_colornames = [cname for cname in ROLES_COLORS.keys() if (not ROLES_COLORS[cname] in protected_colors)]
    idx = random.randint(0, len(allowed_colornames) - 1)
    return allowed_colornames[idx]

class ColorMe(command.CommandType):
    def __init__(self, colorer_module):
        command.CommandType.__init__(self, 'dankify')
        self._cm = colorer_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.channel == self._cm.main_channel:
            asyncio.ensure_future(color_user(command.author, self._cm.client, self._cm.server))
            #yield from asyncio.sleep(1)
            asyncio.ensure_future(self._cm.client.delete_message(command.message))
                                
class ColorerModule(command.Module):
    def __init__(self, necrobot):
        self._necrobot = necrobot
        self.command_types = [ColorMe(self)]

    @property
    def client(self):
        return self._necrobot.client

    @property
    def server(self):
        return self._necrobot.server

    @property
    def main_channel(self):
        return self._necrobot.main_channel
