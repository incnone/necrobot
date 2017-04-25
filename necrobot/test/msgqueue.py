import asyncio
import discord

_msg_events = []
_events_lock = asyncio.Lock()


class MessageEvent(asyncio.Event):
    def __init__(self, predicate):
        asyncio.Event.__init__(self, loop=asyncio.get_event_loop())
        self.predicate = predicate

    def on_message(self, message: discord.Message):
        if self.predicate(message):
            self.set()


async def register_event(predicate):
    event = MessageEvent(predicate)
    async with _events_lock:
        _msg_events.append(event)
        return event


async def send_message(message: discord.Message):
    global _msg_events
    async with _events_lock:
        remaining_msg_events = []

        for event in _msg_events:
            event.on_message(message)
            if not event.is_set():
                remaining_msg_events.append(event)

        _msg_events = remaining_msg_events
