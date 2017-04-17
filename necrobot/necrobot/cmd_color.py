import asyncio
import random

import discord

from necrobot.botbase.command import CommandType

PROTECTED_ROLENAMES = ['Necrobot']
ROLES_COLORS = {
    'teal': discord.Color.teal(),
    'dank_teal': discord.Color.dark_teal(),
    'green': discord.Color.green(),
    'dank_green': discord.Color.dark_green(),
    'blue': discord.Color.blue(),
    'dank_blue': discord.Color.dark_blue(),
    'purple': discord.Color.purple(),
    'dank_purple': discord.Color.dark_purple(),
    'magenta': discord.Color.magenta(),
    'dank_magenta': discord.Color.dark_magenta(),
    'gold': discord.Color.gold(),
    'dank_gold': discord.Color.dark_gold(),
    'orange': discord.Color.orange(),
    'dank_orange': discord.Color.dark_orange(),
    'red': discord.Color.red(),
    'dank_red': discord.Color.dark_red(),
    'lighter_grey': discord.Color.lighter_grey(),
    'dank_grey': discord.Color.dark_grey(),
    'light_grey': discord.Color.light_grey(),
    'danker_grey': discord.Color.darker_grey()
    }


async def color_user(member, client, server):
    protected_colors = []
    for role in server.roles:
        if role.name in PROTECTED_ROLENAMES:
            protected_colors.append(role.colour)            

    for role in member.roles:
        if role.name in ROLES_COLORS.keys():
            await client.remove_roles(member, role)
            protected_colors.append(role.colour)

    new_colorname = get_random_colorname(protected_colors)
    role_to_use = None
    for role in server.roles:
        if role.name == new_colorname:
            role_to_use = role

    if role_to_use is None:
        role_to_use = await client.create_role(
            server,
            name=new_colorname,
            color=ROLES_COLORS[new_colorname],
            hoist=False)

    await client.add_roles(member, role_to_use)


def get_random_colorname(protected_colors):
    allowed_colornames = [cname for cname in ROLES_COLORS.keys() if (not ROLES_COLORS[cname] in protected_colors)]
    idx = random.randint(0, len(allowed_colornames) - 1)
    return allowed_colornames[idx]


class ColorMe(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dankify')
        self.secret_command = True

    async def _do_execute(self, command):
        asyncio.ensure_future(color_user(command.author, self.client, self.necrobot.server))
        asyncio.ensure_future(self.client.delete_message(command.message))
