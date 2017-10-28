"""
Interaction with the necrobot.ratings table.
"""

from necrobot.ladder import ratingutil

from necrobot.database.dbconnect import DBConnect
from necrobot.ladder.rating import Rating


async def get_rating(user_id: int) -> Rating:
    async with DBConnect(commit=False) as cursor:
        params = (user_id,)
        cursor.execute(
            """
            SELECT trueskill_mu, trueskill_sigma 
            FROM ratings 
            WHERE user_id=%s
            """,
            params
        )

        row = cursor.fetchone()
        if row is not None:
            return ratingutil.create_rating(mu=row[0], sigma=row[1])

    # If here, there was no rating
    async with DBConnect(commit=True) as cursor:
        rating = ratingutil.create_rating()
        params = (user_id, rating.mu, rating.sigma,)
        cursor.execute(
            """
            INSERT INTO ratings 
            (user_id, trueskill_mu, trueskill_sigma) 
            VALUES (%s, %s, %s)
            """,
            params
        )
        return rating


async def set_rating(user_id: int, rating: Rating):
    async with DBConnect(commit=True) as cursor:
        params = (user_id, rating.mu, rating.sigma,)
        cursor.execute(
            """
            INSERT INTO ratings 
                (user_id, trueskill_mu, trueskill_sigma) 
            VALUES (%s,%s,%s) 
            ON DUPLICATE KEY UPDATE 
                trueskill_mu=VALUES(trueskill_mu), 
                trueskill_sigma=VALUES(trueskill_sigma)
            """,
            params)
