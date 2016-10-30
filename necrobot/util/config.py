class Config(object):
    BOT_COMMAND_PREFIX = '.'
    BOT_VERSION = '0.0.0'

    # admin
    ADMIN_ROLE_NAMES = []  # list of names of roles to give admin access

    # channels
    MAIN_CHANNEL_NAME = 'necrobot_main'
    REFERENCE_CHANNEL_NAME = 'command_list'
    DAILY_LEADERBOARDS_CHANNEL_NAME = 'daily_leaderboards'
    RACE_RESULTS_CHANNEL_NAME = 'race_results'

    # minutes to allow for submissions on old dailies after new ones are rolled out
    DAILY_GRACE_PERIOD = int(60)

    # number of seconds between the final .ready and race start
    COUNTDOWN_LENGTH = int(10)

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

    # if True, then races with only one entrant cannot be started
    REQUIRE_AT_LEAST_TWO_FOR_RACE = True

    # number of seconds to wait between allowing pokes
    RACE_POKE_DELAY = int(10)

    # database
    MYSQL_DB_HOST = 'localhost'
    MYSQL_DB_USER = 'root'
    MYSQL_DB_PASSWD = ''
    MYSQL_DB_NAME = 'necrobot'


def init(config_filename):
    defaults = {
        'bot_command_prefix': '.',
        'bot_version': '0.0.0',
        'channel_main': 'necrobot_main',
        'channel_reference': 'command_list',
        'channel_daily_spoilerchat': 'cadence_dailyspoilerchat',
        'channel_daily_leaderboards': 'cadence_daily_leaderboards',
        'channel_rot_daily_spoilerchat': 'rotating_dailyspoilerchat',
        'channel_rot_daily_leaderboards': 'rotating_daily_leaderboards',
        'channel_race_results': 'race_results',
        'daily_grace_period_length_minutes': '60',
        'race_countdown_time_seconds': '10',
        'race_begin_counting_down_at': '5',
        'race_record_after_seconds': '30',
        'race_cleanup_after_room_is_silent_for_seconds': '180',
        'race_cleanup_after_no_entrants_for_seconds': '120',
        'race_give_cleanup_warning_after_no_entrants_for_seconds': '90',
        'race_require_at_least_two': '0',
        'race_poke_delay': '10',
        'mysql_db_host': 'localhost',
        'mysql_db_user': 'root',
        'mysql_db_passwd': '',
        'mysql_db_name': 'necrobot'
        }

    admin_roles = []
            
    file = open(config_filename, 'r')
    if file:
        for line in file:
            args = line.split('=')
            if len(args) == 2:
                if args[0] in defaults:
                    defaults[args[0]] = args[1].rstrip('\n')
                elif args[0] == 'admin_roles':
                    arglist = args[1].rstrip('\n').split(',')
                    for arg in arglist:
                        admin_roles.append(arg)
                else:
                    print("Error in {0}: variable {1} isn't recognized.".format(config_filename, args[0]))

    Config.BOT_COMMAND_PREFIX = defaults['bot_command_prefix']
    Config.BOT_VERSION = defaults['bot_version']
    Config.MAIN_CHANNEL_NAME = defaults['channel_main']
    Config.REFERENCE_CHANNEL_NAME = defaults['channel_reference']
    Config.ADMIN_ROLE_NAMES = admin_roles
    Config.DAILY_SPOILERCHAT_CHANNEL_NAME = defaults['channel_daily_spoilerchat']
    Config.DAILY_LEADERBOARDS_CHANNEL_NAME = defaults['channel_daily_leaderboards']
    Config.ROTATING_DAILY_SPOILERCHAT_CHANNEL_NAME = defaults['channel_rot_daily_spoilerchat']
    Config.ROTATING_DAILY_LEADERBOARDS_CHANNEL_NAME = defaults['channel_rot_daily_leaderboards']
    Config.RACE_RESULTS_CHANNEL_NAME = defaults['channel_race_results']
    Config.DAILY_GRACE_PERIOD = int(defaults['daily_grace_period_length_minutes'])
    Config.COUNTDOWN_LENGTH = int(defaults['race_countdown_time_seconds'])
    Config.INCREMENTAL_COUNTDOWN_START = int(defaults['race_begin_counting_down_at'])
    Config.FINALIZE_TIME_SEC = int(defaults['race_record_after_seconds'])
    Config.CLEANUP_TIME_SEC = int(defaults['race_cleanup_after_room_is_silent_for_seconds'])
    Config.NO_ENTRANTS_CLEANUP_SEC = int(defaults['race_cleanup_after_no_entrants_for_seconds'])
    Config.NO_ENTRANTS_CLEANUP_WARNING_SEC = int(defaults['race_give_cleanup_warning_after_no_entrants_for_seconds'])
    Config.REQUIRE_AT_LEAST_TWO_FOR_RACE = bool(int(defaults['race_require_at_least_two']))
    Config.RACE_POKE_DELAY = int(defaults['race_poke_delay'])
    Config.MYSQL_DB_HOST = defaults['mysql_db_host']
    Config.MYSQL_DB_USER = defaults['mysql_db_user']
    Config.MYSQL_DB_PASSWD = defaults['mysql_db_passwd']
    Config.MYSQL_DB_NAME = defaults['mysql_db_name']

# -Testing-------------------------------------------------------------------------

if __name__ == "__main__":
    init('data/bot_config')
