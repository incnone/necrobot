import asyncio
import googleapiclient.errors
import necrobot.exception

from necrobot.util.backoff import ExponentialBackoff


async def make_request(request):
    backoff = ExponentialBackoff(base=1, timeout=15)

    while True:
        try:
            return request.execute()
        except googleapiclient.errors.HttpError as e:
            backoff_errors = [429, 502]
            error_type = e.resp.status
            if error_type in backoff_errors:
                try:
                    await asyncio.sleep(backoff.delay())
                except necrobot.exception.TimeoutException:
                    raise e
            else:
                raise
