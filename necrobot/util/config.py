class Config(object):
    BOT_COMMAND_PREFIX = '.'
    BOT_VERSION = '0.8.3'

    # admin
    ADMIN_ROLE_NAMES = ['Admin']  # list of names of roles to give admin access

    # channels
    MAIN_CHANNEL_NAME = 'necrobot_main'
    DAILY_LEADERBOARDS_CHANNEL_NAME = 'daily_leaderboards'
    RACE_RESULTS_CHANNEL_NAME = 'race_results'

    # minutes to allow for submissions on old dailies after new ones are rolled out
    DAILY_GRACE_PERIOD = int(60)

    # number of seconds between the final .ready and race start
    COUNTDOWN_LENGTH = int(10)
    UNPAUSE_COUNTDOWN_LENGTH = int(3)

    # number of seconds at which to start counting down each second in chat
    INCREMENTAL_COUNTDOWN_START = int(5)

    # seconds after race end to finalize+record race
    FINALIZE_TIME_SEC = int(30)

    # minutes of no chatting until the room may be cleaned (only applies if race has been finalized)
    CLEANUP_TIME_SEC = int(180)

    # room is cleaned if there are no race entrants for this duration of time
    NO_ENTRANTS_CLEANUP_SEC = int(120)

    # give a warning re: cleaning race room if no entrants for this duration of time
    NO_ENTRANTS_CLEANUP_WARNING_SEC = int(90)

    # number of seconds to wait between allowing pokes
    RACE_POKE_DELAY = int(10)

    # database
    MYSQL_DB_HOST = 'localhost'
    MYSQL_DB_USER = 'root'
    MYSQL_DB_PASSWD = ''
    MYSQL_DB_NAME = 'necrobot'

    # login
    LOGIN_TOKEN = ''
    SERVER_ID = ''


def init(config_filename):
    defaults = {
        'mysql_db_host': 'localhost',
        'mysql_db_user': 'root',
        'mysql_db_passwd': '',
        'mysql_db_name': 'necrobot',
        'login_token': '',
        'server_id': ''
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

# -Testing-------------------------------------------------------------------------

if __name__ == "__main__":
    init('data/bot_config')
