import mysql.connector
import pytz

from necrobot.botbase.necroevent import NEDispatch
from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.user import userlib
from necrobot.user.necrouser import NecroUser
from necrobot.user.userprefs import UserPrefs

MAX_USERINFO_LEN = 255


class DailyAlert(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dailyalert')
        self.help_text = "Set daily alerts on or off for your account. " \
                         "Use `{0} on` or `{0} off`.".format(self.mention)

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1 or cmd.args[0].lower() not in ['on', 'off']:
            await self.client.send_message(
                cmd.channel,
                "Couldn't parse cmd. Call `{0} on` or `{0} off`.".format(self.mention)
            )
            return

        user_prefs = UserPrefs(daily_alert=(cmd.args[0] == 'on'), race_alert=None)

        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        user.set(user_prefs=user_prefs, commit=True)

        if user_prefs.daily_alert:
            await self.client.send_message(
                cmd.channel,
                "{0}: You will now receive PM alerts with the new daily seeds.".format(cmd.author.mention)
            )
        else:
            await self.client.send_message(
                cmd.channel,
                "{0}: You will no longer receive PM alerts for dailies.".format(cmd.author.mention)
            )


class ForceRTMP(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-rtmp')
        self.help_text = 'Register an RTMP stream for another user. Usage is ' \
                         '`{0} discord_name rtmp_name`.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 2:
            await self.client.send_message(
                cmd.channel,
                '{0}: I was unable to parse your request name because you gave the wrong number of arguments. '
                'Use `{1} discord_name rtmp_name`.'.format(cmd.author.mention, self.mention))
            return

        # Get the user
        discord_name = cmd.args[0]
        user = await userlib.get_user(discord_name=discord_name)
        if user is None:
            await self.client.send_message(
                cmd.channel,
                'Error: Unable to find the user `{0}`.'.format(discord_name))
            return

        rtmp_name = cmd.args[1]
        await _do_rtmp_register(cmd, self, user, rtmp_name)


class RaceAlert(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'racealert')
        self.help_text = "Set race alerts on or off for your account. " \
                         "Use `{0} on` or `{0} off`.".format(self.mention)

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1 or cmd.args[0].lower() not in ['on', 'off']:
            await self.client.send_message(
                cmd.channel,
                "Couldn't parse cmd. Call `{0} on` or `{0} off`.".format(self.mention))
            return

        user_prefs = UserPrefs(daily_alert=None, race_alert=(cmd.args[0] == 'on'))

        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        user.set(user_prefs=user_prefs, commit=True)

        if user_prefs.race_alert:
            await self.client.send_message(
                cmd.channel,
                "{0}: You will now receive PM alerts when a new raceroom is made.".format(cmd.author.mention)
            )
        else:
            await self.client.send_message(
                cmd.channel,
                "{0}: You will no longer receive PM alerts for races.".format(cmd.author.mention)
            )


class RTMP(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'rtmp')
        self.help_text = 'Register an RTMP stream. Usage is `{0} rtmp_name`.'.format(self.mention)

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                '{0}: I was unable to parse your request name because you gave the wrong number of arguments. '
                'Use `{1} rtmp_name`.'.format(cmd.author.mention, self.mention))
            return

        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        rtmp_name = cmd.args[0]
        await _do_rtmp_register(cmd, self, user, rtmp_name)


class SetInfo(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setinfo')
        self.help_text = 'Add additional information to be displayed on `{0}`.'.format(self.mention)

    async def _do_execute(self, cmd: Command):
        if len(cmd.arg_string) > MAX_USERINFO_LEN:
            await self.client.send_message(
                cmd.channel,
                '{0}: Error: `.setinfo` is limited to {1} characters.'.format(cmd.author.mention, MAX_USERINFO_LEN))
            return

        if '\n' in cmd.arg_string or '`' in cmd.arg_string:
            await self.client.send_message(
                cmd.channel,
                '{0}: Error: `.setinfo` cannot contain newlines or backticks.'.format(cmd.author.mention))
            return

        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        user.set(user_info=cmd.arg_string, commit=True)
        await self.client.send_message(
            cmd.channel,
            '{0}: Updated your user info.'.format(cmd.author.mention))


class Timezone(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'timezone')
        self._timezone_loc = 'https://github.com/incnone/necrobot/blob/master/docs/Timezones.txt'
        self.help_text = 'Register a time zone with your account. Usage is `{1} zone_name`. See <{0}> for a ' \
                         'list of recognized time zones; these strings should be input exactly as-is, e.g., ' \
                         '`.timezone US/Eastern`.'.format(self._timezone_loc, self.mention)

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                '{0}: I was unable to parse your timezone because you gave the wrong number of arguments. '
                'See <{1}> for a list of timezones.'.format(cmd.author.mention, self._timezone_loc))
            return

        tz_name = cmd.args[0]
        if tz_name in pytz.common_timezones:
            user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
            user.set(timezone=tz_name, commit=True)
            await self.client.send_message(
                cmd.channel,
                '{0}: Timezone set as {1}.'.format(cmd.author.mention, tz_name))
        else:
            await self.client.send_message(
                cmd.channel,
                '{0}: I was unable to parse your timezone. See <{1}> for a list of timezones.'.format(
                    cmd.author.mention, self._timezone_loc))


class Twitch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'twitch')
        self.help_text = 'Register a twitch stream. Usage is `{0} twitch_name`.'.format(self.mention)

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                '{0}: I was unable to parse your stream name because you gave the wrong number of arguments. '
                'Use `.twitch twitch_name`.'.format(cmd.author.mention))
            return

        twitch_name = cmd.args[0]
        if '/' in twitch_name:
            await self.client.send_message(
                cmd.channel,
                '{0}: Error: your twitch name cannot contain the character /. (Maybe you accidentally '
                'included the "twitch.tv/" part of your stream name?)'.format(cmd.author.mention))
        else:
            user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
            user.set(twitch_name=twitch_name, commit=True)
            await self.client.send_message(
                cmd.channel,
                '{0}: Registered your twitch as `twitch.tv/{1}`.'.format(
                    cmd.author.mention, twitch_name))


