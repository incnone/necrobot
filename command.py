## Represents a user-entered command

import clparse
import config

class Flag(object):
    def __init__(self, arglist):
        self.name = None
        self.args = clparse.pop_command(arglist)
        if self.args:
            name = self.args.pop(0)
        elif arglist:
            self.name = arglist.pop(0)

class Command(object):
    def __init__(self, message):
        self.command = None
        self.flags = []
        self.message = None

        if message.content.startswith(config.BOT_COMMAND_PREFIX):
            args = message.content.split()
            prefix_len = len(config.BOT_COMMAND_PREFIX)
            self.command = args.pop(0)[prefix_len:]
            while args:
                self.flags.append(Flag(args))
            self.message = message

    @property
    def author(self):
        return self.message.author if self.message else None

    @property
    def server(self):
        return self.message.server if self.message else None

    @property
    def channel(self):
        return self.message.channel if self.message else None

    @property
    def private(self):
        return self.message.channel.is_private if self.message else None

# Abstract base class; represents a module that can be attached to the Necrobot
class Module(object):
    def __init__(self):
        pass

    #Overwrite this
    @property
    def infostr(self):
        return 'Unknown module.'

    #Overwrite this
    def execute(self, command):
        print('Error: Module.execute not overwritten.')
        pass
