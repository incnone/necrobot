import discord
from typing import List
from necrobot.util.singleton import Singleton


class MatchGlobals(metaclass=Singleton):
    def __init__(self):
        self._deadline_fn = MatchGlobals._default_deadline
        self._channel_categories = []     # type: List[discord.Channel]

    def set_deadline_fn(self, f):
        self._deadline_fn = f

    def set_channel_categories(self, channels: List[discord.Channel]):
        self._channel_categories = channels

    def add_channel_category(self, channel: discord.Channel):
        self._channel_categories.append(channel)

    @property
    def deadline(self):
        return self._deadline_fn()

    @property
    def channel_categories(self) -> List[discord.Channel]:
        return self._channel_categories

    @staticmethod
    def _default_deadline():
        return None