class UserInfo(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'userinfo')
        self.help_text = 'Get stream and timezone info for the given user (or yourself, if no user provided). ' \
                         'Usage is `.userinfo name`.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) > 1:
            await self.client.send_message(
                cmd.channel, 'Error: Too many arguments for `{0}`.'.format(self.mention))
            return

        # find the user's discord id
        if len(cmd.args) == 0:
            racer = await userlib.get_user(discord_id=cmd.author.id, register=True)
        else:
            racer = await userlib.get_user(any_name=cmd.args[0])
            if racer is None:
                await self.client.send_message(
                    cmd.channel, 'Couldn\'t find a user by the name `{0}`.'.format(cmd.args[0]))
                return

        await self.client.send_message(cmd.channel, racer.infobox)


class ViewPrefs(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'viewprefs', 'getprefs')
        self.help_text = "See your current user preferences."

    async def _do_execute(self, cmd: Command):
        user = await userlib.get_user(discord_id=int(cmd.author.id))
        prefs = user.user_prefs
        prefs_string = ''
        for pref_str in prefs.pref_strings:
            prefs_string += ' ' + pref_str
        await self.client.send_message(
            cmd.author,
            'Your current user preferences: {}'.format(prefs_string))


async def _do_rtmp_register(cmd: Command, cmd_type: CommandType, user: NecroUser, rtmp_name: str):
    try:
        user.set(rtmp_name=rtmp_name, commit=False)
        await user.commit()
    except mysql.connector.IntegrityError:
        duplicate_user = await userlib.get_user(rtmp_name=rtmp_name)
        if duplicate_user is None:
            await cmd_type.client.send_message(
                cmd.channel,
                'Unexpected error: Query raised a mysql.connector.IntegrityError, but couldn\'t find a racer '
                'with RTMP name `{0}`.'.format(rtmp_name)
            )
        else:
            await cmd_type.client.send_message(
                cmd.channel,
                'Error: This RTMP is already registered to the discord user `{0}`.'.format(
                    duplicate_user.discord_name)
            )
        return

    await NEDispatch().publish(event_type='rtmp_name_change', user=user)
    await cmd_type.client.send_message(
        cmd.channel,
        '{0}: Registered the RTMP `{1}` to user `{2}`.'.format(
            cmd.author.mention, rtmp_name, user.discord_name)
    )
