import asyncio
import datetime
import discord
import logging
import os
import mysql.connector

import command
import config
import seedgen

from necrobot import Necrobot

from colorer import ColorerModule
from dailymodule import DailyModule
from racemodule import RaceModule
from seedgenmodule import SeedgenModule

print('Initializing necrobot...')

##-Logging-------------------------------
file_format_str = '%b%d'
utc_today = datetime.datetime.utcnow().date()
utc_yesterday = utc_today - datetime.timedelta(days=1)
utc_today_str = utc_today.strftime(file_format_str)
utc_yesterday_str = utc_yesterday.strftime(file_format_str)

filenames_in_dir = os.listdir('logging')
#### clean old logs
##for file in filenames_in_dir:
##    if not file.startswith(utc_today_str) or file.startswith(utc_yesterday_str):
##        os.remove(file)

## get log output filename
filename_rider = 0
while True:
    filename_rider += 1
    log_output_filename = '{0}-{1}.log'.format(utc_today_str, filename_rider)
    if not (log_output_filename in filenames_in_dir):
        break
log_output_filename = 'logging/{0}'.format(log_output_filename)

## set up logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=log_output_filename, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
##--------------------------------------

class LoginData(object):
    token = ''
    admin_id = None
    server_id = None

#----Main------------------------------------------------------
config.init('data/bot_config')
login_data = LoginData()                                                        # data to be read from the login file

login_info = open('data/login_info', 'r')
login_data.token = login_info.readline().rstrip('\n')
login_data.admin_id = login_info.readline().rstrip('\n')
login_data.server_id = login_info.readline().rstrip('\n')
login_info.close()

seedgen.init_seed()

client = discord.Client()                                                       # the client for discord
necrobot = Necrobot(client, logger)        # main class for necrobot behavior

# Define client events
@client.event
@asyncio.coroutine
def on_ready():
    print('-Logged in---------------')
    print('User name: {0}'.format(client.user.name))
    print('User id  : {0}'.format(client.user.id))
    necrobot.post_login_init(login_data.server_id, login_data.admin_id)

    necrobot.load_module(ColorerModule(necrobot))
    necrobot.load_module(SeedgenModule(necrobot))
    necrobot.load_module(DailyModule(necrobot, necrobot.necrodb))
    necrobot.load_module(RaceModule(necrobot, necrobot.necrodb))
    print('-------------------------')
    print(' ')

@client.event
@asyncio.coroutine
def on_message(message):
    cmd = command.Command(message)
    yield from necrobot.execute(cmd)

@client.event
@asyncio.coroutine
def on_member_join(member):
    yield from necrobot.on_member_join(member)

# Run client
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.login(login_data.token))
    loop.run_until_complete(client.connect())
except Exception:
    loop.run_until_complete(client.close())
finally:
    loop.close()
