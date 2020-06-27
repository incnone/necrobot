"""Global bot configuration.

General
-------
CONFIG_FILE: str
    The name of the configuration file where we will save this config.
BOT_COMMAND_PREFIX: str
    The character string indicating that what follows is a bot command.
BOT_VERSION: str
    The current bot version.
DEBUG_LEVEL: config.DebugLevel
    Determines the amount of logging and output done by the bot, as well as whether testing
    commands are available.

Admin
-----
ADMIN_ROLE_NAMES: list[str]
    List of names of roles to give admin access.
STAFF_ROLE: str
    The specific role that should be pinged when staff-relevant things happen.

Channels
--------
MAIN_CHANNEL_NAME: str
    The general public channel where the bot accepts commands.
LADDER_ADMIN_CHANNEL_NAME: str
    The channel for general ladder admin commands.
RACE_RESULTS_CHANNEL_NAME: str
    The channel where the bot posts public race results.

Database
--------
MYSQL_DB_HOST: str
    The database hostname.
MYSQL_DB_USER: str
    The database username.
MYSQL_DB_PASSWD: str
    The database password.
MYSQL_DB_NAME: str
    The default schema name.

GSheet
------
OAUTH_CREDENTIALS_JSON: str
    The filename where GSheet OAuth credentials are stored.

Ladder
------
RATINGS_IN_NICKNAMES: bool
    Whether to update server nicknames with people's ratings.

League
------
LEAGUE_NAME: str
    The schema name of the current league.
LOG_DIRECTORY: str
    The directory to write match logs to.

Login
-----
LOGIN_TOKEN: str
    The bot's Discord login token.
SERVER_ID: str
    The Discord ID of the server the bot should accept commands on.

Matches
-------
MATCH_AUTOCONTEST_IF_WITHIN_HUNDREDTHS: int
    If the two racer's times are within this many hundredths of a second, the match is 
    automatically contested.
MATCH_FIRST_WARNING: datetime.timedelta
    The time before match start at which to first ping the racers.
MATCH_FINAL_WARNING: datetime.timedelta
    The time before match start at which to make the final ping to the racers.
MATCH_CHANNEL_CATEGORY_NAME: str
    The channel category name for newly created match channels.

Races
-----
COUNTDOWN_LENGTH: int
    The length of a race countdown in seconds.
UNPAUSE_COUNTDOWN_LENGTH: int
    The length of an unpause countdown in seconds.
INCREMENTAL_COUNTDOWN_START: int
    The second at which to start counting down second-by-second.
FINALIZE_TIME_SEC: int
    The number of seconds after the end of the race before its data is recorded.

RaceRooms
---------
CLEANUP_TIME: datetime.timedelta
    The amount of time of no chatting in a room with no ongoing race before it is 
    automatically deleted.
NO_ENTRANTS_CLEANUP: datetime.timedelta
    The amount of time a raceroom can have zero entrants before it is automatically
    deleted.
NO_ENTRANTS_CLEANUP_WARNING: datetime.timedelta
    The amount of time before cleanup at which to warn that the race will soon be
    deleted from having zero entrants.
RACE_POKE_DELAY: int
    The minimum number of seconds between .poke mentions.

Vod recording
-------------
VODRECORD_USERNAME: str
    The username with which to access the VOD recording URL.
VODRECORD_PASSWD: str
    The username with which to access the VOD recording URL.
RECORDING_ACTIVATED: bool
    If False, no cURLs will be sent to the VOD record URL.
"""

import datetime
import unittest
from typing import Optional

from enum import IntEnum
from necrobot.util import console


class DebugLevel(IntEnum):
    FULL_DEBUG = 0
    BOT_DEBUG = 1
    TEST = 2
    RUN = 3

    def __str__(self):
        return self.name.lower()


