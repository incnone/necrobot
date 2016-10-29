import asyncio

from .channel.mainchannel import MainBotChannel
from .channel.pmbotchannel import PMBotChannel
from .daily.dailymanager import DailyManager
from .necrodb import NecroDB
from .race.racemanager import RaceManager
from .util import config

# from util.userprefs import PrefsModule
#
# from daily.dailymodule import DailyModule


class Necrobot(object):
    # Barebones constructor
    # client: [discord.Client] 
    # logger: [logging.Logger]
    def __init__(self, client, logger):
        self.client = client                    # the discord.Client object
        self.server = None                      # the discord.Server on which to read commands
        self.admin_id = None                    # int (discord user id)
        self.necrodb = NecroDB()                # NecroDB object
        self.logger = logger                    # logging.Logger

        self._main_discord_channel = None       # discord.Channel

        self._bot_channels = {}                 # maps discord.Channels onto BotChannels
        self._pm_bot_channel = PMBotChannel(self)

        self.prefs = None                       # userprefs.Prefsmodule
        self._daily_manager = DailyManager(self)
        self._race_manager = RaceManager(self)

    # Initializes object; call after client has been logged in to discord
    # server_id: [int]
    # admin_id: [int]
    def post_login_init(self, server_id, admin_id=None):
        self.admin_id = admin_id

        # set up server
        id_is_int = False
        try:
            server_id_int = int(server_id)
            id_is_int = True
        except ValueError:
            id_is_int = False

        if self.client.servers:
            for s in self.client.servers:
                if id_is_int and s.id == server_id:
                    print("Server id: {}".format(s.id))
                    self.server = s
                elif s.name == server_id:
                    print("Server id: {}".format(s.id))
                    self.server = s
        else:
            print('Error: Could not find the server.')
            exit(1)

        self._main_discord_channel = self.find_channel(config.MAIN_CHANNEL_NAME)
        self.register_bot_channel(self._main_discord_channel, MainBotChannel(self))
        # self.prefs = PrefsModule(self, self.necrodb)
        # self.load_module(self.prefs)

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

    # Return the #necrobot_main channel
    # return: [discord.Channel]
    @property
    def main_channel(self):
        return self._main_discord_channel

    # Return the #command_list channel
    # return: [discord.Channel]
    @property
    def ref_channel(self):
        for channel in self.server.channels:
            if channel.name == config.REFERENCE_CHANNEL_NAME:
                return channel
        return None

    # Get a list of all admin roles on the server
    # return: [list<discord.Role>]
    @property
    def admin_roles(self):
        admin_roles = []
        for rolename in config.ADMIN_ROLE_NAMES:
            for role in self.server.roles:
                if role.name == rolename:
                    admin_roles.append(role)
        return admin_roles

    @property
    def race_manager(self):
        return self._race_manager

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

    # Returns the channel with the given name on the server, if any
    # channel_name: [string]
    # return: [discord.Channel]
    def find_channel(self, channel_name):
        for channel in self.server.channels:
            if channel.name == channel_name:
                return channel
        return None

    # Returns a list of all members with a given username (capitalization ignored)
    # username: [string]
    # return: [list<discord.Member>]
    def find_members(self, username):
        to_return = []
        for member in self.server.members:
            if member.name == username:
                to_return.append(member)
        return to_return

    # Returns the given Discord user as a member of the server
    # user: [discord.User]
    # return: [discord.Member]
    def get_as_member(self, user):
        for member in self.server.members:
            if member.id == user.id:
                return member

    # Registers all users currently on the server
    def register_all_users(self):
        self.necrodb.register_all_users(self.server.members)

    # Registers a specific user on the server
    # member: [discord.Member]
    def register_user(self, member):
        self.necrodb.register_all_users([member])

# Coroutines--------------------
    # Log out of discord
    async def logout(self):
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

        # only reply on-server or to PM
        if not cmd.is_private and cmd.server != self.server:
            return

        # let each module attempt to handle the command in turn
        for module in self.modules:
            asyncio.ensure_future(module.execute(cmd))
