"""
Interaction with the users table.

Methods
-------
write_user
get_users_with_any
get_users_with_all
get_all_discord_ids_matching_prefs
register_discord_user
"""
import discord
import mysql.connector
from typing import Iterable

from necrobot.util import console

from necrobot.database.dbconnect import DBConnect
from necrobot.user.necrouser import NecroUser
from necrobot.user.userprefs import UserPrefs

# For making returns from these functions more friendly. Need async generators, so will be useful when this runs
# in py-3.6
# class UserRow(object):
#     """Raw data necessary to create a NecroUser object."""
#     select_params = """
#         user_id,
#         discord_id,
#         discord_name,
#         twitch_name,
#         rtmp_name,
#         timezone,
#         user_info,
#         daily_alert,
#         race_alert
#         """
#
#     def __init__(self, db_row):
#         self.user_id = db_row[0]            # type: int
#         self.discord_id = db_row[1]         # type: int
#         self.discord_name = db_row[2]       # type: str
#         self.twitch_name = db_row[3]        # type: str
#         self.rtmp_name = db_row[4]          # type: str
#         self.timezone = db_row[5]           # type: str
#         self.user_info = db_row[6]          # type: str
#         self.daily_alert = bool(db_row[7])  # type: bool
#         self.race_alert = bool(db_row[8])   # type: bool


# Commit function
async def write_user(necro_user: NecroUser) -> None:
    if necro_user.user_id is None:
        await _register_user(necro_user)
        return

    rtmp_clash_user_id = await _get_resolvable_rtmp_clash_user_id(necro_user)
    if rtmp_clash_user_id is not None:
        await _transfer_user_id(from_user_id=rtmp_clash_user_id, to_user_id=necro_user.user_id)

    params = (
        necro_user.discord_id,
        necro_user.discord_name,
        necro_user.twitch_name,
        necro_user.rtmp_name,
        necro_user.pronouns,
        necro_user.timezone_str,
        necro_user.user_info,
        necro_user.user_prefs.daily_alert,
        necro_user.user_prefs.race_alert,
        necro_user.user_id
    )

    async with DBConnect(commit=True) as cursor:
        if rtmp_clash_user_id is not None:
            rtmp_clash_params = (rtmp_clash_user_id,)
            cursor.execute(
                """
                DELETE FROM users 
                WHERE user_id=%s
                """,
                rtmp_clash_params
            )

        cursor.execute(
            """
            UPDATE users 
            SET 
               discord_id=%s, 
               discord_name=%s, 
               twitch_name=%s, 
               rtmp_name=%s,
               pronouns=%s, 
               timezone=%s, 
               user_info=%s, 
               daily_alert=%s, 
               race_alert=%s 
            WHERE user_id=%s
            """,
            params
        )


# Search
async def get_users_with_any(
        discord_id: int = None,
        discord_name: str = None,
        twitch_name: str = None,
        rtmp_name: str = None,
        timezone: str = None,
        user_id: int = None,
        case_sensitive: bool = False
):
    return await _get_users_helpfn(
        discord_id=discord_id,
        discord_name=discord_name,
        twitch_name=twitch_name,
        rtmp_name=rtmp_name,
        timezone=timezone,
        user_id=user_id,
        case_sensitive=case_sensitive,
        do_any=True
    )


async def get_all_users_with_any(names: Iterable[str]):
    async with DBConnect(commit=False) as cursor:
        if not names:
            return []
        params = tuple()
        for name in names:
            params += (name.lower(),)
        format_strings = ','.join(['%s'] * len(params))

        params = params + params + params
        print(params)

        cursor.execute(
            """
            SELECT 
               discord_id, 
               discord_name, 
               twitch_name, 
               rtmp_name, 
               timezone, 
               user_info, 
               daily_alert, 
               race_alert, 
               user_id,
               pronouns 
            FROM users 
            WHERE LOWER(discord_name) IN ({fm})
            OR LOWER(twitch_name) IN ({fm})
            OR LOWER(rtmp_name) IN ({fm})
            """.format(fm=format_strings),
            params
        )
        return cursor.fetchall()


