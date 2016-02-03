import asyncio
import datetime
import discord
import logging
import os
import sqlite3
import textwrap
import time

import command
import config
import seedgen

from necrobot import Necrobot

from colorer import ColorerModule
from dailymodule import DailyModule
from racemodule import RaceModule
from seedgenmodule import SeedgenModule

##-Logging-------------------------------
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
##--------------------------------------

class LoginData(object):
    email = ''
    password = ''
    admin_id = None
    server_id = None

#----Main------------------------------------------------------
config.init()
login_data = LoginData()                                                        # data to be read from the login file

login_info = open('data/login_info', 'r')
login_data.email = login_info.readline().rstrip('\n')
login_data.password = login_info.readline().rstrip('\n')
login_data.admin_id = login_info.readline().rstrip('\n')
login_data.server_id = login_info.readline().rstrip('\n')
login_info.close()

seedgen.init_seed()

client = discord.Client()                                                       # the client for discord
necrobot = Necrobot(client, sqlite3.connect(config.DB_FILENAME))                # main class for necrobot behavior
     
# Define client events
@client.event
@asyncio.coroutine
def on_ready():
    print('-Logged in---------------')
    print('User name: {0}'.format(client.user.name))
    print('User id  : {0}'.format(client.user.id))
    print('-------------------------')
    print(' ')
    print('Initializing necrobot...')
    necrobot.post_login_init(login_data.server_id, login_data.admin_id)

    necrobot.load_module(ColorerModule(necrobot))
    necrobot.load_module(SeedgenModule(necrobot))
    necrobot.load_module(DailyModule(necrobot, necrobot.db_conn))
    necrobot.load_module(RaceModule(necrobot, necrobot.db_conn))
    print('...done.')

@client.event
@asyncio.coroutine
def on_message(message):
    cmd = command.Command(message)
    yield from necrobot.execute(cmd)

# Run client
client.run(login_data.email, login_data.password)
