"""
Interaction with matches and match_races tables (in the necrobot schema, or a condor event schema).
"""
import datetime

from necrobot.database import racedb
from necrobot.database.dbconnect import DBConnect
from necrobot.database.dbutil import tn
from necrobot.match.match import Match
from necrobot.match.matchracedata import MatchRaceData


async def record_match_race(
        match: Match,
        race_number: int = None,
        race_id: int = None,
        winner: int = None,
        canceled: bool = False,
        contested: bool = False
        ) -> None:
    if race_number is None:
        race_number = await _get_new_race_number(match)

    async with DBConnect(commit=True) as cursor:
        params = (
            match.match_id,
            race_number,
            race_id,
            winner,
            canceled,
            contested
        )

        cursor.execute(
            """
            INSERT INTO {match_races} 
            (match_id, race_number, race_id, winner, canceled, contested) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE 
               race_id=VALUES(race_id), 
               winner=VALUES(winner), 
               canceled=VALUES(canceled), 
               contested=VALUES(contested)
            """.format(match_races=tn('match_races')),
            params
        )


async def set_match_race_contested(
        match: Match,
        race_number: int = None,
        contested: bool = True
        ) -> None:
    async with DBConnect(commit=True) as cursor:
        params = (
            contested,
            match.match_id,
            race_number,
        )

        cursor.execute(
            """
            UPDATE {match_races}
            SET `contested`=%s
            WHERE `match_id`=%s AND `race_number`=%s
            """.format(match_races=tn('match_races')),
            params
        )


async def change_winner(match: Match, race_number: int, winner: int) -> bool:
    race_to_change = await _get_uncanceled_race_number(match=match, race_number=race_number)
    if race_to_change is None:
        return False

    async with DBConnect(commit=True) as cursor:
        params = (
            winner,
            match.match_id,
            race_to_change,
        )

        cursor.execute(
            """
            UPDATE {match_races}
            SET `winner` = %s
            WHERE `match_id` = %s AND `race_number` = %s
            """.format(match_races=tn('match_races')),
            params
        )
        return True


async def cancel_race(match: Match, race_number: int) -> bool:
    race_to_cancel = await _get_uncanceled_race_number(match=match, race_number=race_number)
    if race_to_cancel is None:
        return False

    async with DBConnect(commit=True) as cursor:
        params = (
            match.match_id,
            race_to_cancel,
        )

        cursor.execute(
            """
            UPDATE {match_races}
            SET `canceled` = TRUE
            WHERE `match_id` = %s AND `race_number` = %s
            """.format(match_races=tn('match_races')),
            params
        )
        return True


async def write_match(match: Match):
    if not match.is_registered:
        await _register_match(match)

    match_racetype_id = await racedb.get_race_type_id(race_info=match.race_info, register=True)

    params = (
        match_racetype_id,
        match.racer_1.user_id,
        match.racer_2.user_id,
        match.suggested_time,
        match.confirmed_by_r1,
        match.confirmed_by_r2,
        match.r1_wishes_to_unconfirm,
        match.r2_wishes_to_unconfirm,
        match.ranked,
        match.is_best_of,
        match.number_of_races,
        match.cawmentator_id,
        match.channel_id,
        match.sheet_id,
        match.sheet_row,
        match.match_id,
    )

    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE {matches}
            SET
               race_type_id=%s,
               racer_1_id=%s,
               racer_2_id=%s,
               suggested_time=%s,
               r1_confirmed=%s,
               r2_confirmed=%s,
               r1_unconfirmed=%s,
               r2_unconfirmed=%s,
               ranked=%s,
               is_best_of=%s,
               number_of_races=%s,
               cawmentator_id=%s,
               channel_id=%s,
               sheet_id=%s,
               sheet_row=%s
            WHERE match_id=%s
            """.format(matches=tn('matches')),
            params
        )


async def register_match_channel(match_id: int, channel_id: int or None) -> None:
    params = (channel_id, match_id,)
    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE {matches}
            SET channel_id=%s
            WHERE match_id=%s
            """.format(matches=tn('matches')),
            params
        )


