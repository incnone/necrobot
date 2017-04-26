from necrobot.database import userdb
from necrobot.util import console

from necrobot.botbase.necrobot import Necrobot
from necrobot.user.necrouser import NecroUser
from necrobot.user.userprefs import UserPrefs


# A library of all NecroUsers that have been checked out from the database, indexed by user ID
user_library_by_uid = {}
user_library_by_did = {}
user_library_by_rtmp = {}


class DuplicateUserException(Exception):
    def __init__(self, err_str):
        self._err_str = err_str

    def __str__(self):
        return self._err_str


def get_user(
        discord_id: int = None,
        discord_name: str = None,
        twitch_name: str = None,
        rtmp_name: str = None,
        user_id: int = None,
        any_name: str = None,
        register: bool = False
        ) -> NecroUser or None:
    """Search for a NecroUser satisfying all of the non-None parameters.

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
        return _get_user_any_name(any_name, register)

    if discord_id is None and discord_name is None and twitch_name is None \
            and rtmp_name is None and user_id is None:
        return None

    cached_user = _get_cached_user(user_id=user_id, discord_id=discord_id, rtmp_name=rtmp_name)
    if cached_user is not None:
        return cached_user

    raw_db_data = userdb.get_users_with_all(
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
            user.set(rtmp_name=rtmp_name, commit=True)
            _cache_user(user)
            return user
        elif discord_id is not None:
            discord_member = Necrobot().find_member(discord_id=discord_id)
            if discord_member is not None:
                user = NecroUser(commit_fn=userdb.write_user)
                user.set(discord_member=discord_member, commit=True)
                _cache_user(user)
                return user
        else:
            console.warning('Tried to register a NecroUser without providing a name or ID.')
            return None

    # If more than one user is found, raise an exception
    elif len(raw_db_data) > 1:
        raise DuplicateUserException(
            'Two or more users found satisfying discord_id={0}, discord_name={1}, twitch_name={2}, '
            'rtmp_name={3}, user_id={4}.'.format(discord_id, discord_name, twitch_name, rtmp_name, user_id))

    # Exactly one user was found; convert into a NecroUser and return it
    for row in raw_db_data:
        return _get_user_from_db_row(row)

    return None


def commit_all_checked_out_users():
    for user in user_library_by_uid.values():
        user.commit()


def _get_user_from_db_row(user_row):
    user = NecroUser(commit_fn=userdb.write_user)
    _set_user_from_db_row(user, user_row)
    _cache_user(user)
    return user


def _get_user_any_name(name: str, register: bool) -> NecroUser or None:
    cached_user = _get_cached_user(rtmp_name=name)
    if cached_user is not None:
        return cached_user

    raw_db_data = userdb.get_users_with_any(
        discord_name=name,
        twitch_name=name,
        rtmp_name=name,
    )

    if not raw_db_data:
        if not register:
            return None
        else:
            user = NecroUser(commit_fn=userdb.write_user)
            user.set(rtmp_name=name, commit=True)
            _cache_user(user)
            return user
    elif len(raw_db_data) > 1:
        def sort_fn(row):
            return \
                32*int(row[3] == name) + 16*int(row[3].lower() == name.lower()) + \
                8*int(row[1] == name) + 4*int(row[1].lower() == name.lower()) + \
                2*int(row[2] == name) + 1*int(row[2].lower() == name.lower())
        raw_db_data = sorted(raw_db_data, key=lambda x: sort_fn(x))

    for user_row in raw_db_data:
        return _get_user_from_db_row(user_row)


def _set_user_from_db_row(user: NecroUser, row):
    user.set(
        discord_member=Necrobot().find_member(discord_id=int(row[0])),
        twitch_name=row[2],
        rtmp_name=row[3],
        timezone=row[4],
        user_info=row[5],
        user_prefs=UserPrefs(daily_alert=bool(row[6]), race_alert=bool(row[7])),
        commit=False
    )
    user.set_user_id(int(row[8]))


def _cache_user(user: NecroUser):
    user_library_by_uid[user.user_id] = user
    if user.discord_id is not None:
        user_library_by_did[user.discord_id] = user
    if user.rtmp_name is not None:
        user_library_by_rtmp[user.rtmp_name] = user


def _get_cached_user(user_id: int = None, discord_id: int = None, rtmp_name: str = None) -> NecroUser or None:
    if user_id is not None and user_id in user_library_by_uid:
        return user_library_by_uid[user_id]
    elif discord_id is not None and discord_id in user_library_by_did:
        return user_library_by_did[discord_id]
    elif rtmp_name is not None and rtmp_name in user_library_by_rtmp:
        return user_library_by_rtmp[rtmp_name]
    return None
