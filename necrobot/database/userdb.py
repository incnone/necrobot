import mysql.connector
from necrobot.util import console

from necrobot.database.dbconnect import DBConnect
from necrobot.user.necrouser import NecroUser
from necrobot.user.userprefs import UserPrefs


# Commit function
def write_user(necro_user: NecroUser):
    if necro_user.user_id is None:
        _register_user(necro_user)
        return

    rtmp_clash_user_id = _get_resolvable_rtmp_clash_user_id(necro_user)
    if rtmp_clash_user_id is not None:
        _transfer_user_id(from_user_id=rtmp_clash_user_id, to_user_id=necro_user.user_id)

    params = (
        necro_user.discord_id,
        necro_user.discord_name,
        necro_user.twitch_name,
        necro_user.rtmp_name,
        necro_user.timezone,
        necro_user.user_info,
        necro_user.user_prefs.daily_alert,
        necro_user.user_prefs.race_alert,
        necro_user.user_id
    )

    with DBConnect(commit=True) as cursor:
        if rtmp_clash_user_id is not None:
            rtmp_clash_params = (rtmp_clash_user_id,)
            cursor.execute(
                "DELETE FROM user_data "
                "WHERE user_id=%s",
                rtmp_clash_params
            )

        cursor.execute(
            "UPDATE user_data "
            "SET "
            "   discord_id=%s, "
            "   discord_name=%s, "
            "   twitch_name=%s, "
            "   rtmp_name=%s, "
            "   timezone=%s, "
            "   user_info=%s, "
            "   daily_alert=%s, "
            "   race_alert=%s "
            "WHERE user_id=%s",
            params
        )

    valid_user_ids[necro_user.user_id] = True


# Search
def get_users_with_any(
        discord_id=None,
        discord_name=None,
        twitch_name=None,
        rtmp_name=None,
        timezone=None,
        user_id=None,
        case_sensitive=False
):
    return _get_users_helpfn(
        discord_id=discord_id,
        discord_name=discord_name,
        twitch_name=twitch_name,
        rtmp_name=rtmp_name,
        timezone=timezone,
        user_id=user_id,
        case_sensitive=case_sensitive,
        do_any=True
    )


def get_users_with_all(
        discord_id=None,
        discord_name=None,
        twitch_name=None,
        rtmp_name=None,
        timezone=None,
        user_id=None,
        case_sensitive=False
):
    return _get_users_helpfn(
        discord_id=discord_id,
        discord_name=discord_name,
        twitch_name=twitch_name,
        rtmp_name=rtmp_name,
        timezone=timezone,
        user_id=user_id,
        case_sensitive=case_sensitive,
        do_any=False
    )


# Simple setters
def set_timezone(discord_id, timezone):
    with DBConnect(commit=True) as cursor:
        params = (timezone, discord_id,)
        cursor.execute(
            "UPDATE user_data "
            "SET timezone=%s "
            "WHERE discord_id=%s",
            params)


def set_twitch(discord_id, twitch_name):
    with DBConnect(commit=True) as cursor:
        params = (twitch_name, discord_id,)
        cursor.execute(
            "UPDATE user_data "
            "SET twitch_name=%s "
            "WHERE discord_id=%s",
            params)


def set_user_info(discord_id, user_info):
    with DBConnect(commit=True) as cursor:
        params = (user_info, discord_id,)
        cursor.execute(
            "UPDATE user_data "
            "SET user_info=%s "
            "WHERE discord_id=%s",
            params)


# UserPrefs
def set_prefs(discord_id, user_prefs):
    new_user_prefs = get_prefs(discord_id=discord_id).merge_prefs(user_prefs)

    with DBConnect(commit=True) as cursor:
        params = (discord_id, new_user_prefs.daily_alert, new_user_prefs.race_alert)
        cursor.execute(
            "INSERT INTO user_data "
            "(discord_id, daily_alert, race_alert) "
            "VALUES (%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE "
            "daily_alert=VALUES(daily_alert), "
            "race_alert=VALUES(race_alert)", params)


def get_prefs(discord_id):
    with DBConnect(commit=False) as cursor:
        params = (discord_id,)
        cursor.execute(
            "SELECT daily_alert, race_alert "
            "FROM user_data "
            "WHERE discord_id=%s",
            params)
        prefs_row = cursor.fetchone()
        cursor.close()
        user_prefs = UserPrefs()
        user_prefs.daily_alert = bool(prefs_row[0])
        user_prefs.race_alert = bool(prefs_row[1])
        return user_prefs


# TODO These have code smell
def get_discord_id(discord_name):
    with DBConnect(commit=False) as cursor:
        params = (discord_name,)
        cursor.execute(
            "SELECT discord_id "
            "FROM user_data "
            "WHERE discord_name=%s",
            params)
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None


