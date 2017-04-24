import discord

from necrobot.database import matchdb
from necrobot.util import console, writechannel

from necrobot.botbase.necrobot import Necrobot
from necrobot.match.match import Match
from necrobot.match.matchinfo import MatchInfo
from necrobot.match.matchroom import MatchRoom
from necrobot.race.raceinfo import RaceInfo


match_library = {}


# noinspection PyIncorrectDocstring
def make_match(*args, register=False, **kwargs) -> Match:
    """Create a Match object. There should be no need to call this directly; use matchutil.make_match instead, 
    since this needs to interact with the database.

    Parameters
    ----------
    racer_1_id: int
        The DB user ID of the first racer.
    racer_2_id: int
        The DB user ID of the second racer.
    max_races: int
        The maximum number of races this match can be. (If is_best_of is True, then the match is a best of
        max_races; otherwise, the match is just repeating max_races.)
    is_best_of: bool
        Whether the match is a best-of-X (if True) or a repeat-X (if False); X is max_races.
    match_id: int
        The DB unique ID of this match.
    suggested_time: datetime.datetime
        The time the match is suggested for. If no tzinfo, UTC is assumed.
    r1_confirmed: bool
        Whether the first racer has confirmed the match time.
    r2_confirmed: bool
        Whether the second racer has confirmed the match time.
    r1_unconfirmed: bool
        Whether the first racer wishes to unconfirm the match time.
    r2_unconfirmed: bool
        Whether the second racer wishes to unconfirm the match time.
    ranked: bool
        Whether the results of this match should be used to update ladder rankings.
    race_info: RaceInfo
        The types of races to be run in this match.
    cawmentator_id: int
        The DB unique ID of the cawmentator for this match.
    register: bool
        Whether to register the match in the database. 
        
    Returns
    ---------
    Match
        The created match.
    """
    if 'match_id' in kwargs and kwargs['match_id'] in match_library:
        return match_library[kwargs['match_id']]

    match = Match(*args, commit_fn=matchdb.write_match, **kwargs)
    if register:
        match.commit()
        match_library[match.match_id] = match
    return match


def get_match_from_id(match_id: int) -> Match or None:
    """Get a match object from its DB unique ID.
    
    Parameters
    ----------
    match_id: int
        The databse ID of the match.

    Returns
    -------
    Optional[Match]
        The match found, if any.
    """
    if match_id is None:
        return None

    if match_id in match_library:
        return match_library[match_id]

    raw_data = matchdb.get_raw_match_data(match_id)
    if raw_data is not None:
        return _make_match_from_raw_db_data(raw_data)
    else:
        return None


