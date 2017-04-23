from necrobot.botbase.command import Command, CommandType
from necrobot.match import matchutil


class CloseAllMatches(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'closeallmatches')
        self.help_text = '[Admin only] Close all match rooms. Use `{0} nolog` to close all rooms without writing ' \
                         'logs (much faster, but no record will be kept of room chat).' \
                         .format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        log = not(len(cmd.args) == 1 and cmd.args[0].lstrip('-').lower() == 'nolog')

        await self.client.send_message(
            cmd.channel,
            'Closing all match channels...'
        )
        await self.client.send_typing(cmd.channel)

        await matchutil.delete_all_match_channels(log=log)

        await self.client.send_message(
            cmd.channel,
            'Done closing all match channels.'
        )


# class CloseFinished(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'closefinished')
#         self.help_text = '[Admin only] Close all match rooms with completed matches. Use `{0} nolog` to close ' \
#                          'without writing logs (much faster, but no record will be kept of room chat).' \
#                          .format(self.mention)
#         self.admin_only = True
#
#     async def _do_execute(self, cmd: Command):
#         log = not(len(cmd.args) == 1 and cmd.args[0].lstrip('-').lower() == 'nolog')
#
#         await self.client.send_message(
#             cmd.channel,
#             'Closing all completed match channels...'
#         )
#         await self.client.send_typing(cmd.channel)
#
#         await matchutil.delete_all_completed_match_channels(log=log)  # TODO
#
#         await self.client.send_message(
#             cmd.channel,
#             'Done closing all completed match channels.'
#         )
