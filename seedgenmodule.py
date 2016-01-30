import asyncio

import command
import seedgen

class RandomSeed(command.CommandType):
    def __init__(self, seedgen_module):
        command.CommandType.__init__(self, 'randomseed')
        self.help_text = "Get a randomly generated seed (returns a random integer between {0} and {1}).".format(seedgen.MIN_SEED, seedgen.MAX_SEED)
        self._sm = seedgen_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.channel.is_private or command.channel == self._sm.main_channel:
            seed = seedgen.get_new_seed()
            yield from self._sm.client.send_message(command.channel, 'Seed generated for {0}: {1}'.format(command.author.mention, seed))

class SeedgenModule(command.Module):
    def __init__(self, necrobot):
        command.Module.__init__(self)
        self._necrobot = necrobot
        self.command_types = [command.DefaultHelp(self),
                              RandomSeed(self)]

    @property
    def infostr(self):
        return 'Seed generation'

    @property
    def client(self):
        return self._necrobot.client

    @property
    def main_channel(self):
        return self._necrobot.main_channel
        
