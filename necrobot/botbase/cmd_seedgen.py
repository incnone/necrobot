from necrobot.botbase.commandtype import CommandType
from necrobot.util.necrodancer import seedgen

MAX_NUM_SEEDS_TO_GENERATE = 20


class RandomSeed(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'randomseed')
        self.help_text = "Get a randomly generated seed (returns a random integer between {0} and {1}). " \
                         "Calling `{2} N` will generate N seeds and return them via PM. " \
                         "(Limited to {3} seeds at once.)".format(
                            seedgen.MIN_SEED,
                            seedgen.MAX_SEED,
                            self.mention,
                            MAX_NUM_SEEDS_TO_GENERATE)

    async def _do_execute(self, command):
        if len(command.args) == 0:
            seed = seedgen.get_new_seed()
            await self.client.send_message(
                command.channel,
                'Seed generated for {0}: {1}'.format(command.author.mention, seed))

        elif len(command.args) == 1:
            try:
                num_seeds = max(0, min(MAX_NUM_SEEDS_TO_GENERATE, int(command.args[0])))
                seedstr = ''
                for i in range(num_seeds):
                    seedstr += '{}, '.format(seedgen.get_new_seed())
                if seedstr:
                    await self.client.send_message(
                        command.author,
                        'Generated {0} seeds: {1}.'.format(num_seeds, seedstr[:-2]))
            except ValueError:
                pass
