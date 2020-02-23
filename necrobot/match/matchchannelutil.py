import discord
from typing import List, Optional

from necrobot.botbase.necrobot import Necrobot
from necrobot.match import matchdb
from necrobot.match.match import Match
from necrobot.match.matchglobals import MatchGlobals
from necrobot.match.matchroom import MatchRoom
from necrobot.match import matchutil
from necrobot.user.necrouser import NecroUser
from necrobot.util import server, console, writechannel
from necrobot.config import Config


def get_matchroom_name(match: Match) -> str:
    """Get a new unique channel name corresponding to the match.
    
    Parameters
    ----------
    match: Match
        The match whose info determines the name.
        
    Returns
    -------
    str
        The name of the channel.
    """
    name_prefix = match.matchroom_name
    cut_length = len(name_prefix) + 1
    largest_postfix = 1

    found = False
    for channel in server.guild.text_channels:
        if channel.name.startswith(name_prefix):
            found = True
            try:
                val = int(channel.name[cut_length:])
                largest_postfix = max(largest_postfix, val)
            except ValueError:
                pass

    return name_prefix if not found else '{0}-{1}'.format(name_prefix, largest_postfix + 1)


async def get_matches_with_channels(racer: NecroUser = None) -> list:
    """
    Parameters
    ----------
    racer: NecroUser
        The racer to find channels for. If None, finds all channeled matches.
    
    Returns
    -------
    list[Match]
        A list of all Matches that have associated channels on the server featuring the specified racer.
    """
    matches = []
    if racer is not None:
        raw_data = await matchdb.get_channeled_matches_raw_data(
            must_be_scheduled=False, order_by_time=False, racer_id=racer.user_id
        )
    else:
        raw_data = await matchdb.get_channeled_matches_raw_data(must_be_scheduled=False, order_by_time=False)

    for row in raw_data:
        channel_id = int(row[13])
        channel = server.find_channel(channel_id=channel_id)
        if channel is not None:
            match = await matchutil.make_match_from_raw_db_data(row=row)
            matches.append(match)
        else:
            console.warning('Found Match with channel {0}, but couldn\'t find this channel.'.format(channel_id))

    return matches


async def delete_all_match_channels(
        log=False,
        completed_only=False
) -> None:
    """Delete all match channels from the server.
    
    Parameters
    ----------
    log: bool
        If True, the channel text will be written to a log file before deletion.
    completed_only: bool
        If True, will only find completed matches.
    """
    for row in await matchdb.get_channeled_matches_raw_data():
        match_id = int(row[0])
        channel_id = int(row[13])
        channel = server.find_channel(channel_id=channel_id)
        delete_this = True
        if channel is not None:
            match_room = Necrobot().get_bot_channel(channel)
            completed = match_room is not None and match_room.played_all_races

            if completed_only and not completed:
                delete_this = False

            if delete_this:
                if log:
                    await writechannel.write_channel(
                        channel=channel,
                        outfile_name='{0}-{1}'.format(match_id, channel.name)
                    )
                await channel.delete()

        if delete_this:
            await matchdb.register_match_channel(match_id, None)


