import asyncio
import command
import config

class Die(command.CommandType):
    def __init__(self, admin_module):
        command.CommandType.__init__(self, 'die')
        self.help_text = ''
        self.suppress_help = True
        self._am = admin_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._am.necrobot.is_admin(command.author):
            yield from self._am.necrobot.logout()

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._am.necrobot.main_channel

class Info(command.CommandType):
    def __init__(self, admin_module):
        command.CommandType.__init__(self, 'info')
        self.help_text = "Necrobot version information."
        self._am = admin_module

    @asyncio.coroutine
    def _do_execute(self, command):
        yield from self._am.client.send_message(command.channel, 'Necrobot v-{0} (alpha). See {1} for a list of commands.'.format(config.BOT_VERSION, self._am.necrobot.ref_channel.mention))

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._am.necrobot.main_channel

## TODO: this doesn't work yet.
## TODO: it'd be nice to have an "update" command that spawns a bootstrapping process to pull from github and then restart this process
##class Reboot(command.CommandType):
##    def __init__(self, admin_module):
##        command.CommandType.__init__(self, 'reboot')
##        self.help_text = "Reboot Necrobot. Admin only."
##        self._am = admin_module
##
##    @asyncio.coroutine
##    def _do_execute(self, command):
##        if self._am.necrobot.is_admin(command.author):
##            yield from self._am.necrobot.reboot()
    
class AdminModule(command.Module):
    def __init__(self, necrobot):
        command.Module.__init__(self, necrobot)
        self.command_types = [Die(self),
                              Info(self)]

    @property
    def infostr(self):
        return 'Admin commands'