def get_all_ids_matching_prefs(user_prefs):
    if user_prefs.is_empty:
        return []

    where_query = ''
    if user_prefs.daily_alert is not None:
        where_query += ' AND daily_alert={0}'.format('TRUE' if user_prefs.daily_alert else 'FALSE')
    if user_prefs.race_alert is not None:
        where_query += ' AND race_alert={0}'.format('TRUE' if user_prefs.race_alert else 'FALSE')
    where_query = where_query[5:]

    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT discord_id "
            "FROM user_data "
            "WHERE {0}".format(where_query))
        to_return = []
        for row in cursor.fetchall():
            to_return.append(int(row[0]))
        return to_return


# def register_all_users(members):
#     with DBConnect(commit=True) as cursor:
#         for member in members:
#             params = (member.id, member.display_name,)
#             cursor.execute(
#                 "INSERT INTO user_data "
#                 "(discord_id, discord_name) "
#                 "VALUES (%s,%s) "
#                 "ON DUPLICATE KEY UPDATE "
#                 "discord_name=VALUES(discord_name)",
#                 params)
#
#
# def register_user(member):
#     with DBConnect(commit=True) as cursor:
#         params = (member.id, member.name,)
#         cursor.execute(
#             "INSERT INTO user_data "
#             "(discord_id, discord_name) "
#             "VALUES (%s,%s) "
#             "ON DUPLICATE KEY UPDATE "
#             "discord_name=VALUES(discord_name)",
#             params)


def _get_users_helpfn(
        discord_id,
        discord_name,
        twitch_name,
        rtmp_name,
        timezone,
        user_id,
        case_sensitive,
        do_any
):
    with DBConnect(commit=False) as cursor:
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
            "SELECT "
            "   discord_id, "
            "   discord_name, "
            "   twitch_name, "
            "   rtmp_name, "
            "   timezone, "
            "   user_info, "
            "   daily_alert, "
            "   race_alert, "
            "   user_id "
            "FROM user_data "
            "WHERE {0}".format(where_query),
            params)
        return cursor.fetchall()


def _register_user(necro_user: NecroUser):
    rtmp_clash_user_id = _get_resolvable_rtmp_clash_user_id(necro_user)

    params = (
        necro_user.discord_id,
        necro_user.discord_name,
        necro_user.twitch_name,
        necro_user.timezone,
        necro_user.user_info,
        necro_user.user_prefs.daily_alert,
        necro_user.user_prefs.race_alert,
        necro_user.rtmp_name,
    )

    with DBConnect(commit=True) as cursor:
        if rtmp_clash_user_id is None:
            try:
                cursor.execute(
                    "INSERT INTO user_data "
                    "(discord_id, discord_name, twitch_name, timezone, user_info, daily_alert, race_alert, rtmp_name) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ",
                    params
                )
                cursor.execute("SELECT LAST_INSERT_ID()")
                necro_user.set_user_id(int(cursor.fetchone()[0]))
            except mysql.connector.IntegrityError:
                console.error('Tried to insert a duplicate racer entry. Params: {0}'.format(params))
                raise
        else:
            cursor.execute(
                "UPDATE user_data "
                "SET "
                "   discord_id=%s, "
                "   discord_name=%s, "
                "   twitch_name=%s, "
                "   timezone=%s, "
                "   user_info=%s, "
                "   daily_alert=%s, "
                "   race_alert=%s "
                "WHERE rtmp_name=%s",
                params
            )
            necro_user.set_user_id(rtmp_clash_user_id)


def _get_resolvable_rtmp_clash_user_id(necro_user: NecroUser) -> int or None:
    """
    Returns the user_id of any entry in the DB with the same rtmp_name as necro_user, a NULL discord_id,
    and a different user_id, or None if no such entry exists.
    Transfers all records referencing the "from" user_id to the "to" user_id.
    WARNING: Possible severe loss of information. Cannot be undone. Use with caution!
    :param necro_user: NecroUser
    """
    if necro_user.rtmp_name is None:
        return None

    rtmp_params = (necro_user.rtmp_name,)

    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT user_id, discord_id "
            "FROM user_data "
            "WHERE rtmp_name=%s",
            rtmp_params
        )

        data = cursor.fetchone()
        if data is None:
            return None

        user_id = int(data[0]) if data[0] is not None else None
        discord_id = int(data[1]) if data[1] is not None else None
        if discord_id is None and discord_id != necro_user.discord_id and user_id != necro_user.user_id:
            return user_id
        else:
            return None


def _transfer_user_id(from_user_id: int, to_user_id: int):
    params = (to_user_id, from_user_id,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "UPDATE match_data "
            "SET racer_1_id=%s "
            "WHERE racer_1_id=%s",
            params
        )
        cursor.execute(
            "UPDATE match_data "
            "SET racer_2_id=%s "
            "WHERE racer_2_id=%s",
            params
        )
