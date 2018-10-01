"""
Primary function for logging on to Discord. 

logon() blocks until the bot is logged out; any code to be run after bot log-on 
should be placed in a coroutine and passed to logon in the on_ready_fn parameter.
"""

import asyncio
import datetime
import logging
import os
import sys
import types
import warnings

import aiohttp
import discord
import websockets

from necrobot import config
from necrobot.botbase.necrobot import Necrobot
from necrobot.stream.vodrecord import VodRecorder
from necrobot.util import backoff, console
from necrobot.util.necrodancer import seedgen


def logon(
        config_filename: str,
        logging_prefix: str,
        load_config_fn: types.FunctionType,
        on_ready_fn: types.FunctionType = None
) -> None:
    """Log on to Discord. Block until logout.
    
    Parameters
    ----------
    config_filename: str
        The filename of the config file to use.
    logging_prefix: str
        A prefix to append to all logfile outputs.
    load_config_fn: [coro] (Necrobot) -> None
        A coroutine to be called after first login, which should set up the Necrobot with the desired
        BotChannels and Managers.
    on_ready_fn: [coro] (Necrobot) -> None
        A coroutine to be called after every login. Useful for unit testing.
    """
    # Initialize config file----------------------------------
    config.init(config_filename)

    # Asyncio debug setup-------------------------------------
    if config.Config.testing():
        asyncio.get_event_loop().set_debug(True)
        warnings.simplefilter("always", ResourceWarning)

    # Logging--------------------------------------------------
    file_format_prefix = logging_prefix
    file_format_str = file_format_prefix + '-%Y-%m-%d-%H-%M-%S'
    utc_today = datetime.datetime.utcnow()
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
    if config.Config.full_debugging():
        asyncio_level = logging.DEBUG
        discord_level = logging.DEBUG
        necrobot_level = logging.DEBUG
    elif config.Config.debugging():
        asyncio_level = logging.INFO
        discord_level = logging.INFO
        necrobot_level = logging.DEBUG
    elif config.Config.testing():
        asyncio_level = logging.INFO
        discord_level = logging.INFO
        necrobot_level = logging.INFO
    else:  # if config.Config.TEST_LEVEL == config.TestLevel.RUN:
        asyncio_level = logging.WARNING
        discord_level = logging.WARNING
        necrobot_level = logging.INFO

    stream_formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
    file_formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s: %(message)s')

    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stderr_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(filename=log_output_filename, encoding='utf-8', mode='w')

    # stdout_handler.setLevel(logging.INFO)
    # stderr_handler.setLevel(logging.INFO)

    stdout_handler.setFormatter(stream_formatter)
    stderr_handler.setFormatter(stream_formatter)
    file_handler.setFormatter(file_formatter)

    logging.getLogger('discord').setLevel(discord_level)
    logging.getLogger('discord').addHandler(file_handler)
    logging.getLogger('discord').addHandler(stderr_handler)
    logging.getLogger('asyncio').setLevel(asyncio_level)
    logging.getLogger('asyncio').addHandler(file_handler)
    logging.getLogger('asyncio').addHandler(stderr_handler)

    logger = logging.getLogger('necrobot')
    logger.setLevel(necrobot_level)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    console.info('Initializing necrobot...')

    # Seed the random number generator------------------------
    seedgen.init_seed()

    # Run client---------------------------------------------
    retry = backoff.ExponentialBackoff()

    try:
        while True:
            logger.info('Beginning main loop.')
            # Create the discord.py Client object and the Necrobot----
            client = discord.Client()
            the_necrobot = Necrobot()
            the_necrobot.clean_init()
            the_necrobot.ready_client_events(client=client, load_config_fn=load_config_fn, on_ready_fn=on_ready_fn)

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

    finally:
        asyncio.get_event_loop().close()
        VodRecorder().end_all_async_unsafe()
        config.Config.write()
