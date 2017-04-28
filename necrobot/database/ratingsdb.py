"""
Interaction with the necrobot.ratings table.
"""

from necrobot.ladder import ratingutil

from necrobot.database.dbconnect import DBConnect
from necrobot.ladder.rating import Rating


async def get_rating(discord_id: int) -> Rating:
    async with DBConnect(commit=False) as cursor:
        params = (discord_id,)
        cursor.execute(
            """
            SELECT trueskill_mu, trueskill_sigma 
            FROM ratings 
            WHERE discord_id=%s
            """,
            params
        )

        row = cursor.fetchone()
        if row is not None:
            return ratingutil.create_rating(mu=row[0], sigma=row[1])

    # If here, there was no rating
    async with DBConnect(commit=True) as cursor:
        rating = ratingutil.create_rating()
        params = (discord_id, rating.mu, rating.sigma,)
        cursor.execute(
            """
            INSERT INTO ratings 
            (discord_id, trueskill_mu, trueskill_sigma) 
            VALUES (%s, %s, %s)
            """,
            params
        )
        return rating


async def set_rating(discord_id: int, rating: Rating):
    async with DBConnect(commit=True) as cursor:
        params = (discord_id, rating.mu, rating.sigma,)
        cursor.execute(
            """
            INSERT INTO ratings 
                (discord_id, trueskill_mu, trueskill_sigma) 
            VALUES (%s,%s,%s) 
            ON DUPLICATE KEY UPDATE 
                trueskill_mu=VALUES(trueskill_mu), 
                trueskill_sigma=VALUES(trueskill_sigma)
            """,
            params)