class Config(object):
    GRUDGEDOR = False

    # General----------------------------------------------------------------------------------
    CONFIG_FILE = 'data/necrobot_config'
    BOT_COMMAND_PREFIX = '.'
    BOT_VERSION = '0.13.0'
    DEBUG_LEVEL = DebugLevel.TEST

    # Admin -----------------------------------------------------------------------------------
    ADMIN_ROLE_NAMES = ['Admin', 'CoNDOR Staff', 'Necrobot']  # list of names of roles to give admin access
    STAFF_ROLE = 'CoNDOR Staff'

    # Channels --------------------------------------------------------------------------------
    MAIN_CHANNEL_NAME = 'necrobot_main'
    LADDER_ADMIN_CHANNEL_NAME = 'ladder_admin'
    LADDER_MAIN_CHANNEL_NAME = 'ladder_main'
    RACE_RESULTS_CHANNEL_NAME = 'race_results'
    NOTIFICATIONS_CHANNEL_NAME = 'bot_notifications'
    SCHEDULE_CHANNEL_NAME = 'schedule'

    # Database --------------------------------------------------------------------------------
    MYSQL_DB_HOST = 'localhost'
    MYSQL_DB_USER = 'root'
    MYSQL_DB_PASSWD = ''
    MYSQL_DB_NAME = 'necrobot'

    # GSheet ----------------------------------------------------------------------------------
    OAUTH_CREDENTIALS_JSON = 'data/necrobot-service-acct.json'

    # Ladder ----------------------------------------------------------------------------------
    RATINGS_IN_NICKNAMES = True

    # League ----------------------------------------------------------------------------------
    LEAGUE_NAME = ''
    LOG_DIRECTORY = 'logs'

    # Login -----------------------------------------------------------------------------------
    LOGIN_TOKEN = ''
    SERVER_ID = None    # type: Optional[int]

    # Matches ---------------------------------------------------------------------------------
    MATCH_AUTOCONTEST_IF_WITHIN_HUNDREDTHS = 500
    MATCH_FIRST_WARNING = datetime.timedelta(minutes=15)
    MATCH_FINAL_WARNING = datetime.timedelta(minutes=5)
    MATCH_CHANNEL_CATEGORY_NAME = "Race rooms"

    # Races -----------------------------------------------------------------------------------
    COUNTDOWN_LENGTH = int(10)
    UNPAUSE_COUNTDOWN_LENGTH = int(3)
    INCREMENTAL_COUNTDOWN_START = int(3)
    FINALIZE_TIME_SEC = int(30)
    RACE_CHANNEL_CATEGORY_NAME = "Race rooms"

    # RaceRooms -------------------------------------------------------------------------------
    CLEANUP_TIME = datetime.timedelta(minutes=3)
    NO_ENTRANTS_CLEANUP = datetime.timedelta(minutes=2)
    NO_ENTRANTS_CLEANUP_WARNING = datetime.timedelta(minutes=1, seconds=30)
    RACE_POKE_DELAY = int(10)

    # Methods ---------------------------------------------------------------------------------
    @staticmethod
    def write():
        vals = [
            ['login_token', Config.LOGIN_TOKEN],
            ['server_id', str(Config.SERVER_ID)],
            ['test_level', Config.DEBUG_LEVEL],

            ['mysql_db_host', Config.MYSQL_DB_HOST],
            ['mysql_db_user', Config.MYSQL_DB_USER],
            ['mysql_db_passwd', Config.MYSQL_DB_PASSWD],
            ['mysql_db_name', Config.MYSQL_DB_NAME],

            ['main_channel_name', Config.MAIN_CHANNEL_NAME],
            ['match_category_name', Config.MATCH_CHANNEL_CATEGORY_NAME],
            ['league_name', Config.LEAGUE_NAME],
        ]

        with open(Config.CONFIG_FILE, 'w') as file:
            for row in vals:
                file.write('{0}={1}\n'.format(row[0], row[1]))

    @classmethod
    def full_debugging(cls) -> bool:
        return cls.DEBUG_LEVEL <= DebugLevel.FULL_DEBUG

    @classmethod
    def debugging(cls) -> bool:
        return cls.DEBUG_LEVEL <= DebugLevel.BOT_DEBUG

    @classmethod
    def testing(cls) -> bool:
        return cls.DEBUG_LEVEL <= DebugLevel.TEST


def init(config_filename):
    defaults = {
        'login_token': '',
        'server_id': '',
        'mysql_db_host': 'localhost',
        'mysql_db_user': 'root',
        'mysql_db_passwd': '',
        'mysql_db_name': 'necrobot',
        'league_name': '',
        'test_level': '',
        'main_channel_name': 'necrobot_main',
        'match_category_name': 'Race Rooms',
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
    Config.SERVER_ID = int(defaults['server_id'])

    Config.MYSQL_DB_HOST = defaults['mysql_db_host']
    Config.MYSQL_DB_USER = defaults['mysql_db_user']
    Config.MYSQL_DB_PASSWD = defaults['mysql_db_passwd']
    Config.MYSQL_DB_NAME = defaults['mysql_db_name']

    Config.MAIN_CHANNEL_NAME = defaults['main_channel_name']
    Config.MATCH_CHANNEL_CATEGORY_NAME = defaults['match_category_name']
    Config.LEAGUE_NAME = defaults['league_name']

    if defaults['test_level'] == '0':
        Config.DEBUG_LEVEL = DebugLevel.FULL_DEBUG
    elif defaults['test_level'] == '1':
        Config.DEBUG_LEVEL = DebugLevel.BOT_DEBUG
    elif defaults['test_level'] == '2':
        Config.DEBUG_LEVEL = DebugLevel.TEST
    elif defaults['test_level'] == '3':
        Config.DEBUG_LEVEL = DebugLevel.RUN
        Config.STAFF_ROLE = 'CoNDOR Staff'

    Config.CONFIG_FILE = config_filename


# Testing--------------------------------------------------------------------------------------

class TestConfig(unittest.TestCase):
    def test_init_and_write(self):
        init('data/necrobot_config')
        Config.CONFIG_FILE = 'data/config_write_test'
        Config.write()
