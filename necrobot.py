import asyncio
import discord
import logging
import seedgen
import mysql.connector

import config
import command
import colorer

from necrodb import NecroDB
from adminmodule import AdminModule
from userprefs import PrefsModule

class Necrobot(object):
    
    # Barebones constructor
    # client: [discord.Client] 
    # logger: [logging.Logger]
    def __init__(self, client, logger):
        self.client = client
        self.server = None
        self.prefs = None
        self.modules = []
        self.admin_id = None
        self.necrodb = NecroDB()
        self.logger = logger
        self._main_channel = None
        self._wants_to_quit = False
        self._admin_module = None

    # Initializes object; call after client has been logged in to discord
    # server_id: [int]
    # admin_id: [int]
    def post_login_init(self, server_id, admin_id=0):
        self.admin_id = admin_id if admin_id else None

        #set up server
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

        self._main_channel = self.find_channel(config.MAIN_CHANNEL_NAME)
        self.load_module(AdminModule(self))
        self.prefs = PrefsModule(self, self.necrodb)
        self.load_module(self.prefs)

    # Causes the Necrobot to use the given module
    # Doesn't check for duplicates
    # module: [command.Module]
    def load_module(self, module):
        self.modules.append(module)

    # True if the bot wants to quit (and not re-login)
    # return: [bool]
    @property
    def quitting(self):
        return self._wants_to_quit

    # Return the #necrobot_main channel
    # return: [discord.Channel]
    @property
    def main_channel(self):
        return self._main_channel

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

    ##--Coroutines--------------------
    # Log out of discord
    async def logout(self):
        self._wants_to_quit = True
        await self.client.logout()

    # Reboot our login to discord (log out, but do not set quitting = true)
    async def reboot(self):
        self._wants_to_quit = False
        await self.client.logout()

    # Call this when anyone joins the server
    async def on_member_join(self, member):
        self.register_user(member)
        
    # Executes a command
    # cmd: [command.Command]
    async def execute(self, cmd):
        # don't care about bad commands
        if cmd.command == None:
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
