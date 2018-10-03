import asyncio
import discord

from necrobot.util import server
from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.botbase.necrobot import Necrobot
from necrobot.test import msgqueue
from necrobot.config import Config


class TestCommandType(CommandType):
    def __init__(self, bot_channel, cmd_name):
        CommandType.__init__(self, bot_channel, cmd_name)
        self.admin_only = True
        self.testing_command = True

    def get_send_func(self, channel):
        async def send(author, msg, wait_for=None):
            if wait_for is not None:
                wait_ev = await self.wait_event(wait_for)

            await self.client.send_message(channel, "`{0}` {1}".format(author.display_name, msg))
            await Necrobot().force_command(channel=channel, author=author, message_str=msg)

            if wait_for is not None:
                # noinspection PyUnboundLocalVariable
                await wait_ev.wait()
        return send

    @staticmethod
    async def wait_event(msg_str: str):
        def starts_with_str(msg: discord.Message) -> bool:
            return msg_str in msg.content
        return await msgqueue.register_event(starts_with_str)


class TestCreateCategory(TestCommandType):
    def __init__(self, bot_channel):
        TestCommandType.__init__(self, bot_channel, 'testcreatecategory')
        self.help_text = "Make the 'Race Rooms' category channel."

    async def _do_execute(self, cmd: Command):
        await server.create_channel_category(Config.MATCH_CHANNEL_CATEGORY_NAME)


class TestMatch(TestCommandType):
    def __init__(self, bot_channel):
        TestCommandType.__init__(self, bot_channel, 'testmatch')
        self.help_text = "Run a full match from test code. " \
                         "WARNING: This takes several minutes and is only for debugging."

    async def _do_execute(self, cmd: Command):
        fancy = len(cmd.args) == 1 and cmd.args[0] == 'fancy'
        send = self.get_send_func(cmd.channel)

        match = self.bot_channel.match
        racer_1 = match.racer_1.member
        racer_2 = match.racer_2.member
        admin = server.find_admin(ignore=[racer_1.name, racer_2.name])
        if racer_1 is None or racer_2 is None or admin is None:
            await self.client.send_message(
                cmd.channel,
                "Can't find one of the racers (as a Discord member) in this match."
            )
            return

        # Match info
        await send(racer_1, '.matchinfo', wait_for='')
        await send(admin, '.setmatchtype bestof 5', wait_for='This match has been set')
        await send(admin, '.setmatchtype repeat 3', wait_for='This match has been set')

        # Time suggestion
        await send(racer_1, '.suggest friday 8p', wait_for='This match is suggested')
        await send(racer_2, '.suggest tomorrow 12:30', wait_for='This match is suggested')
        await send(racer_1, '.confirm', wait_for='officially scheduled')
        await send(racer_2, '.unconfirm', wait_for='wishes to remove')
        await send(racer_1, '.unconfirm', wait_for='has been unscheduled')

        # Prematch admin commands
        await send(admin, '.f-schedule tomorrow 21:15', wait_for='This match is suggested')
        await send(admin, '.f-confirm', wait_for='Forced confirmation')
        await send(admin, '.postpone', wait_for='has been postponed')
        await send(admin, '.f-begin', wait_for='Please input')

        # Race 1
        await send(racer_1, '.ready', wait_for='is ready')
        await send(racer_2, '.ready', wait_for='The race will begin')
        await send(racer_1, '.unready', wait_for='is no longer ready')
        await send(racer_1, '.r', wait_for='GO!')
        await send(racer_1, '.d', wait_for='Please input')

        # Race 2
        await send(admin, '.reseed', wait_for='Changed seed')
        await send(racer_2, '.ready', wait_for='is ready')
        await send(racer_1, '.ready', wait_for='GO!')
        await send(admin, '.pause', wait_for='Race paused')
        await send(admin, '.unpause', wait_for='GO!')
        await send(racer_1, '.time', wait_for='The current race time')
        await send(racer_2, '.d', wait_for='has finished in')
        await send(racer_1, '.d', wait_for='Please input')

        # Race 3:
        if not fancy:
            await send(racer_1, '.ready', wait_for='is ready')
            await send(racer_2, '.ready', wait_for='GO!')
            await send(racer_1, '.d', wait_for='Match complete')
        else:
            await send(admin, '.cancelrace 1', wait_for='')
            await send(admin, '.recordrace "{0}"'.format(racer_2.display_name), wait_for='')
            await send(admin, '.changewinner 2 "{0}"'.format(racer_1.display_name), wait_for='')
            await send(admin, '.postpone', wait_for='has been postponed')
            await send(admin, '.f-begin', wait_for='Please input')
            await send(admin, '.changerules diamond u', wait_for='Changed rules')
            await send(admin, '.matchinfo', wait_for='')
            await send(admin, '.changerules cadence s', wait_for='Changed rules')
            await send(admin, '.matchinfo', wait_for='')
            await send(racer_1, '.r', wait_for='is ready')
            await send(racer_2, '.r', wait_for='GO!')
            await send(admin, '.pause', wait_for='Race paused')
            await send(admin, '.cancelrace', wait_for='Please input')

            # Race 4:
            await send(racer_1, '.r', wait_for='is ready')
            await send(racer_2, '.r', wait_for='GO!')
            await send(admin, '.pause', wait_for='Race paused')
            await send(admin, '.newrace', wait_for='Please input')

            # Race 5:
            await send(racer_1, '.r', wait_for='is ready')
            await send(racer_2, '.r', wait_for='GO!')
            await send(racer_1, '.d', wait_for='Match complete')
            await send(admin, '.matchinfo', wait_for='')
            await send(admin, '.newrace', wait_for='Please input')

            # Race 6:
            await send(racer_1, '.r', wait_for='is ready')
            await send(racer_2, '.r', wait_for='GO!')
            await send(racer_2, '.d', wait_for='Match complete')

            await send(admin, '.cancelrace 3')