def get_matchroom_name(server: discord.Server, match: Match) -> str:
    """Get a new unique channel name corresponding to the match.
    
    Parameters
    ----------
    server: discord.Server
        The server on which the channel name should be unique.
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
    for channel in server.channels:
        if channel.name.startswith(name_prefix):
            found = True
            try:
                val = int(channel.name[cut_length:])
                largest_postfix = max(largest_postfix, val)
            except ValueError:
                pass

    return name_prefix if not found else '{0}-{1}'.format(name_prefix, largest_postfix + 1)


def get_matches_with_channels() -> list:
    """
    Returns
    -------
    list[Match]
        A list of all Matches that have associated channels on the server.
    """
    matches = []

    for row in matchdb.get_channeled_matches_raw_data():
        channel_id = int(row[13])
        channel = Necrobot().find_channel_with_id(channel_id)
        if channel is not None:
            match = _make_match_from_raw_db_data(row=row)
            matches.append(match)
        else:
            console.error('Found Match with channel {0}, but couldn\'t find this channel.'.format(channel_id))

    return matches


async def delete_all_match_channels(log=False) -> None:
    """Delete all match channels from the server.
    
    Parameters
    ----------
    log: bool
        If True, the channel text will be written to a log file before deletion.
    """
    for row in matchdb.get_channeled_matches_raw_data():
        match_id = int(row[0])
        channel_id = int(row[13])
        channel = Necrobot().find_channel_with_id(channel_id)
        if channel is not None:
            if log:
                await writechannel.write_channel(
                    client=Necrobot().client,
                    channel=channel,
                    outfile_name='{0}-{1}'.format(match_id, channel.name)
                )
            await Necrobot().client.delete_channel(channel)

        matchdb.register_match_channel(match_id, None)


async def recover_stored_match_rooms() -> None:
    """Create MatchRoom objects for matches in the database with stored channels that exist on the
    discord server.
    """
    console.info('Recovering stored match rooms------------')
    for row in matchdb.get_channeled_matches_raw_data():
        channel_id = int(row[13])
        channel = Necrobot().find_channel_with_id(channel_id)
        if channel is not None:
            match = _make_match_from_raw_db_data(row=row)
            new_room = MatchRoom(match_discord_channel=channel, match=match)
            Necrobot().register_bot_channel(channel, new_room)
            await new_room.initialize()
            console.info('  Channel ID: {0}  Match: {1}'.format(channel_id, match))
        else:
            console.info('  Couldn\'t find channel with ID {0}.'.format(channel_id))
    console.info('-----------------------------------------')


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
    necrobot = Necrobot()

    # Check to see the match is registered
    if not match.is_registered:
        if register:
            match.commit()
        else:
            console.error('Tried to make a MatchRoom for an unregistered Match ({0}).'.format(match.matchroom_name))
            return None

    # Check to see if we already have the match channel
    channel_id = matchdb.get_match_channel_id(match.match_id)
    match_channel = necrobot.find_channel_with_id(channel_id) if channel_id is not None else None

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
        match_channel = await necrobot.client.create_channel(
            necrobot.server,
            get_matchroom_name(necrobot.server, match),
            discord.ChannelPermissions(target=necrobot.server.default_role, overwrite=deny_read),
            discord.ChannelPermissions(target=necrobot.server.me, overwrite=permit_read),
            *racer_permissions,
            type=discord.ChannelType.text)

        if match_channel is None:
            console.error('Failed to make a match channel.')
            return None

    # Make the actual RaceRoom and initialize it
    matchdb.register_match_channel(match_id=match.match_id, channel_id=match_channel.id)
    new_room = MatchRoom(match_discord_channel=match_channel, match=match)
    necrobot.register_bot_channel(match_channel, new_room)
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
        console.error('Trying to close the room for an unregistered match.')
        return

    channel_id = matchdb.get_match_channel_id(match.match_id)
    channel = Necrobot().find_channel_with_id(channel_id)
    if channel is None:
        console.error('Coudn\'t find channel with id {0} in close_match_room '
                      '(match_id={1}).'.format(channel_id, match.match_id))
        return

    await Necrobot().unregister_bot_channel(channel)
    await Necrobot().client.delete_channel(channel)
    matchdb.register_match_channel(match_id=match.match_id, channel_id=None)


def _make_match_from_raw_db_data(row):
    match_id = int(row[0])
    if match_id in match_library:
        return match_library[match_id]

    match_info = MatchInfo(
        race_info=matchdb.get_race_info_from_type_id(int(row[1])) if row[1] is not None else RaceInfo(),
        ranked=bool(row[9]),
        is_best_of=bool(row[10]),
        max_races=int(row[11])
    )

    new_match = Match(
        commit_fn=matchdb.write_match,
        match_id=match_id,
        match_info=match_info,
        racer_1_id=int(row[2]),
        racer_2_id=int(row[3]),
        suggested_time=row[4],
        r1_confirmed=bool(row[5]),
        r2_confirmed=bool(row[6]),
        r1_unconfirmed=bool(row[7]),
        r2_unconfirmed=bool(row[8]),
        cawmentator_id=row[12]
    )

    match_library[new_match.match_id] = new_match
    return new_match
