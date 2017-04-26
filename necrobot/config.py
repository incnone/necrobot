import datetime
import unittest

from enum import IntEnum
from necrobot.util import console


class TestLevel(IntEnum):
    FULL_DEBUG = 0
    BOT_DEBUG = 1
    TEST = 2
    RUN = 3

    def __str__(self):
        return self.name.lower()


class Config(object):
    @classmethod
    def full_debugging(cls) -> bool:
        return cls.TEST_LEVEL <= TestLevel.FULL_DEBUG

    @classmethod
    def debugging(cls) -> bool:
        return cls.TEST_LEVEL <= TestLevel.BOT_DEBUG

    @classmethod
    def testing(cls) -> bool:
        return cls.TEST_LEVEL <= TestLevel.TEST

    # Info ------------------------------------------------------------------------------------
    CONFIG_FILE = 'data/necrobot_config'
    BOT_COMMAND_PREFIX = '.'
    BOT_VERSION = '0.10.0'
    TEST_LEVEL = TestLevel.BOT_DEBUG

    # Admin -----------------------------------------------------------------------------------
    ADMIN_ROLE_NAMES = ['Admin', 'CoNDOR Staff']  # list of names of roles to give admin access
    STAFF_ROLE = 'CoNDOR Staff Fake'

    # Channels --------------------------------------------------------------------------------
    MAIN_CHANNEL_NAME = 'necrobot_main'
    DAILY_LEADERBOARDS_CHANNEL_NAME = 'daily_leaderboards'
    LADDER_ADMIN_CHANNEL_NAME = 'ladder_admin'
    RACE_RESULTS_CHANNEL_NAME = 'race_results'

    # League ----------------------------------------------------------------------------------
    LEAGUE_NAME = ''
    LOG_DIRECTORY = 'logs'

    # Daily -----------------------------------------------------------------------------------
    # minutes to allow for submissions on old dailies after new ones are rolled out
    DAILY_GRACE_PERIOD = datetime.timedelta(minutes=60)

    # Ladder ----------------------------------------------------------------------------------
    RATINGS_IN_NICKNAMES = True

    # Matches ---------------------------------------------------------------------------------
    MATCH_AUTOCONTEST_IF_WITHIN_HUNDREDTHS = 500
    MATCH_FIRST_WARNING = datetime.timedelta(minutes=15)
    MATCH_FINAL_WARNING = datetime.timedelta(minutes=5)

    # Races -----------------------------------------------------------------------------------
    # number of seconds between the final .ready and race start
    COUNTDOWN_LENGTH = int(10)
    UNPAUSE_COUNTDOWN_LENGTH = int(3)

    # number of seconds at which to start counting down each second in chat
    INCREMENTAL_COUNTDOWN_START = int(5)

    # seconds after race end to finalize+record race
    FINALIZE_TIME_SEC = int(30)

    # RaceRooms -------------------------------------------------------------------------------
    # amount of no chatting until the room may be cleaned (only applies if race has been finalized)
    CLEANUP_TIME = datetime.timedelta(minutes=3)

    # room is cleaned if there are no race entrants for this duration of time
    NO_ENTRANTS_CLEANUP = datetime.timedelta(minutes=2)

    # give a warning re: cleaning race room if no entrants for this duration of time
    NO_ENTRANTS_CLEANUP_WARNING = datetime.timedelta(minutes=1, seconds=30)

    # number of seconds to wait between allowing pokes
    RACE_POKE_DELAY = int(10)

    # Vod recording ---------------------------------------------------------------------------
    VODRECORD_USERNAME = ''
    VODRECORD_PASSWD = ''
    RECORDING_ACTIVATED = False

    # GSheet ----------------------------------------------------------------------------------
    GSHEET_ID = ''
    OAUTH_CREDENTIALS_JSON = 'data/necrobot-service-acct.json'

    # Database --------------------------------------------------------------------------------
    MYSQL_DB_HOST = 'localhost'
    MYSQL_DB_USER = 'root'
    MYSQL_DB_PASSWD = ''
    MYSQL_DB_NAME = 'necrobot'

    # Login -----------------------------------------------------------------------------------
    LOGIN_TOKEN = ''
    SERVER_ID = ''

    # Methods ---------------------------------------------------------------------------------
    @staticmethod
    def write():
        vals = [
            ['login_token', Config.LOGIN_TOKEN],
            ['server_id', Config.SERVER_ID],
            ['test_level', Config.TEST_LEVEL],

            ['mysql_db_host', Config.MYSQL_DB_HOST],
            ['mysql_db_user', Config.MYSQL_DB_USER],
            ['mysql_db_passwd', Config.MYSQL_DB_PASSWD],
            ['mysql_db_name', Config.MYSQL_DB_NAME],

            ['vodrecord_username', Config.VODRECORD_USERNAME],
            ['vodrecord_passwd', Config.VODRECORD_PASSWD],

            ['league_name', Config.LEAGUE_NAME],

            ['gsheet_id', Config.GSHEET_ID],
        ]

        with open(Config.CONFIG_FILE, 'w') as file:
            for row in vals:
                file.write('{0}={1}\n'.format(row[0], row[1]))


def init(config_filename):
    defaults = {
        'login_token': '',
        'server_id': '',
        'mysql_db_host': 'localhost',
        'mysql_db_user': 'root',
        'mysql_db_passwd': '',
        'mysql_db_name': 'necrobot',
        'vodrecord_username': '',
        'vodrecord_passwd': '',
        'gsheet_id': '',
        'league_name': '',
        'test_level': '',
        }

    with open(config_filename, 'r') as file:
        for line in file:
            args = line.split('=')
            if len(args) == 2:
                if args[0] in defaults:
                    defaults[args[0]] = args[1].rstrip('\n')
                else:
                    console.warning("Error in {0}: variable {1} isn't recognized.".format(config_filename, args[0]))
            else:
                console.warning("Error in {0} reading line: \"{1}\".".format(config_filename, line))

    Config.LOGIN_TOKEN = defaults['login_token']
    Config.SERVER_ID = defaults['server_id']

    Config.MYSQL_DB_HOST = defaults['mysql_db_host']
    Config.MYSQL_DB_USER = defaults['mysql_db_user']
    Config.MYSQL_DB_PASSWD = defaults['mysql_db_passwd']
    Config.MYSQL_DB_NAME = defaults['mysql_db_name']

    Config.VODRECORD_USERNAME = defaults['vodrecord_username']
    Config.VODRECORD_PASSWD = defaults['vodrecord_passwd']

    Config.LEAGUE_NAME = defaults['league_name']
    Config.GSHEET_ID = defaults['gsheet_id']

    if defaults['test_level'] == 'full_debug':
        Config.TEST_LEVEL = TestLevel.FULL_DEBUG
    elif defaults['test_level'] == 'bot_debug':
        Config.TEST_LEVEL = TestLevel.BOT_DEBUG
    elif defaults['test_level'] == 'test':
        Config.TEST_LEVEL = TestLevel.TEST
    elif defaults['test_level'] == 'run':
        Config.TEST_LEVEL = TestLevel.RUN

    Config.CONFIG_FILE = config_filename


# Testing--------------------------------------------------------------------------------------

class TestConfig(unittest.TestCase):
    def test_init_and_write(self):
        init('data/necrobot_config')
        Config.CONFIG_FILE = 'data/config_write_test'
        Config.write()
