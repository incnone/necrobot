"""
Interaction with matches and match_races tables (in the necrobot schema, or a condor event schema).
"""

from necrobot.database import racedb
from necrobot.database.dbconnect import DBConnect
from necrobot.database.dbutil import tn
from necrobot.match.match import Match
from necrobot.match.matchracedata import MatchRaceData


def record_match_race(
        match: Match,
        race_number: int = None,
        race_id: int = None,
        winner: int = None,
        canceled: bool = False,
        contested: bool = False
        ) -> None:
    if race_number is None:
        race_number = _get_new_race_number(match)

    with DBConnect(commit=True) as cursor:
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


def set_match_race_contested(
        match: Match,
        race_number: int = None,
        contested: bool = True
        ) -> None:
    with DBConnect(commit=True) as cursor:
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


def change_winner(match: Match, race_number: int, winner: int) -> bool:
    race_to_change = _get_uncanceled_race_number(match=match, race_number=race_number)
    if race_to_change is None:
        return False

    with DBConnect(commit=True) as cursor:
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


def cancel_race(match: Match, race_number: int) -> bool:
    race_to_cancel = _get_uncanceled_race_number(match=match, race_number=race_number)
    if race_to_cancel is None:
        return False

    with DBConnect(commit=True) as cursor:
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


def write_match(match: Match):
    if not match.is_registered:
        _register_match(match)

    match_racetype_id = racedb.get_race_type_id(race_info=match.race_info, register=True)

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
        match.cawmentator.user_id if match.cawmentator else None,
        match.channel_id,
        match.match_id,
    )

    with DBConnect(commit=True) as cursor:
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
               channel_id=%s
            WHERE match_id=%s
            """.format(matches=tn('matches')),
            params
        )


def register_match_channel(match_id: int, channel_id: int or None) -> None:
    params = (channel_id, match_id,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE {matches}
            SET channel_id=%s
            WHERE match_id=%s
            """.format(matches=tn('matches')),
            params
        )


def get_match_channel_id(match_id: int) -> int:
    params = (match_id,)
    with DBConnect(commit=False) as cursor:
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


def get_channeled_matches_raw_data(
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

    with DBConnect(commit=False) as cursor:
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
                channel_id 
            FROM {matches} 
            WHERE {where_query} {order_query}
            """.format(matches=tn('matches'), where_query=where_query, order_query=order_query), params)
        return cursor.fetchall()


def delete_match(match_id: int):
    params = (match_id,)
    with DBConnect(commit=True) as cursor:
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


def get_match_race_data(match_id: int) -> MatchRaceData:
    params = (match_id,)
    with DBConnect(commit=False) as cursor:
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


def get_most_recent_scheduled_match_id_between(racer_1_id: int, racer_2_id: int, channeled=True) -> int or None:
    params = (racer_1_id, racer_2_id, racer_2_id, racer_1_id)
    where_query = '((racer_1_id=%s AND racer_2_id=%s) OR (racer_1_id=%s AND racer_2_id=%s))'
    if channeled:
        where_query += ' AND `channel_id` IS NOT NULL'

    with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT match_id 
            FROM {matches} 
            WHERE {where_query} 
            ORDER BY `suggested_time` DESC 
            LIMIT 1
            """.format(matches=tn('matches'), where_query=where_query),
            params
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None


def get_fastest_wins_raw(limit: int = None) -> list:
    params = (limit,)
    with DBConnect(commit=False) as cursor:
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


def get_matchstats_raw(user_id: int) -> list:
    params = (user_id,)
    with DBConnect(commit=False) as cursor:
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


def get_raw_match_data(match_id: int) -> list:
    params = (match_id,)

    with DBConnect(commit=False) as cursor:
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
               cawmentator_id 
            FROM {0} 
            WHERE match_id=%s 
            LIMIT 1
            """.format(tn('matches')),
            params
        )
        return cursor.fetchone()


def _register_match(match: Match) -> None:
    match_racetype_id = racedb.get_race_type_id(race_info=match.race_info, register=True)

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
        match.cawmentator.user_id if match.cawmentator else None,
    )

    with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO {0} 
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
            """.format(tn('matches')),
            params
        )
        cursor.execute("SELECT LAST_INSERT_ID()")
        match.set_match_id(int(cursor.fetchone()[0]))


def _get_uncanceled_race_number(match: Match, race_number: int) -> int or None:
    params = (match.match_id,)
    with DBConnect(commit=False) as cursor:
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


def _get_new_race_number(match: Match) -> int:
    params = (match.match_id,)
    with DBConnect(commit=False) as cursor:
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
