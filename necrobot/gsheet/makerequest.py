import asyncio
import googleapiclient.errors
from necrobot.util.backoff import ExponentialBackoff
from necrobot.util.exception import TimeoutException


async def make_request(request):
    backoff = ExponentialBackoff(base=1, timeout=30)

    while True:
        try:
            return request.execute()
        except googleapiclient.errors.HttpError as e:
            backoff_errors = [403, 429]
            error_type = e.resp.status
            if error_type in backoff_errors:
                try:
                    await asyncio.sleep(backoff.delay())
                except TimeoutException:
                    raise e
            else:
                raise