async def get_match_channel_id(match_id: int) -> int:
    params = (match_id,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT channel_id 
            FROM {matches} 
            WHERE match_id=%s 
            LIMIT 1
            """.format(matches=tn('matches')),
            params
        )
        row = cursor.fetchone()
        return int(row[0]) if row[0] is not None else None


async def get_channeled_matches_raw_data(
        must_be_scheduled: bool = False,
        order_by_time: bool = False,
        racer_id: int = None
) -> list:
    params = tuple()

    where_query = "`channel_id` IS NOT NULL"
    if must_be_scheduled:
        where_query += " AND (`suggested_time` IS NOT NULL AND `r1_confirmed` AND `r2_confirmed`)"
    if racer_id is not None:
        where_query += " AND (`racer_1_id` = %s OR `racer_2_id` = %s)"
        params += (racer_id, racer_id,)

    order_query = ''
    if order_by_time:
        order_query = "ORDER BY `suggested_time` ASC"

    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT 
                 match_id, 
                 race_type_id, 
                 racer_1_id, 
                 racer_2_id, 
                 suggested_time, 
                 r1_confirmed, 
                 r2_confirmed, 
                 r1_unconfirmed, 
                 r2_unconfirmed, 
                 ranked, 
                 is_best_of, 
                 number_of_races, 
                 cawmentator_id, 
                 channel_id,
                 sheet_id,
                 sheet_row
            FROM {matches} 
            WHERE {where_query} {order_query}
            """.format(matches=tn('matches'), where_query=where_query, order_query=order_query), params)
        return cursor.fetchall()


async def delete_match(match_id: int):
    params = (match_id,)
    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            DELETE FROM {match_races} 
            WHERE `match_id`=%s
            """.format(match_races=tn('match_races')),
            params
        )
        cursor.execute(
            """
            DELETE FROM {matches} 
            WHERE `match_id`=%s
            """.format(matches=tn('matches')),
            params
        )


async def get_match_race_data(match_id: int) -> MatchRaceData:
    params = (match_id,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT canceled, winner 
            FROM {match_races} 
            WHERE match_id=%s
            """.format(match_races=tn('match_races')),
            params
        )
        finished = 0
        canceled = 0
        r1_wins = 0
        r2_wins = 0
        for row in cursor:
            if bool(row[0]):
                canceled += 1
            else:
                finished += 1
                if int(row[1]) == 1:
                    r1_wins += 1
                elif int(row[1]) == 2:
                    r2_wins += 1
        return MatchRaceData(finished=finished, canceled=canceled, r1_wins=r1_wins, r2_wins=r2_wins)


