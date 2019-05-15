from typing import List, Optional, Union
import discord
import necrobot.exception
from necrobot.botbase.command import Command
from necrobot.match import matchinfo, matchutil
from necrobot.match import matchchannelutil
from necrobot.user import userlib


async def make_match_from_cmd(
        cmd: Command,
        racer_members: Optional[List[Union[discord.User, discord.Member]]] = None,
        racer_names: Optional[List[str]] = None,
        match_info: matchinfo.MatchInfo = matchinfo.MatchInfo(),
        allow_duplicates: bool = True
):
    if racer_members is None:
        racer_members = []
    if racer_names is None:
        racer_names = []

    racers = []

    # Add the racers from member objects
    for member in racer_members:
        racer_as_necrouser = await userlib.get_user(discord_id=member.id)
        if racer_as_necrouser is not None:
            racers.append(racer_as_necrouser)
        else:
            await cmd.channel.send(
                'Unexpected error: Couldn\'t find `{0}` in the database.'.format(member.display_name)
            )
            return

    # Add the racers from names
    for name in racer_names:
        racer_as_necrouser = await userlib.get_user(any_name=name)

        if racer_as_necrouser is not None:
            racers.append(racer_as_necrouser)
        else:
            await cmd.channel.send(
                'Couldn\'t find a user with name `{0}`.'.format(name)
            )
            return

    # Check we have exactly two racers
    if len(racers) != 2:
        await cmd.channel.send(
            'Unexpected error: Tried to create a match with more than two racers.'
        )
        return

    # Check for duplicating match
    if not allow_duplicates:
        duplicate = await matchutil.match_exists_between(racers[0], racers[1])
        if duplicate:
            raise necrobot.exception.DuplicateMatchException()

    # Create the Match object
    new_match = await matchutil.make_match(
        racer_1_id=racers[0].user_id,
        racer_2_id=racers[1].user_id,
        match_info=match_info,
        register=True
    )

    # Create the match room
    match_room = await matchchannelutil.make_match_room(match=new_match)
    await match_room.send_channel_start_text()

    # Output success
    await cmd.channel.send(
        'Match created in channel {0}.'.format(
            match_room.channel.mention))

    return new_match
