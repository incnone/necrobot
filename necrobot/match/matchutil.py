import datetime
import discord
import pytz

from necrobot.database import matchdb, racedb
from necrobot.util import console, timestr, writechannel

from necrobot.botbase.necrobot import Necrobot
from necrobot.match.match import Match
from necrobot.match.matchinfo import MatchInfo
from necrobot.match.matchroom import MatchRoom
from necrobot.race.raceinfo import RaceInfo
from necrobot.user.necrouser import NecroUser


match_library = {}


# noinspection PyIncorrectDocstring
async def make_match(*args, register=False, **kwargs) -> Match:
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
    await match.initialize()
    if register:
        match.commit()
        match_library[match.match_id] = match
    return match


async def get_match_from_id(match_id: int) -> Match or None:
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

    raw_data = await matchdb.get_raw_match_data(match_id)
    if raw_data is not None:
        return await make_match_from_raw_db_data(raw_data)
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


async def get_upcoming_and_current() -> list:
    """    
    Returns
    -------
    list[Match]
        A list of all upcoming and ongoing matches, in order. 
    """
    matches = []
    for row in await matchdb.get_channeled_matches_raw_data(must_be_scheduled=True, order_by_time=True):
        channel_id = int(row[13]) if row[13] is not None else None
        if channel_id is not None:
            channel = Necrobot().find_channel_with_id(channel_id)
            if channel is not None:
                match = await make_match_from_raw_db_data(row=row)
                if match.suggested_time > pytz.utc.localize(datetime.datetime.utcnow()):
                    matches.append(match)
                else:
                    match_room = Necrobot().get_bot_channel(channel)
                    if match_room is not None and await match_room.during_races():
                        matches.append(match)

    return matches


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
        channel = Necrobot().find_channel_with_id(channel_id)
        if channel is not None:
            match = await make_match_from_raw_db_data(row=row)
            matches.append(match)
        else:
            console.warning('Found Match with channel {0}, but couldn\'t find this channel.'.format(channel_id))

    return matches


async def delete_all_match_channels(log=False, completed_only=False) -> None:
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
        channel = Necrobot().find_channel_with_id(channel_id)
        delete_this = True
        if channel is not None:
            if completed_only:
                match_room = Necrobot().get_bot_channel(channel)
                if match_room is None or not await match_room.played_all_races():
                    delete_this = False

            if delete_this:
                if log:
                    await writechannel.write_channel(
                        client=Necrobot().client,
                        channel=channel,
                        outfile_name='{0}-{1}'.format(match_id, channel.name)
                    )
                await Necrobot().client.delete_channel(channel)

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
    necrobot = Necrobot()

    # Check to see the match is registered
    if not match.is_registered:
        if register:
            match.commit()
        else:
            console.warning('Tried to make a MatchRoom for an unregistered Match ({0}).'.format(match.matchroom_name))
            return None

    # Check to see if we already have the match channel
    channel_id = match.channel_id
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
            console.warning('Failed to make a match channel.')
            return None

    # Make the actual RaceRoom and initialize it
    match.set_channel_id(int(match_channel.id))
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
        console.warning('Trying to close the room for an unregistered match.')
        return

    channel_id = match.channel_id
    channel = Necrobot().find_channel_with_id(channel_id)
    if channel is None:
        console.warning('Coudn\'t find channel with id {0} in close_match_room '
                        '(match_id={1}).'.format(channel_id, match.match_id))
        return

    await Necrobot().unregister_bot_channel(channel)
    await Necrobot().client.delete_channel(channel)
    match.set_channel_id(None)


async def get_nextrace_displaytext(match_list: list) -> str:
    utcnow = pytz.utc.localize(datetime.datetime.utcnow())
    if len(match_list) > 1:
        display_text = 'Upcoming matches: \n'
    else:
        display_text = 'Next match: \n'

    for match in match_list:
        # noinspection PyUnresolvedReferences
        display_text += '\N{BULLET} **{0}** - **{1}**'.format(
            match.racer_1.bot_name,
            match.racer_2.bot_name)
        if match.suggested_time is None:
            display_text += '\n'
            continue

        display_text += ': {0} \n'.format(timestr.timedelta_to_str(match.suggested_time - utcnow, punctuate=True))
        if await match.get_cawmentator() is not None:
            display_text += '    Cawmentary: <http://www.twitch.tv/{0}> \n'.format(match.cawmentator.twitch_name)
        elif match.racer_1.rtmp_name is not None and match.racer_2.rtmp_name is not None:
            display_text += '    RTMP: <http://rtmp.condorleague.tv/#{0}/{1}> \n'.format(
                match.racer_1.rtmp_name.lower(), match.racer_2.rtmp_name.lower())
    return display_text


async def delete_match(match_id: int) -> None:
    await matchdb.delete_match(match_id=match_id)
    if match_id in match_library:
        del match_library[match_id]


async def make_match_from_raw_db_data(row: list) -> Match:
    match_id = int(row[0])
    if match_id in match_library:
        return match_library[match_id]

    match_info = MatchInfo(
        race_info=await racedb.get_race_info_from_type_id(int(row[1])) if row[1] is not None else RaceInfo(),
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
        cawmentator_id=row[12],
        channel_id=int(row[13]) if row[13] is not None else None
    )

    await new_match.initialize()
    match_library[new_match.match_id] = new_match
    return new_match
