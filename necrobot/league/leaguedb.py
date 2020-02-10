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
import datetime
from typing import Optional, List

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
               {leagues}.`worksheet_id`,
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
                worksheet_id=row[4]
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
               {leagues}.`worksheet_id`,
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
                worksheet_id=row[4]
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
            league.worksheet_id,
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
                `worksheet_id`, 
                `number_of_races`, 
                `is_best_of`, 
                `race_type`
            ) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE
               `league_tag` = VALUES(`league_tag`), 
               `league_name` = VALUES(`league_name`), 
               `worksheet_id` = VALUES(`worksheet_id`),
               `number_of_races` = VALUES(`number_of_races`), 
               `is_best_of` = VALUES(`is_best_of`), 
               `race_type` = VALUES(`race_type`)
            """.format(leagues=tn('leagues')),
            params
        )


async def get_matchstats_raw(league_tag: str, user_id: int) -> list:
    params = (user_id, league_tag,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS wins,
                MIN(winner_time) AS best_win,
                AVG(winner_time) AS average_win
            FROM {race_summary}
            WHERE `winner_id` = %s AND `league_tag` = %s
            LIMIT 1
            """.format(race_summary=tn('race_summary')),
            params
        )
        winner_data = cursor.fetchone()
        if winner_data is None:
            winner_data = [0, None, None]
        cursor.execute(
            """
            SELECT COUNT(*) AS losses
            FROM {race_summary}
            WHERE loser_id = %s AND `league_tag` = %s
            LIMIT 1
            """.format(race_summary=tn('race_summary')),
            params
        )
        loser_data = cursor.fetchone()
        if loser_data is None:
            loser_data = [0]
        return winner_data + loser_data


async def get_fastest_wins_raw(league_tag: str, limit: int = None) -> list:
    params = (league_tag, limit,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT
                {race_runs}.`time` AS `time`,
                users_winner.twitch_name AS winner_name,
                users_loser.twitch_name AS loser_name,
                {matches}.suggested_time AS match_time
            FROM 
                {match_races}
                INNER JOIN {matches}
                    ON {matches}.match_id = {match_races}.match_id
                INNER JOIN {races} 
                    ON {races}.race_id = {match_races}.race_id
                INNER JOIN users users_winner 
                    ON IF(
                        {match_races}.winner = 1,
                        users_winner.`user_id` = {matches}.racer_1_id,
                        users_winner.`user_id` = {matches}.racer_2_id
                    )
                INNER JOIN users users_loser 
                    ON IF(
                        {match_races}.winner = 1,
                        users_loser.user_id = {matches}.racer_2_id,
                        users_loser.user_id = {matches}.racer_1_id
                    )
                INNER JOIN {race_runs}
                    ON ( 
                        {race_runs}.race_id = {races}.race_id
                        AND {race_runs}.user_id = users_winner.user_id
                    )
            WHERE
                {match_races}.winner != 0
                AND {matches}.`league_tag` = %s
            ORDER BY `time` ASC
            LIMIT %s
            """.format(
                race_runs=tn('race_runs'),
                matches=tn('matches'),
                match_races=tn('match_races'),
                races=tn('races')
            ),
            params
        )
        return cursor.fetchall()


async def get_match_id(
        racer_1_id: int,
        racer_2_id: int,
        league_tag: Optional[str] = None,
        scheduled_time: datetime.datetime = None,
        finished_only: Optional[bool] = None
) -> int or None:
    """Attempt to find a match between the two racers

    If multiple matches are found, prioritize as follows:
        1. Prefer matches closer to scheduled_time, if scheduled_time is not None
        2. Prefer channeled matches
        3. Prefer the most recent scheduled match
        4. Randomly

    Parameters
    ----------
    league_tag: str
        The tag for the league to search in
    racer_1_id: int
        The user ID of the first racer
    racer_2_id: int
        The user ID of the second racer
    scheduled_time: datetime.datetime or None
        The approximate time to search around, or None to skip this priority
    finished_only: bool
        If not None, then: If True, only return matches that have a finish_time; if False, only return matches without

    Returns
    -------
    Optional[int]
        The match ID, if one is found.
    """
    param_dict = {
        'league_tag': league_tag,
        'racer1': racer_1_id,
        'racer2': racer_2_id,
        'time': scheduled_time
    }

    where_str = '(racer_1_id=%(racer1)s AND racer_2_id=%(racer2)s) ' \
                'OR (racer_1_id=%(racer2)s AND racer_2_id=%(racer1)s)'
    if league_tag is not None:
        where_str = '({old_str}) AND (league_tag=%(league_tag)s)'.format(
            old_str=where_str
        )
    if finished_only is not None:
        where_str = '({old_str}) AND (finish_time IS {nullstate})'.format(
            old_str=where_str,
            nullstate=('NOT NULL' if finished_only else 'NULL')
        )

    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT 
                {matches}.match_id, 
                {matches}.suggested_time, 
                {matches}.channel_id,
                ABS({matches}.`suggested_time` - '2017-23-04 12:00:00') AS abs_del
            FROM {matches}
            WHERE {where_str}
            ORDER BY
                IF(%(time)s IS NULL, 0, -ABS(`suggested_time` - %(time)s)) DESC,
                `channel_id` IS NULL ASC, 
                `suggested_time` DESC
            LIMIT 1
            """.format(matches=tn('matches'), where_str=where_str),
            param_dict
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None


async def get_standings_data_raw(league_tag: str):
    param_dict = {
        'league_tag': league_tag
    }
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT 
                {match_info}.racer_1_name,
                {match_info}.racer_2_name,
                {match_info}.racer_1_wins,
                {match_info}.racer_2_wins
            FROM {match_info}
            WHERE {match_info}.league_tag = %(league_tag)s AND {match_info}.completed
            """.format(match_info=tn('match_info')),
            param_dict
        )

        return cursor.fetchall()
