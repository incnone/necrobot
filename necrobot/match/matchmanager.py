from necrobot.util import console
from necrobot.database import matchdb
from necrobot.match import matchutil

from necrobot.botbase.necrobot import Necrobot
from necrobot.match.matchroom import MatchRoom
from necrobot.util.singleton import Singleton


class MatchManager(object, metaclass=Singleton):
    def __init__(self):
        pass

    async def initialize(self):
        await self._recover_stored_match_rooms()

    async def refresh(self):
        pass

    async def close(self):
        pass

    @staticmethod
    async def _recover_stored_match_rooms() -> None:
        """Recover MatchRoom objects on bot init
        
        Creates MatchRoom objects for `Match`es in the database which are registered (via their `channel_id`) to
        some discord.Channel on the server.
        """
        console.info('Recovering stored match rooms------------')
        for row in await matchdb.get_channeled_matches_raw_data():
            channel_id = int(row[13])
            channel = Necrobot().find_channel_with_id(channel_id)
            if channel is not None:
                match = await matchutil.make_match_from_raw_db_data(row=row)
                new_room = MatchRoom(match_discord_channel=channel, match=match)
                Necrobot().register_bot_channel(channel, new_room)
                await new_room.initialize()
                console.info('  Channel ID: {0}  Match: {1}'.format(channel_id, match))
            else:
                console.info('  Couldn\'t find channel with ID {0}.'.format(channel_id))
        console.info('-----------------------------------------')
