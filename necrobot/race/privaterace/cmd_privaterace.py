from necrobot.botbase.commandtype import CommandType


class Add(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'add')
        self.help_text = 'Give a user permission to see the room.'
        self.admin_only = True

    async def _do_execute(self, command):
        for username in command.args:
            for member in self.necrobot.find_members(username):
                await self.bot_channel.allow(member)
                await self.bot_channel.write('Added {} to the room.'.format(member.mention))
        return True


class NoPost(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'nopost')
        self.help_text = 'Ask the bot not to post results of this race in the results necrobot. (On by default.)'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.set_post_result(False)


class Post(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'post')
        self.help_text = 'Ask the bot to post results of this race in the results necrobot.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.set_post_result(True)


class ShowAdmins(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'showadmins', 'admins')
        self.help_text = 'List all admins for this race.'

    async def _do_execute(self, command):
        admin_names = ''
        for member in self.bot_channel.permission_info.admins:
            admin_names += member.name + ', '
        for role in self.bot_channel.permission_info.admin_roles:
            admin_names += role.name + ' (role), '

        if admin_names:
            await self.bot_channel.write('The admins for this room are: {}'.format(admin_names[:-2]))
        else:
            await self.bot_channel.write('No admins for this room.')


class Remove(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'remove')
        self.help_text = "Remove a user's permission to see the room."
        self.admin_only = True

    async def _do_execute(self, command):
        for username in command.args:
            for member in self.necrobot.find_members(username):
                if self.bot_channel.is_admin(member):
                    await self.bot_channel.write(
                        'Cannot remove {0}, as they are an admin for this room.'.format(member.display_name))
                else:
                    await self.bot_channel.deny(member)
                    await self.bot_channel.write('Removed {0} from the room.'.format(member.display_name))


class MakeAdmin(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'admin', 'makeadmin')
        self.help_text = 'Make specified users into admins for the race (cannot be undone).'
        self.admin_only = True

    async def _do_execute(self, command):
        for username in command.args:
            for member in self.necrobot.find_members(username):
                await self.bot_channel.allow(member)
                if member not in self.bot_channel.permission_info.admins:
                    self.bot_channel.permission_info.admins.append(member)
                await self.bot_channel.write('Made {0} an admin for the race.'.format(member.display_name))
