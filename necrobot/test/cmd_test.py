import discord

from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.test import msgqueue


class TestCommandType(CommandType):
    def __init__(self, bot_channel, cmd_name):
        CommandType.__init__(self, bot_channel, cmd_name)
        self.admin_only = True
        self.testing_command = True

    def get_send_func(self, channel):
        async def send(racer, msg, wait_for=None):
            if wait_for is not None:
                wait_ev = await self.wait_event(wait_for)

            await self.client.send_message(channel, "`{0}` {1}".format(racer.display_name, msg))
            await self.necrobot.force_command(channel=channel, author=racer, message_str=msg)

            if wait_for is not None:
                # noinspection PyUnboundLocalVariable
                await wait_ev.wait()
        return send

    @staticmethod
    async def wait_event(msg_str: str):
        def starts_with_str(msg: discord.Message) -> bool:
            return msg_str in msg.content
        return await msgqueue.register_event(starts_with_str)


class TestMatch(TestCommandType):
    def __init__(self, bot_channel):
        TestCommandType.__init__(self, bot_channel, 'testmatch')
        self.help_text = "Run a full match from test code. WARNING: This is only for debugging."

    async def _do_execute(self, cmd: Command):
        send = self.get_send_func(cmd.channel)

        match = self.bot_channel.match
        racer_1 = match.racer_1.member
        racer_2 = match.racer_2.member
        admin = self.necrobot.find_admin(ignore=[racer_1.display_name, racer_2.display_name])
        if racer_1 is None or racer_2 is None or admin is None:
            await self.client.send_message(
                cmd.channel,
                "Can't find one of the racers (as a Discord member) in this match."
            )
            return

        # # Match info
        # await send(racer_1, '.matchinfo', wait_for='')
        # await send(admin, '.setmatchtype bestof 5', wait_for='This match has been set')
        # await send(admin, '.setmatchtype repeat 3', wait_for='This match has been set')
        #
        # # Time suggestion
        # await send(racer_1, '.suggest friday 8p', wait_for='This match is suggested')
        # await send(racer_2, '.suggest tomorrow 12:30', wait_for='This match is suggested')
        # await send(racer_1, '.confirm', wait_for='officially scheduled')
        # await send(racer_2, '.unconfirm', wait_for='wishes to remove')
        # await send(racer_1, '.unconfirm', wait_for='has been unscheduled')
        #
        # # Prematch admin commands
        # await send(admin, '.f-schedule tomorrow 21:15', wait_for='This match is suggested')
        # await send(admin, '.f-confirm', wait_for='Forced confirmation')
        # await send(admin, '.postpone', wait_for='has been postponed')
        # await send(admin, '.f-begin', wait_for='Please input')
        #
        # # Race 1: Racer 1 wins, no finish from Racer 2
        # await send(racer_1, '.ready', wait_for='is ready')
        # await send(racer_2, '.ready', wait_for='The race will begin')
        # await send(racer_1, '.unready', wait_for='is no longer ready')
        # await send(racer_1, '.r', wait_for='GO!')
        # await send(racer_1, '.d', wait_for='Please input')
        #
        # # Race 2: Try out admin commands, racer finish
        # await send(admin, '.reseed', wait_for='Changed seed')
        # await send(racer_2, '.ready', wait_for='is ready')
        # await send(racer_1, '.ready', wait_for='GO!')
        # await send(admin, '.pause', wait_for='Race paused')
        # await send(admin, '.unpause', wait_for='GO!')
        # await send(racer_1, '.time', wait_for='The current race time')
        # await send(racer_2, '.d', wait_for='has finished in')
        # await send(racer_1, '.d', wait_for='Please input')
        #
        # # Admin stuff
        # await send(admin, '.cancelrace 1', wait_for='')
        # await send(admin, '.f-recordrace "{0}"'.format(racer_2.display_name), wait_for='')
        await send(admin, '.changewinner 2 "{0}"'.format(racer_1.display_name), wait_for='')
        await send(admin, '.postpone', wait_for='has been postponed')
        await send(admin, '.f-begin', wait_for='Please input')

        # Race 3:
        await send(admin, '.changerules diamond u', wait_for='Changed rules')
        await send(admin, '.matchinfo', wait_for='')
        await send(admin, '.changerules cadence s', wait_for='Changed rules')
        await send(admin, '.matchinfo', wait_for='')
        await send(racer_1, '.r', wait_for='is ready')
        await send(racer_2, '.r', wait_for='GO!')

        await send(admin, '.pause', wait_for='Race paused')
        await send(admin, '.cancelrace', wait_for='Please input')
        await send(racer_1, '.r', wait_for='is ready')
        await send(racer_2, '.r', wait_for='GO!')

        await send(admin, '.pause', wait_for='Race paused')
        await send(admin, '.forcenewrace', wait_for='Please input')
        await send(racer_1, '.r', wait_for='is ready')
        await send(racer_2, '.r', wait_for='GO!')
        await send(racer_1, '.d', wait_for='The match has ended')

        await send(admin, '.matchinfo', wait_for='')
        await send(admin, '.f-newrace', wait_for='Please input')
        await send(racer_1, '.r', wait_for='is ready')
        await send(racer_2, '.r', wait_for='GO!')
        await send(racer_2, '.d', wait_for='The match has ended')

        await send(admin, '.cancelrace 3')
