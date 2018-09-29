# from necrobot.condor.condormgr import CondorMgr
from necrobot.botbase.necroevent import NEDispatch
from necrobot.botbase.commandtype import CommandType
from necrobot.util import server


class StaffAlert(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'staff')
        self.help_text = 'Alert the CoNDOR Staff to a problem.'

    async def _do_execute(self, cmd):
        msg = 'Alert: `.staff` called by `{0}` in channel {1}.'.format(cmd.author.display_name, cmd.channel.mention)
        await NEDispatch().publish('notify', message=msg)

        if server.staff_role is not None:
            await self.client.send_message(
                cmd.channel,
                '{0}: Alerting CoNDOR Staff: {1}.'.format(
                    cmd.author.mention,
                    server.staff_role.mention
                )
            )


# class UpdateSchedule(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'updateschedule')
#         self.help_text = 'Update the #schedule channel.'
#         self.admin_only = True
#
#     async def _do_execute(self, cmd):
#         await CondorMgr().update_schedule_channel()
