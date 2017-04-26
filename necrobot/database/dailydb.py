"""
Interaction with the necrobot.dailies and necrobot.daily_runs tables.
"""

from necrobot.database.dbconnect import DBConnect
import necrobot.util.level


def get_daily_seed(daily_id, daily_type):
    with DBConnect(commit=False) as cursor:
        params = (daily_id, daily_type,)
        cursor.execute(
            """
            SELECT seed
            FROM dailies
            WHERE daily_id=%s AND type=%s
            """,
            params)
        return cursor.fetchall()


def get_daily_times(daily_id, daily_type):
    with DBConnect(commit=False) as cursor:
        params = (daily_id, daily_type,)
        cursor.execute(
            """
            SELECT users.discord_name,daily_runs.level,daily_runs.time
            FROM daily_runs 
                INNER JOIN users ON daily_runs.user_id=users.user_id
            WHERE daily_runs.daily_id=%s AND daily_runs.type=%s
            ORDER BY daily_runs.level DESC, daily_runs.time ASC
            """,
            params)
        return cursor.fetchall()


def has_submitted_daily(discord_id, daily_id, daily_type):
    with DBConnect(commit=False) as cursor:
        params = (discord_id, daily_id, daily_type,)
        cursor.execute(
            """
            SELECT discord_id
            FROM daily_runs_uinfo
            WHERE discord_id=%s AND daily_id=%s AND type=%s AND level != -1
            """,
            params)
        return cursor.fetchone() is not None


def has_registered_daily(discord_id, daily_id, daily_type):
    with DBConnect(commit=False) as cursor:
        params = (discord_id, daily_id, daily_type,)
        cursor.execute(
            """
            SELECT discord_id
            FROM daily_runs_uinfo
            WHERE discord_id=%s AND daily_id=%s AND type=%s
            """,
            params)
        return cursor.fetchone() is not None


def register_daily(user_id, daily_id, daily_type, level=necrobot.util.level.LEVEL_NOS, time=-1):
    with DBConnect(commit=True) as cursor:
        params = (user_id, daily_id, daily_type, level, time,)
        cursor.execute(
            """
            INSERT INTO daily_runs
                (user_id, daily_id, type, level, time)
            VALUES (%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                user_id=VALUES(user_id),
                daily_id=VALUES(daily_id),
                type=VALUES(type),
                level=VALUES(level),
                time=VALUES(time)
            """,
            params)


def registered_daily(discord_id, daily_type):
    with DBConnect(commit=False) as cursor:
        params = (discord_id, daily_type,)
        cursor.execute(
            """
            SELECT daily_id
            FROM daily_runs_uinfo
            WHERE discord_id=%s AND type=%s
            ORDER BY daily_id DESC
            LIMIT 1
            """,
            params)
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0


def submitted_daily(discord_id, daily_type):
    with DBConnect(commit=False) as cursor:
        params = (discord_id, daily_type,)
        cursor.execute(
            """
            SELECT daily_id 
            FROM daily_runs_uinfo 
            WHERE discord_id=%s AND type=%s AND level != -1
            ORDER BY daily_id DESC 
            LIMIT 1
            """,
            params)
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0


def delete_from_daily(discord_id, daily_id, daily_type):
    with DBConnect(commit=True) as cursor:
        params = (discord_id, daily_id, daily_type,)
        cursor.execute(
            """
            UPDATE daily_runs_uinfo 
            SET level=-1 
            WHERE discord_id=%s AND daily_id=%s AND type=%s
            """,
            params)


def create_daily(daily_id, daily_type, seed, message_id=0):
    with DBConnect(commit=True) as cursor:
        params = (daily_id, daily_type, seed, message_id)
        cursor.execute(
            """
            INSERT INTO dailies 
            (daily_id, type, seed, msg_id) 
            VALUES (%s,%s,%s,%s)
            """,
            params)


def register_daily_message(daily_id, daily_type, message_id):
    with DBConnect(commit=True) as cursor:
        params = (message_id, daily_id, daily_type,)
        cursor.execute(
            """
            UPDATE dailies 
            SET msg_id=%s 
            WHERE daily_id=%s AND type=%s
            """,
            params)


def get_daily_message_id(daily_id, daily_type):
    with DBConnect(commit=False) as cursor:
        params = (daily_id, daily_type,)
        cursor.execute(
            """
            SELECT msg_id 
            FROM dailies 
            WHERE daily_id=%s AND type=%s
            """,
            params)
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0
