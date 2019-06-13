"""
Module for interacting with the speedruns table of the database.
"""

from necrobot.database.dbconnect import DBConnect
from necrobot.database.dbutil import tn
from necrobot.race import racedb
from necrobot.race.raceinfo import RaceInfo
from necrobot.user.necrouser import NecroUser


def submit(
        necro_user: NecroUser,
        category_race_info: RaceInfo,
        category_score: int,
        vod_url: str
) -> None:
    category_type_id = await racedb.get_race_type_id(race_info=category_race_info, register=True)

    params = (
        necro_user.user_id,
        category_type_id,
        category_score,
        vod_url
    )
    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO {speedruns}
            (user_id, type_id, score, vod)
            VALUES (%s, %s, %s, %s)
            """.format(speedruns=tn('speedruns')),
            params
        )
