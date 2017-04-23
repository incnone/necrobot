"""
Interaction with the necrobot.ladder_data table.
"""

from necrobot.ladder import ratingutil

from necrobot.database.dbconnect import DBConnect
from necrobot.ladder.rating import Rating


def get_rating(discord_id: int) -> Rating:
    with DBConnect(commit=False) as cursor:
        params = (discord_id,)
        cursor.execute(
            "SELECT trueskill_mu, trueskill_sigma "
            "FROM ladder_data "
            "WHERE discord_id=%s",
            params
        )

        row = cursor.fetchone()
        if row is not None:
            return ratingutil.create_rating(mu=row[0], sigma=row[1])

    # If here, there was no rating
    with DBConnect(commit=True) as cursor:
        rating = ratingutil.create_rating()
        params = (discord_id, rating.mu, rating.sigma,)
        cursor.execute(
            "INSERT INTO ladder_data "
            "(discord_id, trueskill_mu, trueskill_sigma) "
            "VALUES (%s, %s, %s)",
            params
        )
        return rating


def set_rating(discord_id: int, rating: Rating):
    with DBConnect(commit=True) as cursor:
        params = (discord_id, rating.mu, rating.sigma,)
        cursor.execute(
            "INSERT INTO ladder_data "
            "(discord_id, trueskill_mu, trueskill_sigma) "
            "VALUES (%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE "
            "trueskill_mu=VALUES(trueskill_mu), "
            "trueskill_sigma=VALUES(trueskill_sigma)",
            params)
