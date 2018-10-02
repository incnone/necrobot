"""
Module containing global server information for discord. Acts as a very small encapsulation layer between the bot and
discord.py.
"""

import discord
import discord.http
from typing import List, Optional, Union
from necrobot.config import Config


client = None           # type: discord.Client
server = None           # type: discord.Server

main_channel = None     # type: discord.Channel
admin_roles = list()    # type: List[discord.Role]
staff_role = None       # type: Optional[discord.Role]


def init(client_: discord.Client, server_: discord.Server) -> None:
    global client, server, main_channel, admin_roles, staff_role
    client = client_
    server = server_
    main_channel = server.default_channel
    for rolename in Config.ADMIN_ROLE_NAMES:
        for role in server.roles:
            if role.name == rolename:
                admin_roles.append(role)
            if role.name == Config.STAFF_ROLE:
                staff_role = role


def find_admin(ignore=list()) -> Optional[discord.Member]:
    """Returns a random bot admin (for testing purposes)"""
    for member in server.members:
        if member.display_name in ignore or member.id == client.user.id:
            continue
        for role in member.roles:
            if role in admin_roles:
                return member
    return None


def find_channel(channel_name: str = None, channel_id: Union[str, int] = None) -> Optional[discord.Channel]:
    """Returns the channel with the given name on the server, if any"""
    if channel_id is not None:
        for channel in server.channels:
            if int(channel.id) == int(channel_id):
                return channel
    elif channel_name is not None:
        for channel in server.channels:
            if channel.name.lower() == channel_name.lower():
                return channel
    return None


def find_member(discord_name: str = None, discord_id: Union[str, int] = None) -> Optional[discord.Member]:
    """Returns a member with a given username or ID (capitalization ignored)"""
    if discord_name is None and discord_id is None:
        return None

    if discord_id is not None:
        for member in server.members:
            if int(member.id) == int(discord_id):
                return member

    if discord_name is not None:
        for member in server.members:
            if member.display_name.lower() == discord_name.lower() \
                    or member.name.lower() == discord_name.lower():
                return member


def find_members(username: str) -> List[discord.Member]:
    """Returns a list of all members with a given username (capitalization ignored)"""
    to_return = []
    for member in server.members:
        if member.display_name.lower() == username.lower():
            to_return.append(member)
    return to_return


def find_role(role_name: str) -> Optional[discord.Role]:
    """Finds a discord.Role with the given name, if any"""
    for role in server.roles:
        if role.name.lower() == role_name.lower():
            return role
    return None


def get_as_member(user: discord.User) -> Optional[discord.Member]:
    """Returns the given Discord user as a member of the server"""
    for member in server.members:
        if int(member.id) == int(user.id):
            return member
    return None


def is_admin(user: discord.User) -> bool:
    """True if user is a server admin"""
    member = get_as_member(user)
    for role in member.roles:
        if role in admin_roles:
            return True
    return False


async def set_channel_category(channel: discord.Channel, category: discord.Channel):
    await client.http.request(
        discord.http.Route('PATCH', '/channels/{channel_id}', channel_id=channel.id),
        json={'parent_id': category.id}
    )


async def create_channel_category(name: str) -> discord.Channel:
    data = await client.http.request(
        discord.http.Route('POST', '/guilds/{guild_id}/channels', guild_id=server.id),
        json={
            'name': name,
            'type': 4   # 4 is the "category" channel type
        }
    )
    channel = discord.Channel(server=server, **data)
    return channel
