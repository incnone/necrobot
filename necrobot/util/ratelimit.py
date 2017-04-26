"""
Copies in a lot of code from discord.py because I want direct access to rate limit information

Working with stuff I shouldn't be accessing, so hopefully discord.py updates with getting rate-limit info sometime soon
"""
import asyncio
import datetime
import logging

import discord
import discord.http
from discord import utils
from discord.errors import HTTPException, Forbidden, NotFound


log = logging.getLogger('discord')
global_over = None


class RateLimitInfo(object):
    def __init__(self):
        self.limit = None
        self.remaining = None
        self.reset = None
        self.now = None

    def __str__(self):
        return 'Limit {0}, Remaining {1}, Reset {2}, Now {3}, Delta {4}'.format(
            self.limit, self.remaining, self.reset, self.now, self.time_until_reset)

    @property
    def time_until_reset(self) -> datetime.timedelta:
        delta = self.reset - self.now
        if delta.total_seconds() >= 0:
            return delta
        else:
            return datetime.timedelta(seconds=0)


# noinspection PyProtectedMember
@asyncio.coroutine
def send_and_get_rate_limit(
        client: discord.Client,
        channel: discord.Channel,
        content: str
):
    global global_over
    global_over = asyncio.Event(loop=asyncio.get_event_loop())
    global_over.set()

    channel_id, guild_id = yield from client._resolve_destination(channel)

    rate_limit_info = RateLimitInfo()
    data = yield from send_message(client.http, channel_id, content, rate_limit_info)
    channel = client.get_channel(data.get('channel_id'))
    # noinspection PyArgumentList
    message = client.connection._create_message(channel=channel, **data)
    return message, rate_limit_info


@asyncio.coroutine
def send_message(
        self: discord.http.HTTPClient,
        channel_id,
        content,
        rate_limit_info,
        *,
        tts=False,
        embed=None
):
    r = discord.http.Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
    payload = {}

    if content:
        payload['content'] = content

    if tts:
        payload['tts'] = True

    if embed:
        payload['embed'] = embed

    return request(self, r, rate_limit_info, json=payload)


@asyncio.coroutine
def request(
        self: discord.http.HTTPClient,
        route: discord.http.Route,
        rate_limit_info: RateLimitInfo,
        *,
        header_bypass_delay=None,
        **kwargs
):
    global global_over

    bucket = route.bucket
    method = route.method
    url = route.url

    lock = self._locks.get(bucket)
    if lock is None:
        lock = asyncio.Lock(loop=self.loop)
        if bucket is not None:
            self._locks[bucket] = lock

    # header creation
    headers = {
        'User-Agent': self.user_agent,
    }

    if self.token is not None:
        headers['Authorization'] = 'Bot ' + self.token if self.bot_token else self.token

    # some checking if it's a JSON request
    if 'json' in kwargs:
        headers['Content-Type'] = 'application/json'
        kwargs['data'] = utils.to_json(kwargs.pop('json'))

    kwargs['headers'] = headers

    if not global_over.is_set():
        # wait until the global lock is complete
        yield from global_over.wait()

    yield from lock
    with discord.http.MaybeUnlock(lock) as maybe_lock:
        for tries in range(5):
            r = yield from self.session.request(method, url, **kwargs)
            log.debug(self.REQUEST_LOG.format(method=method, url=url, status=r.status, json=kwargs.get('data')))
            try:
                # even errors have text involved in them so this is safe to call
                data = yield from discord.http.json_or_text(r)

                # check if we have rate limit header information
                rate_limit_info.remaining = r.headers.get('X-Ratelimit-Remaining')
                if rate_limit_info.remaining is not None:
                    rate_limit_info.limit = r.headers['X-Ratelimit-Limit']
                    rate_limit_info.now = discord.http.parsedate_to_datetime(r.headers['Date'])
                    rate_limit_info.reset = datetime.datetime.fromtimestamp(
                                int(r.headers['X-Ratelimit-Reset']),
                                datetime.timezone.utc
                            )

                if rate_limit_info.remaining == '0' and r.status != 429:
                    # we've depleted our current bucket
                    if header_bypass_delay is None:
                        now = discord.http.parsedate_to_datetime(r.headers['Date'])
                        reset = datetime.datetime.fromtimestamp(
                            int(r.headers['X-Ratelimit-Reset']),
                            datetime.timezone.utc
                        )
                        delta = (reset - now).total_seconds()
                    else:
                        delta = header_bypass_delay

                    fmt = 'A rate limit bucket has been exhausted (bucket: {bucket}, retry: {delta}).'
                    log.info(fmt.format(bucket=bucket, delta=delta))
                    maybe_lock.defer()
                    self.loop.call_later(delta, lock.release)

                # the request was successful so just return the text/json
                if 300 > r.status >= 200:
                    log.debug(self.SUCCESS_LOG.format(method=method, url=url, text=data))
                    return data

                # we are being rate limited
                if r.status == 429:
                    fmt = 'We are being rate limited. Retrying in {:.2} seconds. Handled under the bucket "{}"'

                    # sleep a bit
                    retry_after = data['retry_after'] / 1000.0
                    log.info(fmt.format(retry_after, bucket))

                    # check if it's a global rate limit
                    is_global = data.get('global', False)
                    if is_global:
                        log.info('Global rate limit has been hit. Retrying in {:.2} seconds.'.format(retry_after))
                        global_over.clear()

                    yield from asyncio.sleep(retry_after, loop=self.loop)
                    log.debug('Done sleeping for the rate limit. Retrying...')

                    # release the global lock now that the
                    # global rate limit has passed
                    if is_global:
                        global_over.set()
                        log.debug('Global rate limit is now over.')

                    continue

                # we've received a 502, unconditional retry
                if r.status == 502 and tries <= 5:
                    yield from asyncio.sleep(1 + tries * 2, loop=self.loop)
                    continue

                # the usual error cases
                if r.status == 403:
                    raise Forbidden(r, data)
                elif r.status == 404:
                    raise NotFound(r, data)
                else:
                    raise HTTPException(r, data)
            finally:
                # clean-up just in case
                yield from r.release()