async def get_users_with_all(
        discord_id: int = None,
        discord_name: str = None,
        twitch_name: str = None,
        rtmp_name: str = None,
        timezone: str = None,
        user_id: int = None,
        case_sensitive: bool = False
):
    return await _get_users_helpfn(
        discord_id=discord_id,
        discord_name=discord_name,
        twitch_name=twitch_name,
        rtmp_name=rtmp_name,
        timezone=timezone,
        user_id=user_id,
        case_sensitive=case_sensitive,
        do_any=False
    )


async def get_all_discord_ids_matching_prefs(user_prefs: UserPrefs) -> list:
    if user_prefs.is_empty:
        return []

    where_query = ''
    if user_prefs.daily_alert is not None:
        where_query += ' AND daily_alert={0}'.format('TRUE' if user_prefs.daily_alert else 'FALSE')
    if user_prefs.race_alert is not None:
        where_query += ' AND race_alert={0}'.format('TRUE' if user_prefs.race_alert else 'FALSE')
    where_query = where_query[5:]

    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT discord_id 
            FROM users 
            WHERE {0}
            """.format(where_query))
        to_return = []
        for row in cursor.fetchall():
            to_return.append(int(row[0]))
        return to_return


async def register_discord_user(user: discord.User):
    params = (user.id, user.display_name,)
    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO users 
                (discord_id, discord_name) 
            VALUES (%s, %s) 
            ON DUPLICATE KEY UPDATE 
                discord_name = VALUES(discord_name)
            """,
            params
        )


async def _get_users_helpfn(
        discord_id,
        discord_name,
        twitch_name,
        rtmp_name,
        timezone,
        user_id,
        case_sensitive,
        do_any
):
    async with DBConnect(commit=False) as cursor:
        params = tuple()
        if discord_id is not None:
            params += (int(discord_id),)
        if discord_name is not None:
            params += (discord_name,) if case_sensitive else (discord_name.lower(),)
        if twitch_name is not None:
            params += (twitch_name,) if case_sensitive else (twitch_name.lower(),)
        if rtmp_name is not None:
            params += (rtmp_name,) if case_sensitive else (rtmp_name.lower(),)
        if timezone is not None:
            params += (timezone,)
        if user_id is not None:
            params += (user_id,)

        connector = ' OR ' if do_any else ' AND '
        where_query = ''
        if discord_id is not None:
            where_query += ' {0} discord_id=%s'.format(connector)
        if discord_name is not None:
            where_query += ' {0} discord_name=%s'.format(connector) if case_sensitive \
                else ' {0} LOWER(discord_name)=%s'.format(connector)
        if twitch_name is not None:
            where_query += ' {0} twitch_name=%s'.format(connector) if case_sensitive \
                else ' {0} LOWER(twitch_name)=%s'.format(connector)
        if rtmp_name is not None:
            where_query += ' {0} rtmp_name=%s'.format(connector) if case_sensitive \
                else ' {0} LOWER(rtmp_name)=%s'.format(connector)
        if timezone is not None:
            where_query += ' {0} timezone=%s'.format(connector)
        if user_id is not None:
            where_query += ' {0} user_id=%s'.format(connector)
        where_query = where_query[len(connector):] if where_query else 'TRUE'

        cursor.execute(
            """
            SELECT 
               discord_id, 
               discord_name, 
               twitch_name, 
               rtmp_name, 
               timezone, 
               user_info, 
               daily_alert, 
               race_alert, 
               user_id,
               pronouns
            FROM users 
            WHERE {0}
            """.format(where_query),
            params)
        return cursor.fetchall()


