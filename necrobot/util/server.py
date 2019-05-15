"""
Module containing global server information for discord. Acts as a very small encapsulation layer between the bot and
discord.py.
"""

import discord
import discord.http
from typing import List, Optional, Union
from necrobot.config import Config


client = None           # type: Optional[discord.Client]
guild = None           # type: Optional[discord.Guild]
admin_roles = list()    # type: List[discord.Role]


def init(client_: discord.Client, guild_: discord.Guild) -> None:
    global client, guild, admin_roles
    client = client_
    guild = guild_
    for rolename in Config.ADMIN_ROLE_NAMES:
        for role in guild.roles:
            if role.name == rolename:
                admin_roles.append(role)


def find_admin(ignore: Optional[List[str]] = None) -> Optional[discord.Member]:
    """Returns a random bot admin (for testing purposes)"""
    if ignore is None:
        ignore = []

    for member in guild.members:
        if member.display_name in ignore or member.id == client.user.id:
            continue
        for role in member.roles:
            if role in admin_roles:
                return member
    return None


def find_channel(channel_name: str = None, channel_id: Union[str, int] = None) -> Optional[discord.TextChannel]:
    """Returns a channel with the given name on the server, if any"""
    if channel_id is not None:
        for channel in guild.channels:
            if int(channel.id) == int(channel_id):
                return channel
    elif channel_name is not None:
        for channel in guild.channels:
            if channel.name.lower() == channel_name.lower():
                return channel
    return None


def find_category(channel_name: str = None) -> Optional[discord.CategoryChannel]:
    """Returns a channel with the given name on the server, if any"""
    for channel in guild.categories:
        if channel.name.lower() == channel_name.lower():
            return channel
    return None


def find_all_channels(channel_name: str) -> List[discord.abc.GuildChannel]:
    """Returns all channels with the given name on the server"""
    found_channels = []
    for channel in guild.channels:
        if channel.name.lower() == channel_name.lower():
            found_channels.append(channel)
    return found_channels


def find_member(discord_name: str = None, discord_id: Union[str, int] = None) -> Optional[discord.Member]:
    """Returns a member with a given username or ID (capitalization ignored)"""
    if discord_name is None and discord_id is None:
        return None

    if discord_id is not None:
        for member in guild.members:
            if int(member.id) == int(discord_id):
                return member

    if discord_name is not None:
        for member in guild.members:
            if member.display_name.lower() == discord_name.lower() \
                    or member.name.lower() == discord_name.lower():
                return member


def find_members(username: str) -> List[discord.Member]:
    """Returns a list of all members with a given username (capitalization ignored)"""
    to_return = []
    for member in guild.members:
        if member.display_name.lower() == username.lower():
            to_return.append(member)
    return to_return


def find_role(role_name: str) -> Optional[discord.Role]:
    """Finds a discord.Role with the given name, if any"""
    for role in guild.roles:
        if role.name.lower() == role_name.lower():
            return role
    return None


def get_as_member(user: discord.User) -> Optional[discord.Member]:
    """Returns the given Discord user as a member of the server"""
    for member in guild.members:
        if member.id == user.id:
            return member
    return None


def is_admin(user: Union[discord.User, discord.Member]) -> bool:
    """True if user is a server admin"""
    if isinstance(user, discord.User):
        member = get_as_member(user)    # type: discord.Member
    else:
        member = user                   # type: discord.Member

    for role in member.roles:
        if role in admin_roles:
            return True
    return False


async def set_channel_category(channel: discord.TextChannel, category: discord.CategoryChannel):
    await channel.edit(category=category)


async def create_channel_category(name: str) -> discord.CategoryChannel:
    return await guild.create_category(name=name)
