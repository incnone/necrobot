"""
Interaction with matches and match_races tables (in the necrobot schema, or a condor event schema).
"""

from necrobot.config import Config
from necrobot.database import racedb
from necrobot.database.dbconnect import DBConnect
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
            "INSERT INTO {0} "
            "(match_id, race_number, race_id, winner, canceled, contested) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "   race_id=VALUES(race_id), "
            "   winner=VALUES(winner), "
            "   canceled=VALUES(canceled), "
            "   contested=VALUES(contested)".format(_t('match_races')),
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
            "UPDATE {0} "
            "SET `winner` = %s "
            "WHERE `match_id` = %s AND `race_number` = %s".format(_t('match_races')),
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
            "UPDATE {0} "
            "SET `canceled` = TRUE "
            "WHERE `match_id` = %s AND `race_number` = %s".format(_t('match_races')),
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
        match.match_id,
    )

    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "UPDATE {0} "
            "SET "
            "   race_type_id=%s, "
            "   racer_1_id=%s, "
            "   racer_2_id=%s, "
            "   suggested_time=%s, "
            "   r1_confirmed=%s, "
            "   r2_confirmed=%s, "
            "   r1_unconfirmed=%s, "
            "   r2_unconfirmed=%s, "
            "   ranked=%s, "
            "   is_best_of=%s, "
            "   number_of_races=%s, "
            "   cawmentator_id=%s "
            "WHERE match_id=%s".format(_t('matches')),
            params
        )


def register_match_channel(match_id: int, channel_id: int or None) -> None:
    params = (channel_id, match_id,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "UPDATE {0} "
            "SET channel_id=%s "
            "WHERE match_id=%s".format(_t('matches')),
            params
        )


def get_match_channel_id(match_id: int) -> int:
    params = (match_id,)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT channel_id "
            "FROM {0} "
            "WHERE match_id=%s".format(_t('matches')),
            params
        )
        row = cursor.fetchone()
        return int(row[0]) if row[0] is not None else None


def get_channeled_matches_raw_data() -> list:
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT "
            "   match_id, "
            "   race_type_id, "
            "   racer_1_id, "
            "   racer_2_id, "
            "   suggested_time, "
            "   r1_confirmed, "
            "   r2_confirmed, "
            "   r1_unconfirmed, "
            "   r2_unconfirmed, "
            "   ranked, "
            "   is_best_of, "
            "   number_of_races, "
            "   cawmentator_id, "
            "   channel_id "
            "FROM {0} "
            "WHERE channel_id IS NOT NULL".format(_t('matches'))
        )
        return cursor.fetchall()


def get_match_race_data(match_id: int) -> MatchRaceData:
    params = (match_id,)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT canceled, winner "
            "FROM {0} "
            "WHERE match_id=%s".format(_t('match_races')),
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


def get_most_recent_scheduled_match_id_between(racer_1_id: int, racer_2_id: int) -> int or None:
    params = (racer_1_id, racer_2_id, racer_2_id, racer_1_id)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT match_id "
            "FROM {0} "
            "WHERE (racer_1_id=%s AND racer_2_id=%s) OR (racer_1_id=%s AND racer_2_id=%s)".format(_t('matches')),
            params
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None


def get_raw_match_data(match_id: int) -> list:
    params = (match_id,)

    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT "
            "   match_id, "
            "   race_type_id, "
            "   racer_1_id, "
            "   racer_2_id, "
            "   suggested_time, "
            "   r1_confirmed, "
            "   r2_confirmed, "
            "   r1_unconfirmed, "
            "   r2_unconfirmed, "
            "   ranked, "
            "   is_best_of, "
            "   number_of_races, "
            "   cawmentator_id "
            "FROM {0} "
            "WHERE match_id=%s".format(_t('matches')),
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
            "INSERT INTO {0} "
            "("
            "   race_type_id, "
            "   racer_1_id, "
            "   racer_2_id, "
            "   suggested_time, "
            "   r1_confirmed, "
            "   r2_confirmed, "
            "   r1_unconfirmed, "
            "   r2_unconfirmed, "
            "   ranked, "
            "   is_best_of, "
            "   number_of_races, "
            "   cawmentator_id"
            ")"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)".format(_t('matches')),
            params
        )
        cursor.execute("SELECT LAST_INSERT_ID()")
        match.set_match_id(int(cursor.fetchone()[0]))


def _get_uncanceled_race_number(match: Match, race_number: int) -> int or None:
    params = (match.match_id,)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT `race_number` "
            "FROM {0} "
            "WHERE `match_id` = %s AND `canceled` = FALSE "
            "ORDER BY `race_number` ASC".format(_t('match_races')),
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
            "SELECT `race_number` "
            "FROM {0} "
            "WHERE `match_id` = %s "
            "ORDER BY `race_number` DESC "
            "LIMIT 1".format(_t('match_races')),
            params
        )
        return int(cursor.fetchone()[0]) + 1


def _t(tablename: str) -> str:
    return '`{0}`.`{1}`'.format(Config.CONDOR_EVENT, tablename) if Config.CONDOR_EVENT else '`{0}`'.format(tablename)
