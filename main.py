import aiohttp
import asyncio
import datetime
import discord
import logging
import os
import websockets

import botconfigs

from necrobot.botbase.command import Command
from necrobot.botbase.necrobot import Necrobot
from necrobot.util import backoff, config, console, seedgen


# Define client events
def ready_client_events(client, the_necrobot):
    # Called after the client has successfully logged in
    @client.event
    async def on_ready():
        await the_necrobot.post_login_init(
            client=client,
            server_id=config.Config.SERVER_ID,
            # load_config_fn=botconfigs.load_standard_config  # TODO put back
            load_config_fn=botconfigs.load_testing_config
        )

    # Called whenever a new message is posted in any necrobot on any server
    @client.event
    async def on_message(message):
        cmd = Command(message)
        await the_necrobot.execute(cmd)

    # Called when a new member joins any server
    @client.event
    async def on_member_join(member):
        await the_necrobot.on_member_join(member)


def main(def_client_events):
    # Logging--------------------------------------------------
    file_format_str = '%Y-%m-%d'
    utc_today = datetime.datetime.utcnow().date()
    utc_today_str = utc_today.strftime(file_format_str)

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
    console.info('Initializing necrobot...')
    config.init('data/bot_config')

    # Seed the random number generator------------------------
    seedgen.init_seed()

    # Run client---------------------------------------------
    retry = backoff.ExponentialBackoff()

    logger.info('Entering main loop.')
    while True:
        logger.info('Beginning main loop: creating ')
        # Create the discord.py Client object and the Necrobot----
        client = discord.Client()
        the_necrobot = Necrobot()
        def_client_events(client, the_necrobot)

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
                    raise  # Do not reconnect on authentication failure

                logger.exception('Exception while running.')

            finally:
                for task in asyncio.Task.all_tasks(asyncio.get_event_loop()):
                    task.cancel()

                asyncio.get_event_loop().run_until_complete(asyncio.sleep(retry.delay()))

        if the_necrobot.quitting:
            break


if __name__ == "__main__":
    main(ready_client_events)
