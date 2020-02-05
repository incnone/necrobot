"""
Interaction with the necrobot.leagues table.

Methods
-------
create_league(schema_name: str) -> None
    Make a new league.
get_league(schema_name: str) -> League
    Get a registered league.
get_entrant_ids() -> list[int]
    Get the NecroUser IDs of all entrants.
register_user(user_id: int) -> None
    Register a user in the `entrants` table.
write_league(League) -> None
    Write information in an already registered league to the database.

Exceptions
----------
LeagueAlreadyExists
LeagueDoesNotExist
InvalidSchemaName
"""
from typing import List

import necrobot.exception
from necrobot.database.dbconnect import DBConnect
from necrobot.database.dbutil import tn
from necrobot.league.league import League
from necrobot.match.matchinfo import MatchInfo
from necrobot.race.raceinfo import RaceInfo
from necrobot.race import racedb


async def get_entrant_ids() -> list:
    """Get NecroUser IDs for all entrants to the league
    
    Returns
    -------
    list[int]
    """
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `user_id`
            FROM {entrants}
            """.format(entrants=tn('entrants'))
        )
        to_return = []
        for row in cursor:
            to_return.append(int(row[0]))
        return to_return


async def get_league(league_tag: str) -> League:
    """
    Parameters
    ----------
    league_tag: str
        The unique identifier for the league

    Returns
    -------
    League
        A League object for the event.
    """
    params = (league_tag,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT 
               {leagues}.`league_tag`, 
               {leagues}.`league_name`, 
               {leagues}.`number_of_races`, 
               {leagues}.`is_best_of`, 
               {leagues}.`gsheet_id`,
               `race_types`.`character`, 
               `race_types`.`descriptor`, 
               `race_types`.`seeded`, 
               `race_types`.`amplified`, 
               `race_types`.`seed_fixed`
            FROM {leagues}
            LEFT JOIN `race_types` ON `leagues`.`race_type` = `race_types`.`type_id` 
            WHERE {leagues}.`league_tag` = %s 
            LIMIT 1
            """.format(leagues=tn('leagues')),
            params
        )
        for row in cursor:
            race_info = RaceInfo()
            if row[5] is not None:
                race_info.set_char(row[5])
            if row[6] is not None:
                race_info.descriptor = row[6]
            if row[7] is not None:
                race_info.seeded = bool(row[7])
            if row[8] is not None:
                race_info.amplified = bool(row[8])
            if row[9] is not None:
                race_info.seed_fixed = bool(row[9])

            match_info = MatchInfo(
                max_races=int(row[2]) if row[2] is not None else None,
                is_best_of=bool(row[3]) if row[3] is not None else None,
                ranked=None,
                race_info=race_info
            )

            return League(
                commit_fn=write_league,
                league_tag=row[0],
                league_name=row[1],
                match_info=match_info,
                gsheet_id=row[4]
            )

        raise necrobot.exception.LeagueDoesNotExist()


async def get_all_leagues() -> List[League]:
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT 
               {leagues}.`league_tag`, 
               {leagues}.`league_name`, 
               {leagues}.`number_of_races`, 
               {leagues}.`is_best_of`, 
               {leagues}.`gsheet_id`,
               `race_types`.`character`, 
               `race_types`.`descriptor`, 
               `race_types`.`seeded`, 
               `race_types`.`amplified`, 
               `race_types`.`seed_fixed`
            FROM {leagues}
            LEFT JOIN `race_types` ON `leagues`.`race_type` = `race_types`.`type_id` 
            """.format(leagues=tn('leagues'))
        )
        all_leagues = []
        for row in cursor:
            race_info = RaceInfo()
            if row[5] is not None:
                race_info.set_char(row[5])
            if row[6] is not None:
                race_info.descriptor = row[6]
            if row[7] is not None:
                race_info.seeded = bool(row[7])
            if row[8] is not None:
                race_info.amplified = bool(row[8])
            if row[9] is not None:
                race_info.seed_fixed = bool(row[9])

            match_info = MatchInfo(
                max_races=int(row[2]) if row[2] is not None else None,
                is_best_of=bool(row[3]) if row[3] is not None else None,
                ranked=None,
                race_info=race_info
            )

            all_leagues.append(League(
                commit_fn=write_league,
                league_tag=row[0],
                league_name=row[1],
                match_info=match_info,
                gsheet_id=row[4]
            ))
        return all_leagues


async def register_user(user_id: int) -> None:
    """Register the user for the league
    
    Parameters
    ----------
    user_id: int
        The user's NecroUser ID.
    """
    async with DBConnect(commit=True) as cursor:
        params = (user_id,)
        cursor.execute(
            """
            INSERT INTO {entrants}
                (user_id)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE
                user_id = VALUES(user_id)
            """.format(entrants=tn('entrants')),
            params
        )


async def assign_match(match_id: int, league_tag: str):
    async with DBConnect(commit=True) as cursor:
        params = (match_id, league_tag)
        cursor.execute(
            """
            INSERT INTO {league_matches}
                (`match_id`, `league_tag`)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                `match_id` = VALUES(`match_id`),
                `league_tag` = VALUES(`league_tag`)
            """.format(league_matches=tn('league_matches')),
            params
        )


async def write_league(league: League) -> None:
    """Write the league to the database
    
    Parameters
    ----------
    league: League
        The league object to be written. Will create a new row if the schema_name is not in the database, and
        update otherwise.
    """
    match_info = league.match_info
    race_type_id = await racedb.get_race_type_id(race_info=match_info.race_info, register=True)

    async with DBConnect(commit=True) as cursor:
        params = (
            league.tag,
            league.name,
            league.gsheet_id,
            match_info.max_races,
            match_info.is_best_of,
            race_type_id,
        )

        cursor.execute(
            """
            INSERT INTO {leagues}
            (
                `league_tag`, 
                `league_name`, 
                `gsheet_id`, 
                `number_of_races`, 
                `is_best_of`, 
                `race_type`
            ) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE
               `league_tag` = VALUES(`league_tag`), 
               `league_name` = VALUES(`league_name`), 
               `gsheet_id` = VALUES(`gsheet_id`),
               `number_of_races` = VALUES(`number_of_races`), 
               `is_best_of` = VALUES(`is_best_of`), 
               `race_type` = VALUES(`race_type`)
            """.format(leagues=tn('leagues')),
            params
        )
