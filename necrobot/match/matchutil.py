import datetime
from typing import Optional

from necrobot.match.matchgsheetinfo import MatchGSheetInfo
from necrobot.match import matchdb
from necrobot.match.match import Match
from necrobot.match.matchinfo import MatchInfo
from necrobot.race import racedb
from necrobot.race.raceinfo import RaceInfo

match_library = {}


def invalidate_cache():
    global match_library
    match_library = {}


async def make_match(register=False, update=False, **kwargs) -> Optional[Match]:
    # noinspection PyIncorrectDocstring
    """Create a Match object.

    Parameters
    ----------
    racer_1_id: int
        The DB user ID of the first racer.
    racer_2_id: int
        The DB user ID of the second racer.
    max_races: int
        The maximum number of races this match can be. (If is_best_of is True, then the match is a best of
        max_races; otherwise, the match is just repeating max_races.)
    match_id: int
        The DB unique ID of this match. If this parameter is specified, the return value may be None, if no match
        in the database has the specified ID.
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
    match_info: MatchInfo
        The types of races to be run in this match.
    cawmentator_id: int
        The DB unique ID of the cawmentator for this match.
    sheet_id: int
        The sheetID of the worksheet the match was created from, if any.
    league_tag: str
        The tag for the league this match is in, if any.
    register: bool
        Whether to register the match in the database. 
    update: bool
        If match_id is given and this is True, updates the database match with any other specified parameters.
    
    Returns
    ---------
    Match
        The created match.
    """
    if 'match_id' in kwargs and kwargs['match_id'] is not None:
        cached_match = await get_match_from_id(kwargs['match_id'])
        if update and cached_match is not None:
            cached_match.raw_update(**kwargs)
            await cached_match.commit()
        return cached_match

    match = Match(commit_fn=matchdb.write_match, **kwargs)
    await match.initialize()
    if register:
        await match.commit()
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

    sheet_info = MatchGSheetInfo()
    sheet_info.wks_id = row[14]
    sheet_info.row = row[15]

    new_match = Match(
        commit_fn=matchdb.write_match,
        match_id=match_id,
        match_info=match_info,
        racer_1_id=int(row[2]),
        racer_2_id=int(row[3]),
        suggested_time=row[4],
        finish_time=row[16],
        r1_confirmed=bool(row[5]),
        r2_confirmed=bool(row[6]),
        r1_unconfirmed=bool(row[7]),
        r2_unconfirmed=bool(row[8]),
        cawmentator_id=row[12],
        channel_id=int(row[13]) if row[13] is not None else None,
        gsheet_info=sheet_info,
        autogenned=bool(row[17]),
        league_tag=row[18]
    )

    await new_match.initialize()
    match_library[new_match.match_id] = new_match
    return new_match


async def get_race_data(match: Match):
    return await matchdb.get_match_race_data(match.match_id)


async def match_exists_between(racer_1, racer_2) -> bool:
    prior_match_ids = await matchdb.get_matches_between(racer_1.user_id, racer_2.user_id)
    return bool(prior_match_ids)
