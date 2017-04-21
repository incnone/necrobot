from necrobot.database.racedb import get_race_type_id

from necrobot.database.dbconnect import DBConnect
from necrobot.race.match.matchracedata import MatchRaceData
from necrobot.race.raceinfo import RaceInfo


def record_match_race(match, race_number, race_id, winner, canceled, contested):
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
            "INSERT INTO match_races "
            "(match_id, race_number, race_id, winner, canceled, contested) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "   race_id=VALUES(race_id), "
            "   winner=VALUES(winner), "
            "   canceled=VALUES(canceled), "
            "   contested=VALUES(contested)",
            params
        )


def get_largest_race_number(discord_id):
    with DBConnect(commit=False) as cursor:
        params = (discord_id,)
        cursor.execute(
            "SELECT race_id "
            "FROM racer_data "
            "WHERE discord_id = %s "
            "ORDER BY race_id DESC "
            "LIMIT 1",
            params)
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0


def get_race_info_from_type_id(race_type):
    params = (race_type,)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT `character`, `descriptor`, `seeded`, `amplified`, `seed_fixed` "
            "FROM `race_types` "
            "WHERE `type_id`=%s",
            params
        )

        row = cursor.fetchone()
        if row is not None:
            race_info = RaceInfo()
            race_info.set_char(row[0])
            race_info.descriptor = row[1]
            race_info.seeded = bool(row[2])
            race_info.amplified = bool(row[3])
            race_info.seed_fixed = bool(row[4])
            return race_info
        else:
            return None


def write_match(match):
    if not match.is_registered:
        _register_match(match)

    match_racetype_id = get_race_type_id(race_info=match.race_info, register=True)

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
            "UPDATE match_data "
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
            "WHERE match_id=%s",
            params
        )


def register_match_channel(match_id: int, channel_id: int or None):
    params = (channel_id, match_id,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "UPDATE match_data "
            "SET channel_id=%s "
            "WHERE match_id=%s",
            params
        )


def get_match_channel_id(match_id: int) -> int:
    params = (match_id,)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT channel_id "
            "FROM match_data "
            "WHERE match_id=%s",
            params
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None


def get_channeled_matches_raw_data():
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
            "FROM match_data "
            "WHERE channel_id IS NOT NULL"
        )
        return cursor.fetchall()


def get_match_race_data(match_id: int) -> MatchRaceData:
    params = (match_id,)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT canceled, winner "
            "FROM `match_races` "
            "WHERE match_id=%s",
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
            "FROM match_data "
            "WHERE (racer_1_id=%s AND racer_2_id=%s) OR (racer_1_id=%s AND racer_2_id=%s)",
            params
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None


def add_cawmentary(match_id: int, cawmentator_id: int or None):
    params = (cawmentator_id, match_id,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "UPDATE match_data "
            "SET cawmentator_id=%s "
            "WHERE match_id=%s",
            params
        )


def get_cawmentary(match_id: int) -> int or None:
    params = (match_id,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "SELECT cawmentator_id "
            "FROM match_data "
            "WHERE match_id=%s",
            params
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None


def get_raw_match_data(match_id):
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
            "FROM match_data "
            "WHERE match_id=%s",
            params
        )
        return cursor.fetchone()


def _register_match(match):
    match_racetype_id = get_race_type_id(race_info=match.race_info, register=True)

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
            "INSERT INTO match_data "
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
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            params
        )
        cursor.execute("SELECT LAST_INSERT_ID()")
        match.set_match_id(int(cursor.fetchone()[0]))