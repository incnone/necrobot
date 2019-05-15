import necrobot.exception
from necrobot.botbase.commandtype import CommandType
from necrobot.botbase.necrobot import Necrobot


class Die(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'die')
        self.help_text = 'Tell the bot to log out.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await Necrobot().logout()


# class Reboot(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'reboot')
#         self.help_text = 'Reboot the necrobot.'
#         self.admin_only = True
#
#     async def _do_execute(self, cmd):
#         await Necrobot().reboot()


class RedoInit(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'redoinit')
        self.help_text = 'Call Necrobot\'s initialization method.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await Necrobot().redo_init()


class RaiseException(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'raiseexception')
        self.help_text = 'Raise an exception.'
        self.admin_only = True
        self.testing_command = True

    async def _do_execute(self, cmd):
        raise necrobot.exception.NecroException('Raised by RaiseException.')
