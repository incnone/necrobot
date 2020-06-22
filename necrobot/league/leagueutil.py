"""Utility for parsing user-entered strings and finding a corresponding Match"""
import datetime
import shlex
from typing import Optional

import pytz

import necrobot.exception
from necrobot.botbase.necrobot import Necrobot
from necrobot.match import matchdb
from necrobot.match.matchutil import make_match_from_raw_db_data
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.league import leaguedb
from necrobot.match import matchutil
from necrobot.match.match import Match
from necrobot.user import userlib
from necrobot.util.parse import dateparse
from necrobot.util import server, console, timestr, rtmputil, strutil


async def find_match(
        input_str: str,
        tz: pytz.timezone = pytz.utc,
        finished_only: Optional[bool] = None
) -> Match:
    """Find a match in the league database corresponding to the input args
    
    Parameters
    ----------
    input_str: str
        A user-input string that we want to use to find a registered match.
    tz: pytz.timezone
        A timezone (used for interpreting dates in the input_str)
    finished_only: bool
        If not None, then: If True, only return finished matches; if False, only return unfinished matches

    Returns
    -------
    Match
        The found match.
        
    Raises
    ------
    NotFoundException
        If no match could be found.
    ParseException
        If the input string couldn't be parsed meaningfully.
    """
    args = shlex.split(input_str)
    if len(args) < 2:
        raise necrobot.exception.ParseException('Need at least two racer names to find a match.')

    league_tag = args[0].lower()
    try:
        await LeagueMgr().get_league(league_tag=league_tag)
        args.pop(0)
    except necrobot.exception.LeagueDoesNotExist:
        league_tag = None
        # raise necrobot.exception.NotFoundException("Can't find any league by the name `{0}`.".format(args[0]))

    racer_1 = await userlib.get_user(any_name=args[0])
    if racer_1 is None:
        raise necrobot.exception.NotFoundException("Can't find any racer by the name `{0}`.".format(args[0]))
    args.pop(0)

    racer_2 = await userlib.get_user(any_name=args[0])
    if racer_2 is None:
        raise necrobot.exception.NotFoundException("Can't find any racer by the name `{0}`.".format(args[0]))
    args.pop(0)

    match_date = None
    match_date_str = ''
    for arg in args:
        match_date_str += arg + ' '
    if match_date_str:
        match_date_str = match_date_str[:-1]
        match_date = dateparse.parse_datetime(match_date_str, tz)

    match_id = await leaguedb.get_match_id(
        racer_1_id=racer_1.user_id,
        racer_2_id=racer_2.user_id,
        league_tag=league_tag,
        scheduled_time=match_date,
        finished_only=finished_only
    )
    if match_id is None:
        if finished_only is None:
            raise necrobot.exception.NotFoundException(
                "Can't find any match between `{0}` and `{1}`.".format(racer_1.display_name, racer_2.display_name)
            )
        elif finished_only is True:
            raise necrobot.exception.NotFoundException(
                "Can't find any completed match between `{0}` and `{1}`.".format(
                    racer_1.display_name, racer_2.display_name
                )
            )
        elif finished_only is False:
            raise necrobot.exception.NotFoundException(
                "Can't find any uncompleted match between `{0}` and `{1}`.".format(
                    racer_1.display_name, racer_2.display_name
                )
            )

    return await matchutil.get_match_from_id(match_id)


async def get_upcoming_and_current(league_tag: Optional[str] = None) -> list:
    """
    Parameters
    ----------
    league_tag: Optional[str]
        If not None, only look for matches in the given league.
    Returns
    -------
    list[Match]
        A list of all upcoming and ongoing matches, in order.
    """
    matches = []
    for row in await matchdb.get_channeled_matches_raw_data(must_be_scheduled=True, order_by_time=True):
        channel_id = int(row[13]) if row[13] is not None else None
        if channel_id is not None:
            channel = server.find_channel(channel_id=channel_id)
            if channel is not None:
                match = await make_match_from_raw_db_data(row=row)
                if league_tag is not None and match.league_tag != league_tag:
                    continue
                if match.suggested_time is None:
                    console.warning('Found match object {} has no suggested time.'.format(repr(match)))
                    continue
                if match.suggested_time > pytz.utc.localize(datetime.datetime.utcnow()):
                    matches.append(match)
                else:
                    match_room = Necrobot().get_bot_channel(channel)
                    if match_room is not None and await match_room.during_races():
                        matches.append(match)

    return matches


async def get_nextrace_displaytext(match_list: list) -> str:
    utcnow = pytz.utc.localize(datetime.datetime.utcnow())
    if len(match_list) > 1:
        display_text = 'Upcoming matches: \n'
    else:
        display_text = 'Next match: \n'

    for match in match_list:
        # TODO: Hacky s9 emote solution
        s9_emotes = {
            'cad': '<:cadence:676159524033527808>',
            'mel': '<:melody:676159691134337040>',
            'coh': '<:zelda:676158586975420457>',
            'noc': '<:nocturna:724458364125446204>'
        }
        if match.league_tag in s9_emotes:
            display_text += '{2} **{0}** - **{1}**'.format(
                match.racer_1.display_name,
                match.racer_2.display_name,
                s9_emotes[match.league_tag]
            )
        else:
            display_text += '\N{BULLET} **{0}** - **{1}** ({2})'.format(
                match.racer_1.display_name,
                match.racer_2.display_name,
                match.format_str
            )

        if match.suggested_time is None:
            display_text += '\n'
            continue

        display_text += ': {0} \n'.format(timestr.timedelta_to_str(match.suggested_time - utcnow, punctuate=True))
        match_cawmentator = await match.get_cawmentator()
        if match_cawmentator is not None:
            display_text += '    Cawmentary: <http://www.twitch.tv/{0}> \n'.format(match_cawmentator.twitch_name)
        elif match.racer_1.twitch_name is not None and match.racer_2.twitch_name is not None:
            display_text += '    Kadgar: {} \n'.format(
                rtmputil.kadgar_link(match.racer_1.twitch_name, match.racer_2.twitch_name)
            )

    display_text += '\nFull schedule: <https://condor.host/schedule>'

    return display_text


async def get_schedule_infotext():
    utcnow = pytz.utc.localize(datetime.datetime.utcnow())
    matches = await get_upcoming_and_current()

    max_r1_len = 0
    max_r2_len = 0
    for match in matches:
        max_r1_len = max(max_r1_len, len(strutil.tickless(match.racer_1.display_name)))
        max_r2_len = max(max_r2_len, len(strutil.tickless(match.racer_2.display_name)))

    schedule_text = '``` \nUpcoming matches: \n'
    for match in matches:
        if len(schedule_text) > 1800:
            break
        schedule_text += '{r1:>{w1}} v {r2:<{w2}} : '.format(
            r1=strutil.tickless(match.racer_1.display_name),
            w1=max_r1_len,
            r2=strutil.tickless(match.racer_2.display_name),
            w2=max_r2_len
        )
        if match.suggested_time - utcnow < datetime.timedelta(minutes=0):
            schedule_text += 'Right now!'
        else:
            schedule_text += timestr.str_full_24h(match.suggested_time)
        schedule_text += '\n'
    schedule_text += '```'

    return schedule_text
