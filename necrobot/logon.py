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

import discord

from necrobot import config
from necrobot.botbase.necrobot import Necrobot
# from necrobot.stream.vodrecord import VodRecorder
from necrobot.util import console
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
    log_timestr_format = '%Y-%m-%d-%H-%M-%S'
    log_file_format = '{prefix}-{timestr}.log'
    log_output_filename = os.path.join(
        'logging',
        log_file_format.format(prefix=logging_prefix, timestr=datetime.datetime.utcnow().strftime(log_timestr_format))
    )

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
    try:
        logger.info('Beginning main loop.')
        # Create the discord.py Client object and the Necrobot----
        intents = discord.Intents.default()
        intents.members = True
        client = discord.Client(intents=intents)
        the_necrobot = Necrobot()
        the_necrobot.clean_init()
        the_necrobot.ready_client_events(client=client, load_config_fn=load_config_fn, on_ready_fn=on_ready_fn)

        client.run(config.Config.LOGIN_TOKEN)

    finally:
        # VodRecorder().end_all_async_unsafe()
        config.Config.write()
