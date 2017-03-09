import asyncio
import aiohttp
import datetime
import logging
import os
import sys
import websockets

import discord
from necrobot.command.command import Command
from necrobot.necrobot import Necrobot
from necrobot.util import backoff, config, seedgen


# Define client events
def ready_client_events():
    # Called after the client has successfully logged in
    @client.event
    async def on_ready():
        print('-Logged in---------------')
        print('User name: {0}'.format(client.user.name))
        print('User id  : {0}'.format(client.user.id))
        the_necrobot.post_login_init(config.Config.SERVER_ID)
        print('-------------------------')
        print(' ')

    # Called whenever a new message is posted in any channel on any server
    @client.event
    async def on_message(message):
        cmd = Command(message)
        await the_necrobot.execute(cmd)

    # Called when a new member joins any server
    @client.event
    async def on_member_join(member):
        await the_necrobot.on_member_join(member)


if __name__ == "__main__":
    # Prepend timestamps to stdout and stderr, and send output to logging
    class StampedOutput(object):
        def __init__(self, out_str):
            self._out_str = out_str
            self._logger = logging.getLogger('discord')
            self._warning_level = out_str == sys.stderr

        new_line = True

        def _do_logging(self, s):
            if self._warning_level:
                self._logger.warning(s)
            else:
                self._logger.info(s)

        def flush(self):
            pass

        def write(self, s):
            if s == '\n':
                self._out_str.write(s)
                self.new_line = True
            elif self.new_line:
                self._out_str.write(s)
                self._do_logging('[{0}]: {1}'.format(datetime.datetime.utcnow().strftime("%H-%M-%S"), s))
                self.new_line = False
            else:
                self._out_str.write(s)
                self._do_logging(s)


    sys.stdout = StampedOutput(sys.stdout)
    sys.stderr = StampedOutput(sys.stderr)

    print('Initializing necrobot...')

    # Logging--------------------------------------------------
    file_format_str = '%Y-%m-%d'
    utc_today = datetime.datetime.utcnow().date()
    utc_yesterday = utc_today - datetime.timedelta(days=1)
    utc_today_str = utc_today.strftime(file_format_str)
    utc_yesterday_str = utc_yesterday.strftime(file_format_str)

    filenames_in_dir = os.listdir('logging')

    # Get log output filename
    filename_rider = 0
    while True:
        filename_rider += 1
        log_output_filename = '{0}-{1}.log'.format(utc_today_str, filename_rider)
        if not (log_output_filename in filenames_in_dir):
            break
    # noinspection PyUnboundLocalVariable
    log_output_filename = 'logging/{0}'.format(log_output_filename)

    # Set up logger
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename=log_output_filename, encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

# Initialize config file----------------------------------
    config.init('data/bot_config')

# Seed the random number generator------------------------
    seedgen.init_seed()

# Try to get login data from login_info if you didn't find it in bot_config; for back-compatibility
    if config.Config.LOGIN_TOKEN == '':
        login_info = open('data/login_info', 'r')
        config.Config.LOGIN_TOKEN = login_info.readline().rstrip('\n')
        login_info.readline().rstrip('\n')
        config.Config.SERVER_ID = login_info.readline().rstrip('\n')
        login_info.close()

# Run client---------------------------------------------
    retry = backoff.ExponentialBackoff()

    logger.info('Entering main loop.')
    while True:
        logger.info('Beginning main loop: creating ')
        # Create the discord.py Client object and the Necrobot----
        client = discord.Client()
        the_necrobot = Necrobot(client)
        ready_client_events()

        while not client.is_logged_in:
            try:
                asyncio.get_event_loop().run_until_complete(client.login(config.Config.LOGIN_TOKEN))
            except (discord.HTTPException, aiohttp.ClientError):
                logger.exception('Exception while logging in.')
                asyncio.get_event_loop().run_until_complete(asyncio.sleep(retry.delay()))
            else:
                break

        while client.is_logged_in:
            if client.is_closed:
                # noinspection PyProtectedMember
                client._closed.clear()
                client.http.recreate()

            try:
                logger.info('Connecting.')
                asyncio.get_event_loop().run_until_complete(client.connect())

            except (discord.HTTPException,
                    aiohttp.ClientError,
                    discord.GatewayNotFound,
                    discord.ConnectionClosed,
                    websockets.InvalidHandshake,
                    websockets.WebSocketProtocolError) as e:

                if isinstance(e, discord.ConnectionClosed) and e.code == 4004:
                    raise       # Do not reconnect on authentication failure

                logger.exception('Exception while running.')

            finally:
                for task in asyncio.Task.all_tasks(asyncio.get_event_loop()):
                    task.cancel()

                asyncio.get_event_loop().run_until_complete(asyncio.sleep(retry.delay()))

        if the_necrobot.quitting:
            break