class TestRace(TestCommandType):
    def __init__(self, bot_channel):
        TestCommandType.__init__(self, bot_channel, 'testrace')
        self.help_text = "Run a full race from test code. " \
                         "WARNING: This takes several minutes and is only for debugging."

    async def _do_execute(self, cmd: Command):
        send = self.get_send_func(cmd.channel)

        alice = server.find_member(discord_name='incnone_testing')
        bob = server.find_member(discord_name='condorbot_alpha')
        carol = server.find_member(discord_name='condorbot')
        admin = server.find_member(discord_name='incnone')

        if alice is None or bob is None or carol is None or admin is None:
            await self.client.send_message(
                cmd.channel,
                "Can't find one of the racers (as a Discord member) in this match."
            )
            return

        # Race 1: some common stuff
        await send(alice, '.r', wait_for='Waiting on')
        await send(bob, '.e', wait_for='2 entrants')
        await send(alice, '.ready', wait_for='is already ready')
        await send(bob, '.ready', wait_for='The race will begin')
        await send(alice, '.unready', wait_for='is no longer ready')
        await send(alice, '.r', wait_for='GO!')
        await send(carol, '.notify', wait_for='will be alerted')
        await send(alice, '.f', wait_for='has forfeit')
        await send(alice, '.unforfeit', wait_for='no longer forfeit')
        await send(bob, '.death 3-2', wait_for='has forfeit')
        await send(bob, '.c spirits are fair')
        await asyncio.sleep(2)
        await send(alice, '.d', wait_for='The race is over')
        await send(alice, '.igt 4:20.69')
        await send(bob, '.re', wait_for='Race number')
        await send(alice, '.c i did it')

        # Race 2: admin stuff
        await send(alice, '.join')
        await send(carol, '.j')
        await send(admin, '.e', wait_for='3 entrants')
        await send(alice, '.missing', wait_for='Unentered')
        await send(bob, '.r')
        await send(alice, '.r')
        await send(carol, '.r', wait_for='1 remaining')
        await send(alice, '.poke')
        await send(bob, '.poke')
        await send(admin, '.kick "{0}"'.format(alice.display_name), wait_for='no longer entered')
        await send(alice, '.r', wait_for='is ready')
        await send(admin, '.reseed', wait_for='Changed seed')
        await send(admin, '.changerules Diamond u custom have a blast with diamond', wait_for="Couldn't parse")
        await send(admin, '.changerules Diamond u custom "have a blast with diamond"', wait_for="Changed rules")
        await send(admin, '.reseed', wait_for='This is not a seeded race')
        await send(admin, '.unenter', wait_for='GO!')
        await send(admin, '.pause', wait_for='Race paused')
        await send(bob, '.time', wait_for='The current race time')
        asyncio.sleep(1)
        await send(carol, '.time', wait_for='The current race time')
        await send(admin, '.forceforfeit "{0}"'.format(carol.display_name), wait_for='has forfeit')
        await send(alice, '.missing', wait_for='Still racing')
        await send(alice, '.d')
        asyncio.sleep(1)
        await send(admin, '.unpause', wait_for='GO!')
        await send(carol, '.d', wait_for='has finished')
        await send(bob, '.d 5-4 i can\'t deep blues', wait_for='has forfeit')
        await send(bob, '.notify off', wait_for='not be alerted')
        await send(carol, '.undone', wait_for='continues to race')
        await send(alice, '.d', wait_for='has finished')
        await send(carol, '.d', wait_for='The race is over')

        # Race 3
        await send(alice, '.re', wait_for='Race number')
        await send(alice, '.r')
        await send(carol, '.r', wait_for='GO!')
        await send(admin, '.forceforfeitall', wait_for='The race is over')




