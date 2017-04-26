import asyncio
import sys

from necrobot import loader, logon
from necrobot.util import ratelimit


async def on_ready_fn(necrobot):
    sys.stdout.flush()
    await asyncio.sleep(1)

    try:
        msg_rl_pair = await ratelimit.send_and_get_rate_limit(
            necrobot.client,
            necrobot.find_channel('season5'),
            'hi'
        )
        print(msg_rl_pair[1])
    except SystemExit:
        pass
    finally:
        await necrobot.logout()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/condorbot_config',
        load_config_fn=loader.load_condorbot_config,
        on_ready_fn=on_ready_fn
    )
