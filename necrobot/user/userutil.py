from necrobot.botbase.necrobot import Necrobot
from necrobot.database import necrodb
from necrobot.user.necrouser import NecroUser
from necrobot.user.userprefs import UserPrefs


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


def get_user(discord_id=None, discord_name=None, twitch_name=None, rtmp_name=None, user_id=None):
    if discord_id is None and discord_name is None and twitch_name is None \
            and rtmp_name is None and user_id is None:
        raise RuntimeError('Error: Called NecroUser.get_user with no non-None fields.')

    raw_db_data = necrodb.get_all_users(
        discord_id=int(discord_id),
        discord_name=discord_name,
        twitch_name=twitch_name,
        rtmp_name=rtmp_name,
        user_id=user_id
    )

    if not raw_db_data:
        return None
    elif len(raw_db_data) > 1:
        raise DuplicateUserException(
            'Two or more users found satisfying discord_id={0}, discord_name={1}, twitch_name={2}, '
            'rtmp_name={3}.'.format(discord_id, discord_name, twitch_name, rtmp_name))

    for row in raw_db_data:
        member = Necrobot().find_member(discord_id=int(row[0]))
        if member is None:
            return None

        user = NecroUser(member)
        user.twitch_name = row[2]
        user.rtmp_name = row[3]
        user.set_timezone(row[4])
        user.user_info = row[5]
        user.user_prefs = UserPrefs()
        user.user_prefs.daily_alert = bool(row[6])
        user.user_prefs.race_alert = bool(row[7])
        user.user_id = int(row[8])
        return user
