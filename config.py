def init(config_filename):
    global BOT_COMMAND_PREFIX
    global BOT_VERSION

    #admin
    global ADMIN_ROLE_NAMES                     #list of names of roles to give admin access

    #channels
    global MAIN_CHANNEL_NAME
    global REFERENCE_CHANNEL_NAME
    global DAILY_SPOILERCHAT_CHANNEL_NAME
    global DAILY_LEADERBOARDS_CHANNEL_NAME
    global ROTATING_DAILY_SPOILERCHAT_CHANNEL_NAME
    global ROTATING_DAILY_LEADERBOARDS_CHANNEL_NAME
    global RACE_RESULTS_CHANNEL_NAME

    #daily
    global DAILY_GRACE_PERIOD                     #minutes to allow for submissions on old dailies after new ones are rolled out

    #race
    global COUNTDOWN_LENGTH                        #number of seconds between the final .ready and race start
    global INCREMENTAL_COUNTDOWN_START             #number of seconds at which to start counting down each second in chat
    global FINALIZE_TIME_SEC                       #seconds after race end to finalize+record race
    global CLEANUP_TIME_SEC                        #minutes of no chatting until the room may be cleaned (only applies if race has been finalized)
    global NO_ENTRANTS_CLEANUP_SEC                 #room is cleaned if there are no race entrants for this duration of time
    global NO_ENTRANTS_CLEANUP_WARNING_SEC         #give a warning re: cleaning race room if no entrants for this duration of time
    global REQUIRE_AT_LEAST_TWO_FOR_RACE           #if True, then races with only one entrant cannot be started
    global RACE_POKE_DELAY                         #number of seconds to wait between allowing pokes 

    #database
    global MYSQL_DB_HOST
    global MYSQL_DB_USER
    global MYSQL_DB_PASSWD
    global MYSQL_DB_NAME
    
    defaults = {
        'bot_command_prefix':'.',
        'bot_version':'0.0.0',
        'channel_main':'necrobot_main',
        'channel_reference':'command_list',
        'channel_daily_spoilerchat':'cadence_dailyspoilerchat',
        'channel_daily_leaderboards':'cadence_daily_leaderboards',
        'channel_rot_daily_spoilerchat':'rotating_dailyspoilerchat',
        'channel_rot_daily_leaderboards':'rotating_daily_leaderboards',
        'channel_race_results':'race_results',
        'daily_grace_period_length_minutes':'60',
        'race_countdown_time_seconds':'10',
        'race_begin_counting_down_at':'5',
        'race_record_after_seconds':'30',
        'race_cleanup_after_room_is_silent_for_seconds':'180',
        'race_cleanup_after_no_entrants_for_seconds':'120',
        'race_give_cleanup_warning_after_no_entrants_for_seconds':'90', 
        'race_require_at_least_two':'0',
        'race_poke_delay':'10',
        'mysql_db_host':'localhost',
        'mysql_db_user':'root',
        'mysql_db_passwd':'',
        'mysql_db_name':'necrobot'
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

    BOT_COMMAND_PREFIX = defaults['bot_command_prefix']
    BOT_VERSION = defaults['bot_version']
    MAIN_CHANNEL_NAME = defaults['channel_main']
    REFERENCE_CHANNEL_NAME = defaults['channel_reference']
    ADMIN_ROLE_NAMES = admin_roles
    DAILY_SPOILERCHAT_CHANNEL_NAME = defaults['channel_daily_spoilerchat']
    DAILY_LEADERBOARDS_CHANNEL_NAME = defaults['channel_daily_leaderboards']
    ROTATING_DAILY_SPOILERCHAT_CHANNEL_NAME = defaults['channel_rot_daily_spoilerchat']
    ROTATING_DAILY_LEADERBOARDS_CHANNEL_NAME = defaults['channel_rot_daily_leaderboards']
    RACE_RESULTS_CHANNEL_NAME = defaults['channel_race_results']
    DAILY_GRACE_PERIOD = int(defaults['daily_grace_period_length_minutes'])
    COUNTDOWN_LENGTH = int(defaults['race_countdown_time_seconds'])
    INCREMENTAL_COUNTDOWN_START = int(defaults['race_begin_counting_down_at'])
    FINALIZE_TIME_SEC = int(defaults['race_record_after_seconds'])
    CLEANUP_TIME_SEC = int(defaults['race_cleanup_after_room_is_silent_for_seconds'])
    NO_ENTRANTS_CLEANUP_SEC = int(defaults['race_cleanup_after_no_entrants_for_seconds'])
    NO_ENTRANTS_CLEANUP_WARNING_SEC = int(defaults['race_give_cleanup_warning_after_no_entrants_for_seconds'])
    REQUIRE_AT_LEAST_TWO_FOR_RACE = bool(int(defaults['race_require_at_least_two']))
    RACE_POKE_DELAY = int(defaults['race_poke_delay'])
    MYSQL_DB_HOST = defaults['mysql_db_host']
    MYSQL_DB_USER = defaults['mysql_db_user']
    MYSQL_DB_PASSWD = defaults['mysql_db_passwd']
    MYSQL_DB_NAME = defaults['mysql_db_name']

##--Testing-------------------------------------------------------------------------

if __name__ == "__main__":
    init('data/bot_config')
        
