# Credit to Hornwitser -- https://gist.github.com/Hornwitser/93aceb86533ed3538b6f

import random
import time
import necrobot.exception


class ExponentialBackoff:
    """An implementation of the exponential backoff algorithm

    Provides a convenient interface to implement an exponential backoff
    for reconnecting or retrying transmissions in a distributed network.

    Once instantiated, the delay method will return the next interval to
    wait for when retrying a connection or transmission.  The maximum
    delay increases exponentially with each retry up to a maximum of
    2^10 * base, and is reset if no more attempts are needed in a period
    of 2^11 * base seconds.

    Parameters
    ----------
    base
        The base delay in seconds.  The first retry-delay will be up to
        this many seconds.  Defaults to 1
    integral : bool
        Set to True if whole periods of base is desirable, otherwise any
        number in between may be returnd. Defaults to False.
    """

    def __init__(self, base=1, *, integral=False, timeout=None):
        self._base = base

        self._exp = 0
        self._max = 10
        self._last_invocation = time.monotonic()
        self._timeout = min(timeout, base * 2 ** (self._max + 1)) \
            if timeout is not None else base * 2 ** (self._max + 1)

        # Use our own random instance to avoid messing with global one
        rand = random.Random()
        rand.seed()

        self._randfunc = rand.rand_range if integral else rand.uniform

    def delay(self):
        """Compute the next delay

        Returns the next delay to wait according to the exponential
        backoff algorithm.  This is a value between 0 and base * 2^exp
        where exponent starts off at 1 and is incremented at every
        invocation of this method up to a maximum of 10.

        If a period of more than the timout has passed since the last
        retry, raise a TimeoutException.
        """
        invocation = time.monotonic()
        interval = invocation - self._last_invocation
        self._last_invocation = invocation

        if interval > self._timeout:
            raise necrobot.exception.TimeoutException()

        self._exp = min(self._exp + 1, self._max)
        return self._randfunc(0, self._base * 2 ** self._exp)

    def reset(self):
        """Reset the delay"""
        self._exp = 0
