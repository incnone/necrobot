from necrobot.botbase.necrobot import Necrobot
from necrobot.database import necrodb
from necrobot.user.necrouser import NecroUser
from necrobot.user.userprefs import UserPrefs
from necrobot.util import console


class DuplicateUserException(Exception):
    def __init__(self, err_str):
        self._err_str = err_str

    def __str__(self):
        return self._err_str


class NecroUserCM(object):
    def __init__(self, discord_member):
        self.user = get_user(discord_id=discord_member.id)

    def __enter__(self):
        return self.user

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.user.commit()


def _get_user_any_name(name: str, register: bool) -> NecroUser or None:
    raw_db_data = necrodb.get_users_with_any(
        discord_name=name,
        twitch_name=name,
        rtmp_name=name,
    )

    if not raw_db_data:
        if not register:
            return None
        else:
            user = NecroUser(rtmp_name=name)
            necrodb.write_user(user)
            return user
    elif len(raw_db_data) > 1:
        def sort_fn(row):
            return \
                32*int(row[3] == name) + 16*int(row[3].lower() == name.lower()) + \
                8*int(row[1] == name) + 4*int(row[1].lower() == name.lower()) + \
                2*int(row[2] == name) + 1*int(row[2].lower() == name.lower())
        raw_db_data = sorted(raw_db_data, key=lambda x: sort_fn(x))

    for user_row in raw_db_data:
        user = NecroUser()
        user.member = Necrobot().find_member(discord_id=int(user_row[0]))
        user.twitch_name = user_row[2]
        user.rtmp_name = user_row[3]
        user.set_timezone(user_row[4])
        user.user_info = user_row[5]
        user.user_prefs = UserPrefs()
        user.user_prefs.daily_alert = bool(user_row[6])
        user.user_prefs.race_alert = bool(user_row[7])
        user.user_id = int(user_row[8])
        return user


def get_user(
        discord_id=None,
        discord_name=None,
        twitch_name=None,
        rtmp_name=None,
        user_id=None,
        any_name=None,
        register=False
) -> NecroUser or None:
    """
    Searches for a NecroUser in the databse whose fields are all equal to the given, non-None inputs. If any_name is
    specified, 
    :param discord_id: Optional[int] The user's discord ID.
    :param discord_name: Optional[str] The user's discord name.
    :param twitch_name: Optional[str] The user's twitch name.
    :param rtmp_name: Optional[str] The user's rtmp_name.
    :param user_id: Optional[int] The unique user ID (the database PK) 
    :param any_name: Optional[str] Will search for a user, if possible, whose rtmp_name, discord_name, or twitch_name 
    is equal to that name, case-insensitive. If multiple users, prioritize by name type (1=rtmp, 2=discord, 3=twitch),
    then by case-sensitivity, then randomly.
    :param register: bool If the user is not found, will create a new user. This requires that either discord_id, 
    rtmp_name, or any_name be given. If any_name is given, will be interpreted as an RTMP name.
    :return: The found NecroUser, or None if no such.
    :exception DuplicateUserException: If two or more users are found satisfying the requirements.
    """
    if discord_id is None and discord_name is None and twitch_name is None \
            and rtmp_name is None and user_id is None and any_name is None:
        raise RuntimeError('Error: Called NecroUser.get_user with no non-None fields.')

    if any_name is not None:
        return _get_user_any_name(any_name, register)

    raw_db_data = necrodb.get_users_with_all(
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
            user = NecroUser(rtmp_name=rtmp_name)
            necrodb.write_user(user)
            return user
        elif discord_id is not None:
            discord_member = Necrobot().find_member(discord_id=discord_id)
            if discord_member is not None:
                user = NecroUser(discord_member=discord_member)
                necrodb.write_user(user)
                return user
        else:
            console.error('Tried to register a NecroUser without providing a name or ID.')
            return None

    # If more than one user is found, raise an exception
    elif len(raw_db_data) > 1:
        raise DuplicateUserException(
            'Two or more users found satisfying discord_id={0}, discord_name={1}, twitch_name={2}, '
            'rtmp_name={3}, user_id={4}.'.format(discord_id, discord_name, twitch_name, rtmp_name, user_id))

    # Exactly one user was found; convert into a NecroUser and return it
    for row in raw_db_data:
        user = NecroUser()
        user.member = Necrobot().find_member(discord_id=int(row[0]))
        user.twitch_name = row[2]
        user.rtmp_name = row[3]
        user.set_timezone(row[4])
        user.user_info = row[5]
        user.user_prefs = UserPrefs()
        user.user_prefs.daily_alert = bool(row[6])
        user.user_prefs.race_alert = bool(row[7])
        user.user_id = int(row[8])
        return user

    return None
