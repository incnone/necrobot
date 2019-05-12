"""
Module for the NecroUser library.

NecroUser represents a bot user, and is in correspondence with data stored in a row of the `users` table of
the database. This module is responsible for checking out users from the database and storing a library, indexed
by user ID, of checked out users.
"""

import necrobot.exception
from necrobot.user.necrouser import NecroUser
from necrobot.user.userprefs import UserPrefs
from necrobot.util import console
from necrobot.util import server
from necrobot.user import userdb

# Libraries of checked out users
user_library_by_uid = {}
user_library_by_did = {}


async def fill_user_dict(user_dict: dict):
    """
    For each key in the given dict, find a NecroUser, if possible, matching that key (via the logic used for the
    'any_name' field of get_user), and put that NecroUser into the value.
    """
    # TODO: be more careful about name duplication
    raw_db_data = await userdb.get_all_users_with_any(user_dict.keys())
    for row in raw_db_data:
        necrouser = _get_user_from_db_row(row)
        if necrouser.discord_name is not None and necrouser.discord_name.lower() in user_dict:
            user_dict[necrouser.discord_name.lower()] = necrouser
        elif necrouser.discord_name is not None and necrouser.twitch_name.lower() in user_dict:
            user_dict[necrouser.twitch_name.lower()] = necrouser
        elif necrouser.discord_name is not None and necrouser.rtmp_name.lower() in user_dict:
            user_dict[necrouser.rtmp_name.lower()] = necrouser
    return user_dict


async def get_user(
    discord_id: int = None,
    discord_name: str = None,
    twitch_name: str = None,
    rtmp_name: str = None,
    user_id: int = None,
    any_name: str = None,
    register: bool = False
) -> NecroUser or None:
    """Search for a NecroUser satisfying the given parameter. Behavior only guaranteed when exactly one of the
    parameters other than register is non-None.

    Parameters
    ----------
    discord_id: int
        The user's discord ID.
    discord_name: str
        The user's discord name. Case-insensitve.
    twitch_name: str
        The user's twitch name. Case-insensitve.
    rtmp_name: str
        The user's RTMP name. Case-insensitve.
    user_id: int
        The user's database ID.
    any_name: str
        Will search for a user, if possible, whose rtmp_name, discord_name, or twitch_name is equal to that name, 
        case-insensitive. If multiple users, prioritize by name type (1=rtmp, 2=discord, 3=twitch), then randomly.
        Providing this field means that the above fields will be ignored.
    register: bool
        If True, will register a new user if none is found matching the given parameters. This requires that either
        discord_id, rtmp_name, or any_name is not None. (If any_name is given, it will be registered as an RTMP name.)

    Returns
    -------
    NecroUser or None
        The found NecroUser object.
    """
    if any_name is not None:
        return await _get_user_any_name(any_name, register)

    if discord_id is None and discord_name is None and twitch_name is None \
            and rtmp_name is None and user_id is None:
        return None

    cached_user = _get_cached_user(
        discord_id=discord_id,
        user_id=user_id
    )
    if cached_user is not None:
        return cached_user

    raw_db_data = await userdb.get_users_with_all(
        discord_id=discord_id,
        discord_name=discord_name,
        twitch_name=twitch_name,
        rtmp_name=rtmp_name,
        user_id=user_id
    )

    # If no user found, register if asked, otherwise return None
    if not raw_db_data:
        if not register:
            return None
        elif rtmp_name is not None:
            user = NecroUser(commit_fn=userdb.write_user)
            user.set(rtmp_name=rtmp_name, commit=False)
            await user.commit()
            _cache_user(user)
            return user
        elif discord_id is not None:
            discord_member = server.find_member(discord_id=discord_id)
            if discord_member is not None:
                user = NecroUser(commit_fn=userdb.write_user)
                user.set(discord_member=discord_member, commit=False)
                await user.commit()
                _cache_user(user)
                return user
        else:
            console.warning('Tried to register a NecroUser without providing a name or ID.')
            return None

    # If more than one user is found, raise an exception
    elif len(raw_db_data) > 1:
        raise necrobot.exception.DuplicateUserException(
            'Two or more users found satisfying discord_id={0}, discord_name={1}, twitch_name={2}, '
            'rtmp_name={3}, user_id={4}.'.format(discord_id, discord_name, twitch_name, rtmp_name, user_id))

    # Exactly one user was found; convert into a NecroUser and return it
    for row in raw_db_data:
        return _get_user_from_db_row(row)

    return None


async def commit_all_checked_out_users():
    for user in user_library_by_uid.values():
        await user.commit()


def _get_user_from_db_row(user_row):
    cached_user = _get_cached_user(user_row[8])
    if cached_user is not None:
        return cached_user

    user = NecroUser(commit_fn=userdb.write_user)
    console.debug('Getting user from data: {}'.format(user_row))
    user.set(
        discord_id=user_row[0],
        discord_name=user_row[1],
        twitch_name=user_row[2],
        rtmp_name=user_row[3],
        timezone=user_row[4],
        user_info=user_row[5],
        user_prefs=UserPrefs(daily_alert=bool(user_row[6]), race_alert=bool(user_row[7])),
        commit=False
    )
    user._user_id = int(user_row[8])
    _cache_user(user)
    return user


async def _get_user_any_name(name: str, register: bool) -> NecroUser or None:
    raw_db_data = await userdb.get_users_with_any(
        discord_name=name,
        twitch_name=name,
        rtmp_name=name,
    )

    if not raw_db_data:
        if not register:
            return None
        else:
            user = NecroUser(commit_fn=userdb.write_user)
            user.set(rtmp_name=name, commit=False)
            await user.commit()
            _cache_user(user)
            return user

    raw_db_data = sorted(raw_db_data, key=lambda x: _raw_db_sort_fn(x, name, name, name), reverse=True)
    for user_row in raw_db_data:
        return _get_user_from_db_row(user_row)


def _cache_user(user: NecroUser):
    if user.user_id is None:
        console.warning('Trying to cache a user with no user ID.')
        return

    user_library_by_uid[user.user_id] = user
    if user.discord_id is not None:
        user_library_by_did[user.discord_id] = user


def _get_cached_user(
        user_id: int = None,
        discord_id: int = None,
) -> NecroUser or None:
    if user_id is not None and user_id in user_library_by_uid:
        return user_library_by_uid[user_id]
    elif discord_id is not None and discord_id in user_library_by_did:
        return user_library_by_did[discord_id]
    else:
        return None


def _raw_db_sort_fn(row, discord_name, twitch_name, rtmp_name):
    return \
        32*int(row[3] == rtmp_name) \
        + 16*int(row[3].lower() == rtmp_name.lower() if row[3] is not None else 0) + \
        8*int(row[1] == discord_name) \
        + 4*int(row[1].lower() == discord_name.lower() if row[1] is not None else 0) + \
        2*int(row[2] == twitch_name) \
        + 1*int(row[2].lower() == twitch_name.lower() if row[2] is not None else 0)