async def _register_user(necro_user: NecroUser):
    rtmp_clash_user_id = await _get_resolvable_rtmp_clash_user_id(necro_user)

    params = (
        necro_user.discord_id,
        necro_user.discord_name,
        necro_user.twitch_name,
        necro_user.timezone_str,
        necro_user.user_info,
        necro_user.user_prefs.daily_alert,
        necro_user.user_prefs.race_alert,
        necro_user.rtmp_name,
    )

    async with DBConnect(commit=True) as cursor:
        if rtmp_clash_user_id is None:
            try:
                cursor.execute(
                    """
                    INSERT INTO users 
                    (discord_id, discord_name, twitch_name, timezone, user_info, daily_alert, race_alert, rtmp_name) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s) 
                    """,
                    params
                )
                cursor.execute("SELECT LAST_INSERT_ID()")
                uid = int(cursor.fetchone()[0])
                necro_user._user_id = uid
            except mysql.connector.IntegrityError:
                console.warning('Tried to insert a duplicate racer entry. Params: {0}'.format(params))
                raise
        else:
            cursor.execute(
                """
                UPDATE users 
                SET 
                   discord_id=%s, 
                   discord_name=%s, 
                   twitch_name=%s, 
                   timezone=%s, 
                   user_info=%s, 
                   daily_alert=%s, 
                   race_alert=%s 
                WHERE rtmp_name=%s
                """,
                params
            )
            necro_user._user_id = rtmp_clash_user_id


async def _get_resolvable_rtmp_clash_user_id(necro_user: NecroUser) -> int or None:
    """Returns the user ID of any entry in the DB with the same rtmp_name as necro_user, a NULL discord_id,
    and a different user ID, or None if no such entry exists.
    
    Parameters
    ----------
    necro_user: NecroUser
        The user to check for an already existing entry

    Returns
    -------
    Optional[int]
        The ID that can be overwritten, if any.
    """
    if necro_user.rtmp_name is None:
        return None

    rtmp_params = (necro_user.rtmp_name,)

    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `user_id`, `discord_id` 
            FROM `users` 
            WHERE `rtmp_name`=%s
            """,
            rtmp_params
        )

        data = cursor.fetchone()
        if data is None:
            return None

        user_id = int(data[0])
        discord_id = data[1]
        if discord_id is None and user_id != necro_user.user_id:
            return user_id
        else:
            return None


async def _transfer_user_id(from_user_id: int, to_user_id: int):
    """For all matches featuring the "from" user ID, update these racers to be the "to" user ID.   
    
    Updates the `matches` tables for the core necrobot, and the `matches` and `entrants` tables for all leagues.
    
    Does not update `race_runs` or `daily_runs` tables, since these should not contain entries with user IDs that
    are unregistered to discord IDs, and so there should be no records attached to `from_user_id` in those tables
    unless this coroutine is being called in error.
    
    WARNING: Possible severe loss of information. Use with caution! If used in error, consider trying to restore
    the `matches` and `entrants` tables by reading user IDs from the `race_runs` tables.
    
    Parameters
    ----------
    from_user_id: int
        The ID to search for in all match databases.
    to_user_id: int
        The ID to change to.
    """
    params = {
        'to_uid': to_user_id,
        'from_uid': from_user_id,
    }

    async with DBConnect(commit=True) as cursor:
        # Update main-database matches
        cursor.execute(
            """
            UPDATE matches 
            SET racer_1_id=%(to_uid)s 
            WHERE racer_1_id=%(from_uid)s
            """,
            params
        )
        cursor.execute(
            """
            UPDATE matches 
            SET racer_2_id=%(to_uid)s 
            WHERE racer_2_id=%(from_uid)s
            """,
            params
        )

        # Update leagues
        cursor.execute(
            """
            SELECT `schema_name` 
            FROM leagues 
            """
        )

        schema_names = []
        for row in cursor:
            schema_names.append(row[0])

        for schema_name in schema_names:
            cursor.execute(
                """
                UPDATE `{schema_name}`.entrants 
                SET user_id=%(to_uid)s 
                WHERE user_id=%(from_uid)s
                """.format(schema_name=schema_name),
                params
            )
            cursor.execute(
                """
                UPDATE `{schema_name}`.matches 
                SET racer_1_id=%(to_uid)s 
                WHERE racer_1_id=%(from_uid)s
                """.format(schema_name=schema_name),
                params
            )
            cursor.execute(
                """
                UPDATE `{schema_name}`.matches 
                SET racer_2_id=%(to_uid)s 
                WHERE racer_2_id=%(from_uid)s
                """.format(schema_name=schema_name),
                params
            )
