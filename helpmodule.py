import command

class Help(command.CommandType):
    def __init__(self, help_module):
        command.CommandType.__init__(self, 'help')
        self.help_text = 'Help.'
        self._hm = help_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.args:
        else:
            

class HelpModule(command.Module):
    def __init__(self, necrobot):
        self._necrobot = necrobot
        self.command_types = []
    
    @property
    def infostr(self):
        return 'Help and information.'
        
    @property
    def client(self):
        return self._necrobot.client

    @property
    def modules(self):
        return self._necrobot.modules
