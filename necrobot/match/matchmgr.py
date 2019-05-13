import discord

from necrobot.botbase.necroevent import NEDispatch, NecroEvent
from necrobot.botbase.manager import Manager
from necrobot.botbase.necrobot import Necrobot
from necrobot.match import matchdb, matchutil
from necrobot.match.matchroom import MatchRoom
from necrobot.match.matchglobals import MatchGlobals
from necrobot.util import console, server
from necrobot.util.singleton import Singleton
from necrobot.config import Config


class MatchMgr(Manager, metaclass=Singleton):
    def __init__(self):
        NEDispatch().subscribe(self)

    async def initialize(self):
        await self._recover_stored_match_rooms()
        category_channels = server.find_all_channels(channel_name=Config.MATCH_CHANNEL_CATEGORY_NAME)
        MatchGlobals().set_channel_categories(category_channels)

    async def refresh(self):
        pass

    async def close(self):
        pass

    def on_botchannel_create(self, channel, bot_channel):
        pass

    # noinspection PyMethodMayBeStatic
    async def ne_process(self, ev: NecroEvent):
        if ev.event_type == 'rtmp_name_change':
            for row in await matchdb.get_channeled_matches_raw_data():
                if int(row[2]) == ev.user.user_id or int(row[3]) == ev.user.user_id:
                    channel_id = int(row[13])
                    channel = server.find_channel(channel_id=channel_id)
                    if channel is not None:
                        read_perms = discord.PermissionOverwrite(read_messages=True)
                        await server.client.edit_channel_permissions(
                            channel=channel,
                            target=ev.user.member,
                            overwrite=read_perms
                        )

    @staticmethod
    async def _recover_stored_match_rooms() -> None:
        """Recover MatchRoom objects on bot init
        
        Creates MatchRoom objects for `Match`es in the database which are registered (via their `channel_id`) to
        some discord.Channel on the server.
        """
        console.info('Recovering stored match rooms------------')
        for row in await matchdb.get_channeled_matches_raw_data():
            channel_id = int(row[13])
            channel = server.find_channel(channel_id=channel_id)
            if channel is not None:
                match = await matchutil.make_match_from_raw_db_data(row=row)
                new_room = MatchRoom(match_discord_channel=channel, match=match)
                Necrobot().register_bot_channel(channel, new_room)
                await new_room.initialize()
                console.info('  Channel ID: {0}  Match: {1}'.format(channel_id, match))
            else:
                console.info('  Couldn\'t find channel with ID {0}.'.format(channel_id))
        console.info('-----------------------------------------')
