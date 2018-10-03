import discord
from necrobot.util.singleton import Singleton


class MatchGlobals(metaclass=Singleton):
    def __init__(self):
        self._deadline_fn = MatchGlobals._default_deadline
        self._channel_category = None

    def set_deadline_fn(self, f):
        self._deadline_fn = f

    def set_channel_category(self, channel: discord.Channel):
        self._channel_category = channel

    @property
    def deadline(self):
        return self._deadline_fn()

    @property
    def channel_category(self):
        return self._channel_category

    @staticmethod
    def _default_deadline():
        return None
