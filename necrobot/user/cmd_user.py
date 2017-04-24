import pytz

from mysql.connector import IntegrityError

from necrobot.user import userutil

from necrobot.botbase.commandtype import CommandType
from necrobot.user.userprefs import UserPrefs
from necrobot.config import Config

MAX_USERINFO_LEN = 255


class DailyAlert(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dailyalert')
        self.help_text = "Set daily alerts on or off for your account. " \
                         "Use `{0} on` or `{0} off`.".format(self.mention)

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1 or cmd.args[0].lower() not in ['on', 'off']:
            await self.client.send_message(
                cmd.channel,
                "Couldn't parse cmd. Call `{0} on` or `{0} off`.".format(self.mention))
            return

        user_prefs = UserPrefs()
        if cmd.args[0] == 'on':
            user_prefs.daily_alert = True
        else:
            user_prefs.daily_alert = False

        userutil.get_user(discord_id=int(cmd.author.id), register=True).set(user_prefs=user_prefs, commit=True)

        if user_prefs.daily_alert:
            await self.client.send_message(
                cmd.channel,
                "{0}: You will now receive PM alerts with the new daily seeds.".format(cmd.author.mention))
        else:
            await self.client.send_message(
                cmd.channel,
                "{0}: You will no longer receive PM alerts for dailies.".format(cmd.author.mention))


class RaceAlert(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'racealert')
        self.help_text = "Set race alerts on or off for your account. " \
                         "Use `{0} on` or `{0} off`.".format(self.mention)

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1 or cmd.args[0].lower() not in ['on', 'off']:
            await self.client.send_message(
                cmd.channel,
                "Couldn't parse cmd. Call `{0} on` or `{0} off`.".format(self.mention))
            return

        user_prefs = UserPrefs()
        if cmd.args[0] == 'on':
            user_prefs.race_alert = True
        else:
            user_prefs.race_alert = False

        userutil.get_user(discord_id=int(cmd.author.id), register=True).set(user_prefs=user_prefs, commit=True)

        if user_prefs.race_alert:
            await self.client.send_message(
                cmd.channel,
                "{0}: You will now receive PM alerts when a new raceroom is made.".format(cmd.author.mention))
        else:
            await self.client.send_message(
                cmd.channel,
                "{0}: You will no longer receive PM alerts for races.".format(cmd.author.mention))


class ViewPrefs(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'viewprefs', 'getprefs')
        self.help_text = "See your current user preferences."

    async def _do_execute(self, cmd):
        prefs = userutil.get_user(discord_id=int(cmd.author.id)).user_prefs
        prefs_string = ''
        for pref_str in prefs.pref_strings:
            prefs_string += ' ' + pref_str
        await self.client.send_message(
            cmd.author,
            'Your current user preferences: {}'.format(prefs_string))


class RTMP(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'rtmp')
        self.help_text = 'Register an RTMP stream. Usage is ' \
                         '`{0} discord_name rtmp_name`.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd):
        if len(cmd.args) != 2:
            await self.client.send_message(
                cmd.channel,
                '{0}: I was unable to parse your request name because you gave the wrong number of arguments. '
                'Use `{1} discord_name rtmp_name`.'.format(cmd.author.mention, self.mention))
            return

        # Get the user
        discord_name = cmd.args[0]
        user = userutil.get_user(discord_name=discord_name)
        if user is None:
            await self.client.send_message(
                cmd.channel,
                'Error: Unable to find the user `{0}`.'.format(discord_name))
            return

        rtmp_name = cmd.args[1]
        try:
            user.set(rtmp_name=rtmp_name)
        except IntegrityError:
            duplicate_user = userutil.get_user(rtmp_name=rtmp_name)
            if duplicate_user is None:
                await self.client.send_message(
                    cmd.channel,
                    'Unexpected error: Query raised a mysql.connector.IntegrityError, but couldn\'t find a racer '
                    'with RTMP name `{0}`.'.format(rtmp_name)
                )
            else:
                await self.client.send_message(
                    cmd.channel,
                    'Error: This RTMP is already registered to the discord user `{0}`.'.format(
                        duplicate_user.discord_name)
                )
            return

        await self.client.send_message(
            cmd.channel,
            '{0}: Registered the RTMP `{1}` to user `{2}`.'.format(
                cmd.author.mention, rtmp_name, user.discord_name))


class SetInfo(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setinfo')
        self.help_text = 'Add additional information to be displayed on `{0}`.'.format(self.mention)

    async def _do_execute(self, cmd):
        cut_length = len(cmd.command) + len(Config.BOT_COMMAND_PREFIX) + 1
        info = cmd.message.content[cut_length:]

        if len(info) > MAX_USERINFO_LEN:
            await self.client.send_message(
                cmd.channel,
                '{0}: Error: `.setinfo` is limited to {1} characters.'.format(cmd.author.mention, MAX_USERINFO_LEN))
            return

        if '\n' in info or '`' in info:
            await self.client.send_message(
                cmd.channel,
                '{0}: Error: `.setinfo` cannot contain newlines or backticks.'.format(cmd.author.mention))
            return

        userutil.get_user(discord_id=int(cmd.author.id), register=True).set(user_info=info, commit=True)
        await self.client.send_message(
            cmd.channel,
            '{0}: Updated your user info.'.format(cmd.author.mention))


class Timezone(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'timezone')
        self._timezone_loc = 'https://github.com/incnone/condorbot/blob/master/data/tz_list.txt'
        self.help_text = 'Register a time zone with your account. Usage is `{1} zone_name`. See <{0}> for a ' \
                         'list of recognized time zones; these strings should be input exactly as-is, e.g., ' \
                         '`.timezone US/Eastern`.'.format(self._timezone_loc, self.mention)

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                '{0}: I was unable to parse your timezone because you gave the wrong number of arguments. '
                'See <{1}> for a list of timezones.'.format(cmd.author.mention, self._timezone_loc))
            return

        tz_name = cmd.args[0]
        if tz_name in pytz.common_timezones:
            userutil.get_user(discord_id=int(cmd.author.id), register=True).set(timezone=tz_name, commit=True)
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

    async def _do_execute(self, cmd):
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
            userutil.get_user(discord_id=int(cmd.author.id), register=True).set(twitch_name=twitch_name, commit=True)
            await self.client.send_message(
                cmd.channel,
                '{0}: Registered your twitch as `twitch.tv/{1}`.'.format(
                    cmd.author.mention, twitch_name))


class UserInfo(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'userinfo')
        self.help_text = 'Get stream and timezone info for the given user (or yourself, if no user provided). ' \
                         'Usage is `.userinfo name`.'

    async def _do_execute(self, cmd):
        if len(cmd.args) > 1:
            await self.client.send_message(
                cmd.channel, 'Error: Too many arguments for `{0}`.'.format(self.mention))
            return

        # find the user's discord id
        if len(cmd.args) == 0:
            racer = userutil.get_user(discord_id=cmd.author.id, register=True)
        else:
            racer = userutil.get_user(any_name=cmd.args[0])
            if racer is None:
                await self.client.send_message(
                    cmd.channel, 'Couldn\'t find a user by the name `{0}`.'.format(cmd.args[0]))
                return

        await self.client.send_message(cmd.channel, racer.infobox)


class Register(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register')
        self.help_text = 'Register your current Discord name as the name to use for the bot.'

    async def _do_execute(self, cmd):
        self.necrobot.register_user(cmd.author)
        await self.client.send_message(cmd.channel, 'Registered your name as {0}.'.format(cmd.author.mention))


class RegisterAll(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'registerall')
        self.help_text = 'Register all unregistered users.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        self.necrobot.register_all_users()
        await self.client.send_message(cmd.channel, 'Registered all unregistered users.')
