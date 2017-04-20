import datetime


class Config(object):
    BOT_COMMAND_PREFIX = '.'
    BOT_VERSION = '0.10.0'

# Admin
    ADMIN_ROLE_NAMES = ['Admin']  # list of names of roles to give admin access

# Channels
    MAIN_CHANNEL_NAME = 'necrobot_main'
    DAILY_LEADERBOARDS_CHANNEL_NAME = 'daily_leaderboards'
    LADDER_ADMIN_CHANNEL_NAME = 'ladder_admin'
    RACE_RESULTS_CHANNEL_NAME = 'race_results'

# Daily
    # minutes to allow for submissions on old dailies after new ones are rolled out
    DAILY_GRACE_PERIOD = datetime.timedelta(minutes=60)

# Ladder
    RATINGS_IN_NICKNAMES = True

# Matches
    MATCH_FIRST_WARNING = datetime.timedelta(minutes=15)
    MATCH_FINAL_WARNING = datetime.timedelta(minutes=5)

# Races
    # number of seconds between the final .ready and race start
    COUNTDOWN_LENGTH = int(10)
    UNPAUSE_COUNTDOWN_LENGTH = int(3)

    # number of seconds at which to start counting down each second in chat
    INCREMENTAL_COUNTDOWN_START = int(5)

    # seconds after race end to finalize+record race
    FINALIZE_TIME_SEC = int(30)

# RaceRooms
    # amount of no chatting until the room may be cleaned (only applies if race has been finalized)
    CLEANUP_TIME = datetime.timedelta(minutes=3)

    # room is cleaned if there are no race entrants for this duration of time
    NO_ENTRANTS_CLEANUP = datetime.timedelta(minutes=2)

    # give a warning re: cleaning race room if no entrants for this duration of time
    NO_ENTRANTS_CLEANUP_WARNING = datetime.timedelta(minutes=1, seconds=30)

    # number of seconds to wait between allowing pokes
    RACE_POKE_DELAY = int(10)

# Vod recording
    VODRECORD_USERNAME = ''
    VODRECORD_PASSWD = ''
    RECORDING_ACTIVATED = False

# GSheet
    GSHEET_ID = ''
    OAUTH_CREDENTIALS_JSON = 'data/necrobot-service-acct.json'


# Database
    MYSQL_DB_HOST = 'localhost'
    MYSQL_DB_USER = 'root'
    MYSQL_DB_PASSWD = ''
    MYSQL_DB_NAME = 'necrobot'

# Login
    LOGIN_TOKEN = ''
    SERVER_ID = ''


def init(config_filename):
    defaults = {
        'mysql_db_host': 'localhost',
        'mysql_db_user': 'root',
        'mysql_db_passwd': '',
        'mysql_db_name': 'necrobot',
        'login_token': '',
        'server_id': '',
        'vodrecord_username': '',
        'vodrecord_passwd': ''
        }

    file = open(config_filename, 'r')
    if file:
        for line in file:
            args = line.split('=')
            if len(args) == 2:
                if args[0] in defaults:
                    defaults[args[0]] = args[1].rstrip('\n')
                else:
                    print("Error in {0}: variable {1} isn't recognized.".format(config_filename, args[0]))
            else:
                print("Error in {0} reading line: \"{1}\".".format(config_filename, line))

    Config.MYSQL_DB_HOST = defaults['mysql_db_host']
    Config.MYSQL_DB_USER = defaults['mysql_db_user']
    Config.MYSQL_DB_PASSWD = defaults['mysql_db_passwd']
    Config.MYSQL_DB_NAME = defaults['mysql_db_name']
    Config.LOGIN_TOKEN = defaults['login_token']
    Config.SERVER_ID = defaults['server_id']
    Config.VODRECORD_USERNAME = defaults['vodrecord_username']
    Config.VODRECORD_PASSWD = defaults['vodrecord_passwd']

# -Testing-------------------------------------------------------------------------

if __name__ == "__main__":
    init('data/bot_config')
