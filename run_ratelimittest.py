import asyncio
import sys

import run_condorbot
from necrobot.botbase import server
from necrobot import logon
from necrobot.util import ratelimit


async def on_ready_fn(necrobot):
    sys.stdout.flush()
    await asyncio.sleep(1)

    try:
        msg_rl_pair = await ratelimit.send_and_get_rate_limit(
            server.client,
            server.main_channel,
            'testing rate limit'
        )
        print(msg_rl_pair[1])
    except SystemExit:
        pass
    finally:
        await necrobot.logout()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/condorbot_config',
        load_config_fn=run_condorbot.load_condorbot_config,
        on_ready_fn=on_ready_fn
    )