async def get_match_id(
        racer_1_id: int,
        racer_2_id: int,
        scheduled_time: datetime.datetime = None
) -> int or None:
    """Attempt to find a match between the two racers
    
    If multiple matches are found, prioritize as follows: 
        1. Prefer matches closer to scheduled_time, if scheduled_time is not None
        2. Prefer channeled matches
        3. Prefer the most recent scheduled match
        4. Randomly
    
    Parameters
    ----------
    racer_1_id: int
        The user ID of the first racer
    racer_2_id: int
        The user ID of the second racer
    scheduled_time: datetime.datetime or None
        The approximate time to search around, or None to skip this priority

    Returns
    -------
    Optional[int]
        The match ID, if one is found.
    """
    param_dict = {
        'racer1': racer_1_id,
        'racer2': racer_2_id,
        'time': scheduled_time
    }

    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT 
                match_id, 
                suggested_time, 
                channel_id,
                ABS(`suggested_time` - '2017-23-04 12:00:00') AS abs_del
            FROM {matches}
            WHERE 
                (racer_1_id=%(racer1)s AND racer_2_id=%(racer2)s) OR (racer_1_id=%(racer2)s AND racer_2_id=%(racer1)s)
            ORDER BY
                IF(%(time)s IS NULL, 0, -ABS(`suggested_time` - %(time)s)) DESC,
                `channel_id` IS NULL ASC, 
                `suggested_time` DESC
            LIMIT 1
            """.format(matches=tn('matches')),
            param_dict
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None


async def get_fastest_wins_raw(limit: int = None) -> list:
    params = (limit,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT
                {race_runs}.`time` AS `time`,
                users_winner.rtmp_name AS winner_name,
                users_loser.rtmp_name AS loser_name,
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


async def get_matchstats_raw(user_id: int) -> list:
    params = (user_id,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS wins,
                MIN(winner_time) AS best_win,
                AVG(winner_time) AS average_win
            FROM {race_summary}
            WHERE winner_id = %s
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
            WHERE loser_id = %s
            LIMIT 1
            """.format(race_summary=tn('race_summary')),
            params
        )
        loser_data = cursor.fetchone()
        if loser_data is None:
            loser_data = [0]
        return winner_data + loser_data


async def get_raw_match_data(match_id: int) -> list:
    params = (match_id,)

    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT 
                 match_id, 
                 race_type_id, 
                 racer_1_id, 
                 racer_2_id, 
                 suggested_time, 
                 r1_confirmed, 
                 r2_confirmed, 
                 r1_unconfirmed, 
                 r2_unconfirmed, 
                 ranked, 
                 is_best_of, 
                 number_of_races, 
                 cawmentator_id, 
                 channel_id,
                 sheet_id,
                 sheet_row
            FROM {matches} 
            WHERE match_id=%s 
            LIMIT 1
            """.format(matches=tn('matches')),
            params
        )
        return cursor.fetchone()


async def _register_match(match: Match) -> None:
    match_racetype_id = await racedb.get_race_type_id(race_info=match.race_info, register=True)

    params = (
        match_racetype_id,
        match.racer_1.user_id,
        match.racer_2.user_id,
        match.suggested_time,
        match.confirmed_by_r1,
        match.confirmed_by_r2,
        match.r1_wishes_to_unconfirm,
        match.r2_wishes_to_unconfirm,
        match.ranked,
        match.is_best_of,
        match.number_of_races,
        match.cawmentator_id,
    )

    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO {matches} 
            (
               race_type_id, 
               racer_1_id, 
               racer_2_id, 
               suggested_time, 
               r1_confirmed, 
               r2_confirmed, 
               r1_unconfirmed, 
               r2_unconfirmed, 
               ranked, 
               is_best_of, 
               number_of_races, 
               cawmentator_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """.format(matches=tn('matches')),
            params
        )
        cursor.execute("SELECT LAST_INSERT_ID()")
        match.set_match_id(int(cursor.fetchone()[0]))

        params = (match.racer_1.user_id, match.racer_2.user_id,)
        cursor.execute(
            """
            INSERT IGNORE INTO {entrants} (user_id)
            VALUES (%s), (%s)
            """.format(entrants=tn('entrants')),
            params
        )


async def _get_uncanceled_race_number(match: Match, race_number: int) -> int or None:
    params = (match.match_id,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `race_number` 
            FROM {0} 
            WHERE `match_id` = %s AND `canceled` = FALSE 
            ORDER BY `race_number` ASC
            """.format(tn('match_races')),
            params
        )
        races = cursor.fetchall()
        if len(races) < race_number:
            return None

        return int(races[race_number - 1][0])


async def _get_new_race_number(match: Match) -> int:
    params = (match.match_id,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `race_number` 
            FROM {0} 
            WHERE `match_id` = %s 
            ORDER BY `race_number` DESC 
            LIMIT 1
            """.format(tn('match_races')),
            params
        )
        row = cursor.fetchone()
        return int(row[0]) + 1 if row is not None else 1
