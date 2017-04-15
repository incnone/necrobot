from necrobot.botbase.necrodb import NecroDB
from necrobot.daily.dailymanager import DailyManager
from necrobot.necrobot.mainchannel import MainBotChannel
from necrobot.necrobot.pmbotchannel import PMBotChannel
from necrobot.user.prefsmanager import PrefsManager
from necrobot.race.racemanager import RaceManager
from necrobot.util import console
from necrobot.util.config import Config


class Necrobot(object):
    # Barebones constructor
    # client: [discord.Client] 
    # logger: [logging.Logger]
    def __init__(self, client):
        self.client = client                    # the discord.Client object
        self.server = None                      # the discord.Server on which to read commands

        self._main_discord_channel = None       # discord.Channel

        self._bot_channels = {}                 # maps discord.Channels onto BotChannels
        self._pm_bot_channel = None

        self._daily_manager = None
        self._race_manager = None
        self._prefs_manager = None

        self._initted = False
        self._quitting = False

    # Initializes object; call after client has been logged in to discord
    # server_id: [int]
    def post_login_init(self, server_id):
        console.info('-Logged in---------------')
        console.info('User name: {0}'.format(self.client.user.name))
        console.info('User id  : {0}'.format(self.client.user.id))

        # set up server
        try:
            int(server_id)
            id_is_int = True
        except ValueError:
            id_is_int = False

        if self.client.servers:
            for s in self.client.servers:
                if id_is_int and s.id == server_id:
                    console.info("Server id: {}".format(s.id))
                    self.server = s
                elif s.name == server_id:
                    console.info("Server id: {}".format(s.id))
                    self.server = s
        else:
            console.error('Could not find the server.')
            exit(1)

        console.info('-------------------------')
        console.info(' ')

        self._main_discord_channel = self.find_channel(Config.MAIN_CHANNEL_NAME)
        if self._main_discord_channel is None:
            console.error('Could not find the "{0}" necrobot.'.format(Config.MAIN_CHANNEL_NAME))
            exit(1)

        if not self._initted:
            # Create new data
            self.register_bot_channel(self._main_discord_channel, MainBotChannel(self))
            self._pm_bot_channel = PMBotChannel(self)
            self._daily_manager = DailyManager(self)
            self._race_manager = RaceManager(self)
            self._prefs_manager = PrefsManager(self)
            self._initted = True
        else:
            self.refresh()

    def refresh(self):
        channel_pairs = {}
        for channel, bot_channel in self._bot_channels.items():
            new_channel = self.find_channel_with_id(channel.id)
            if new_channel is not None:
                channel_pairs[new_channel] = bot_channel
            bot_channel.refresh(new_channel)
        self._bot_channels = channel_pairs

        if self._daily_manager is not None:
            self._daily_manager.refresh()
        if self._race_manager is not None:
            self._race_manager.refresh()
        if self._prefs_manager is not None:
            self._prefs_manager.refresh()

    def cleanup(self):
        if self._daily_manager is not None:
            self._daily_manager.close()
        if self._race_manager is not None:
            self._race_manager.close()
        if self._prefs_manager is not None:
            self._prefs_manager.close()
        self._bot_channels.clear()

    # Returns the BotChannel corresponding to the given discord.Channel, if one exists
    # discord_channel: [discord.Channel]
    def get_bot_channel(self, discord_channel):
        if discord_channel.is_private:
            return self._pm_bot_channel
        else:
            return self._bot_channels[discord_channel]

    # Causes the Necrobot to use the given module
    # Doesn't check for duplicates
    # module: [command.Module]
    def register_bot_channel(self, discord_channel, bot_channel):
        self._bot_channels[discord_channel] = bot_channel

    def unregister_bot_channel(self, discord_channel):
        del self._bot_channels[discord_channel]

    # True if the bot wants to quit (i.e. if logout() has been called)
    @property
    def quitting(self):
        return self._quitting

    # Return the #necrobot_main necrobot
    # return: [discord.Channel]
    @property
    def main_channel(self):
        return self._main_discord_channel

    # Get a list of all admin roles on the server
    # return: [list<discord.Role>]
    @property
    def admin_roles(self):
        admin_roles = []
        for rolename in Config.ADMIN_ROLE_NAMES:
            for role in self.server.roles:
                if role.name == rolename:
                    admin_roles.append(role)
        return admin_roles

    @property
    def race_manager(self):
        return self._race_manager

    @property
    def daily_manager(self):
        return self._daily_manager

    @property
    def prefs_manager(self):
        return self._prefs_manager

    # Returns true if the user is a server admin
    # user: [discord.User]
    # return: [bool]
    def is_admin(self, user):
        member = self.get_as_member(user)
        admin_roles = self.admin_roles
        for role in member.roles:
            if role in admin_roles:
                return True
        return False

    # Returns the necrobot with the given name on the server, if any
    # channel_name: [string]
    # return: [discord.Channel]
    def find_channel(self, channel_name):
        for channel in self.server.channels:
            if channel.name == channel_name:
                return channel
        return None

    # Returns the necrobot with the given name on the server, if any
    # channel_name: [int]
    # return: [discord.Channel]
    def find_channel_with_id(self, channel_id):
        for channel in self.server.channels:
            if int(channel.id) == int(channel_id):
                return channel
        return None

    # Returns a member with a given username (capitalization ignored)
    # username: [string]
    # return: [list<discord.Member>]
    def find_member(self, username):
        for member in self.server.members:
            if member.display_name.lower() == username.lower():
                return member

    # Returns a list of all members with a given username (capitalization ignored)
    # username: [string]
    # return: [list<discord.Member>]
    def find_members(self, username):
        to_return = []
        for member in self.server.members:
            if member.display_name.lower() == username.lower():
                to_return.append(member)
        return to_return

    # Returns the given Discord user as a member of the server
    # user: [discord.User]
    # return: [discord.Member]
    def get_as_member(self, user):
        for member in self.server.members:
            if int(member.id) == int(user.id):
                return member

    # Registers all users currently on the server
    def register_all_users(self):
        NecroDB().register_all_users(self.server.members)

    # Registers a specific user on the server
    # member: [discord.Member]
    @staticmethod
    def register_user(member):
        NecroDB().register_all_users([member])

# Coroutines--------------------
    # Log out of discord
    async def logout(self):
        self._quitting = True
        await self.client.logout()

    # Log out of discord, but do not set quitting flag
    async def reboot(self):
        await self.client.logout()

    # Call this when anyone joins the server
    async def on_member_join(self, member):
        self.register_user(member)
        
    # Executes a command
    # cmd: [command.Command]
    async def execute(self, cmd):
        # don't care about bad commands
        if cmd.command is None:
            return

        # don't reply to self
        if cmd.author == self.client.user:
            return

        # handle the command with the appropriate bot necrobot
        if cmd.is_private:
            await self._pm_bot_channel.execute(cmd)
        elif cmd.channel in self._bot_channels:
            await self._bot_channels[cmd.channel].execute(cmd)
