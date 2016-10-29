import command


# import sys



class AdminModule(command.Module):
    def __init__(self, necrobot):
        command.Module.__init__(self, necrobot)
        self.command_types = [Die(self),
                              Info(self),
                              Register(self),
                              RegisterAll(self)]
        
    @property
    def infostr(self):
        return 'Admin commands'