async def make_match_room(match: Match, register=False) -> MatchRoom or None:
    """Create a discord.Channel and a corresponding MatchRoom for the given Match. 
    
    Parameters
    ----------
    match: Match
        The Match to create a room for.
    register: bool
        If True, will register the Match in the database.

    Returns
    -------
    Optional[MatchRoom]
        The created room object.
    """
    # Check to see the match is registered
    if not match.is_registered:
        if register:
            await match.commit()
        else:
            console.warning('Tried to make a MatchRoom for an unregistered Match ({0}).'.format(match.matchroom_name))
            return None

    # Check to see if we already have the match channel
    channel_id = match.channel_id
    match_channel = server.find_channel(channel_id=channel_id) if channel_id is not None else None

    # If we couldn't find the channel or it didn't exist, make a new one
    if match_channel is None:
        # Create permissions
        deny_read = discord.PermissionOverwrite(read_messages=False)
        permit_read = discord.PermissionOverwrite(read_messages=True)
        racer_permissions = {server.guild.default_role: deny_read}
        for racer in match.racers:
            if racer.member is not None:
                racer_permissions[racer.member] = permit_read

        # Find the matches category channel
        channel_categories = MatchGlobals().channel_categories      # type: List[discord.CategoryChannel]
        if channel_categories is None:
            category_name = Config.MATCH_CHANNEL_CATEGORY_NAME
            if len(category_name) > 0:
                channel_category = await server.create_channel_category(category_name)
                MatchGlobals().set_channel_categories([channel_category])

        # Attempt to create the channel in each of the categories in reverse order
        if channel_categories is not None:
            success = False
            for channel_category in reversed(channel_categories):
                try:
                    match_channel = await server.guild.create_text_channel(
                        name=get_matchroom_name(match),
                        overwrites=racer_permissions,
                        category=channel_category
                    )
                    success = True
                    break
                except discord.HTTPException:
                    pass

            # If we still haven't made the channel, we're out of space, so register a new matches category
            if not success:
                new_channel_category = await server.create_channel_category(name=Config.MATCH_CHANNEL_CATEGORY_NAME)
                MatchGlobals().add_channel_category(channel=new_channel_category)
                match_channel = await server.guild.create_text_channel(
                    name=get_matchroom_name(match),
                    overwrites=racer_permissions,
                    category=new_channel_category
                )

        # If we don't have or want a category channel, just make the match without a category
        else:
            match_channel = await server.guild.create_text_channel(
                name=get_matchroom_name(match),
                overwrites=racer_permissions
            )

        if match_channel is None:
            console.warning('Failed to make a match channel.')
            return None

    # Make the actual RaceRoom and initialize it
    match.set_channel_id(int(match_channel.id))
    new_room = MatchRoom(match_discord_channel=match_channel, match=match)
    Necrobot().register_bot_channel(match_channel, new_room)
    await new_room.initialize()

    return new_room


async def close_match_room(match: Match) -> None:
    """Close the discord.Channel corresponding to the Match, if any.
    
    Parameters
    ----------
    match: Match
        The Match to close the channel for.
    """
    if not match.is_registered:
        console.warning('Trying to close the room for an unregistered match.')
        return

    channel_id = match.channel_id
    channel = server.find_channel(channel_id=channel_id)
    if channel is None:
        console.warning('Coudn\'t find channel with id {0} in close_match_room '
                        '(match_id={1}).'.format(channel_id, match.match_id))
        return

    await Necrobot().unregister_bot_channel(channel)
    await channel.delete()
    match.set_channel_id(None)


async def get_match_room(match: Match) -> Optional[MatchRoom]:
    """Get the MatchRoom corresponding to the given match, if any.

    Parameters
    ----------
    match: Match
        The Match to get the MatchRoom for.
    """
    if not match.is_registered:
        console.warning('Trying to get a MatchRoom for an unregistered Match.')
        return None

    channel_id = match.channel_id
    if channel_id is None:
        console.warning('Called get_match_room on an unchanneled match.')
        return None

    channel = server.find_channel(channel_id=channel_id)
    if channel is None:
        console.warning(
            'Couldn\'t find channel with id {0} in close_match_room (match_id={1}).'
            .format(channel_id, match.match_id)
        )
        return None

    try:
        matchroom = Necrobot().get_bot_channel(discord_channel=channel)
    except KeyError:
        console.warning(
            'Couldn\'t find MatchRoom for match with ID (match_id={1}), due to KeyError.'
            .format(channel_id, match.match_id)
        )
        return None

    if matchroom is None:
        console.warning(
            'Couldn\'t find MatchRoom with id {0} in close_match_room (match_id={1}).'
            .format(channel_id, match.match_id)
        )
        return None

    return matchroom
