import discord

from necrobot.botbase.necrobot import Necrobot
from necrobot.match import matchdb
from necrobot.match.match import Match
from necrobot.match.matchglobals import MatchGlobals
from necrobot.match.matchroom import MatchRoom
from necrobot.match.matchutil import make_match_from_raw_db_data
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
    for channel in server.server.channels:
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
            match = await make_match_from_raw_db_data(row=row)
            matches.append(match)
        else:
            console.warning('Found Match with channel {0}, but couldn\'t find this channel.'.format(channel_id))

    return matches


async def delete_all_match_channels(
        log=False,
        completed_only=False,
        delete_db_info_for_uncompleted=False
) -> None:
    """Delete all match channels from the server.
    
    Parameters
    ----------
    log: bool
        If True, the channel text will be written to a log file before deletion.
    completed_only: bool
        If True, will only find completed matches.
    """
    match_ids_to_scrub_from_db = []
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

            if delete_db_info_for_uncompleted and not completed:
                match_ids_to_scrub_from_db.append(match_id)

            if delete_this:
                if log:
                    await writechannel.write_channel(
                        client=server.client,
                        channel=channel,
                        outfile_name='{0}-{1}'.format(match_id, channel.name)
                    )
                await server.client.delete_channel(channel)

        if delete_this:
            await matchdb.register_match_channel(match_id, None)

    if delete_db_info_for_uncompleted:
        await matchdb.scrub_matches(match_ids_to_scrub_from_db)


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
        racer_permissions = []
        for racer in match.racers:
            if racer.member is not None:
                racer_permissions.append(discord.ChannelPermissions(target=racer.member, overwrite=permit_read))

        # Make a channel for the room
        # noinspection PyUnresolvedReferences
        match_channel = await server.client.create_channel(
            server.server,
            get_matchroom_name(match),
            discord.ChannelPermissions(target=server.server.default_role, overwrite=deny_read),
            discord.ChannelPermissions(target=server.server.me, overwrite=permit_read),
            *racer_permissions,
            type=discord.ChannelType.text
        )

        if match_channel is None:
            console.warning('Failed to make a match channel.')
            return None

        # Put the match channel in the matches category
        channel_category = MatchGlobals().channel_category
        if channel_category is None:
            category_name = Config.MATCH_CHANNEL_CATEGORY_NAME
            if len(category_name) > 0:
                channel_category = await server.create_channel_category(category_name)
                MatchGlobals().set_channel_category(channel_category)

        if channel_category is not None:
            try:
                await server.set_channel_category(channel=match_channel, category=channel_category)
            except discord.HTTPException:
                # Out of space, so register a new matches category
                new_channel_category = await server.create_channel_category(name=channel_category.name)
                MatchGlobals().set_channel_category(channel=new_channel_category)
                await server.set_channel_category(channel=match_channel, category=new_channel_category)

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
    await server.client.delete_channel(channel)
    match.set_channel_id(None)