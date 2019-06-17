import datetime
import googleapiclient.errors

import necrobot.exception
from necrobot.gsheet import sheetutil, sheetlib
from necrobot.speedrun import categories, speedrundb
from necrobot.user import userlib

from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.botbase.necroevent import NEDispatch
from necrobot.gsheet.speedrunsheet import SpeedrunSheet
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.speedrun.speedrunmgr import SpeedrunMgr
from necrobot.user.necrouser import NecroUser


class Submit(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'submit')
        allowed_category_str = ''
        for category_name in categories.category_list():
            allowed_category_str += '`{}`, '.format(category_name)
        if len(allowed_category_str) >= 2:
            allowed_category_str = allowed_category_str[:-2]
        self.help_text = 'Submit a PB run for a given category. Usage is `{0} category_name category_score vod_url`, ' \
                         'where category_name is the name of the category (e.g. `speed` or `score`); category_score ' \
                         'is the time or score you got, and vod_url is a full URL link to the vod for the run. The ' \
                         'allowed categories are: {1}.' \
                         .format(self.mention, allowed_category_str)

    @property
    def short_help_text(self) -> str:
        return 'Submit a PB run.'

    async def _do_execute(self, cmd: Command) -> None:
        if len(cmd.args) != 3:
            await cmd.channel.send(
                'Error: `{0}` requires exactly 3 arguments. Use `.help submit` for more info.'.format(self.mention)
            )
            return

        necro_user = await userlib.get_user(discord_id=cmd.author.id)   # type: NecroUser
        category_name = cmd.args[0]     # type: str
        category_score = cmd.args[1]    # type: str
        vod_url = cmd.args[2]           # type: str

        # User validity check
        if necro_user is None:
            await cmd.channel.send(
                'Error finding the User object for the command caller.'.format(self.mention)
            )
            return

        race_info = categories.get_raceinfo_for_keyword(category_name)
        if race_info is None:
            await cmd.channel.send(
                'Error: I don\'t recognize the category `{0}`. Use `.help {1}` for a list of categories.'
                .format(category_name, self.mention)
            )
            return

        converted_score = categories.convert_to_score(category_keyword=category_name, score=category_score)
        if converted_score is None:
            await cmd.channel.send(
                'Error: I wasn\'t able to interpret `{0}` as a valid time/score for the category `{1}`.'
                .format(category_score, category_name)
            )
            return

        submission_time = datetime.datetime.utcnow()

        await speedrundb.submit(
            necro_user=necro_user,
            category_race_info=race_info,
            category_score=converted_score,
            vod_url=vod_url,
            submission_time=submission_time
        )

        await NEDispatch().publish(
            event_type='submitted_run',
        )


# class GetRuns(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'verify')
#         self.help_text = 'Mark a submitted run as verified. Usage is `{0} run_id`, where `run_id` is the unique ID ' \
#                          'of the run to be verified. (Use '
#         self.admin_only = True
#
#     @property
#     def short_help_text(self) -> str:
#         return 'Mark a submitted run as verified.'
#
#     async def _do_execute(self, command: Command) -> None:
#         pass


class OverwriteSpeedrunGSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'overwrite-speedrun-sheet')
        self.help_text = "Refresh the GSheet (overwrites all data)."
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        # Get the matchup sheet
        wks_id = 0
        try:
            speedrun_sheet = await sheetlib.get_sheet(
                gsheet_id=SpeedrunMgr().gsheet_id,
                wks_id=wks_id,
                sheet_type=sheetlib.SheetType.SPEEDRUN
            )  # type: SpeedrunSheet
        except (googleapiclient.errors.Error, necrobot.exception.NecroException) as e:
            await cmd.channel.send(
                'Error accessing GSheet: `{0}`'.format(e)
            )
            return

        if speedrun_sheet is None:
            await cmd.channel.send('Error: SpeedrunSheet is None.')
            return

        await speedrun_sheet.overwrite_gsheet()


class SetSpeedrunGSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-speedrun-sheet')
        self.help_text = 'Set the GSheet for displaying submitted speedruns. Usage is `{0} gsheet_id`.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self) -> str:
        return 'Set the GSheet for displaying submitted speedruns.'

    async def _do_execute(self, cmd: Command) -> None:
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Error: `{0}` requires exactly one argument.'.format(self.mention)
            )
            return

        sheet_id = cmd.args[0]
        perm_info = await sheetutil.has_read_write_permissions(sheet_id)

        if not perm_info[0]:
            await cmd.channel.send(
                'Cannot access GSheet: {0}'.format(perm_info[1])
            )
            return

        SpeedrunMgr().gsheet_id = sheet_id
        await cmd.channel.send(
            'The speedrun GSheet for `{league_name}` has been set to "{sheet_name}". <{sheet_url}>'.format(
                league_name=LeagueMgr().league.schema_name,
                sheet_name=perm_info[1],
                sheet_url='https://docs.google.com/spreadsheets/d/{0}'.format(SpeedrunMgr().gsheet_id)
            )
        )


class Verify(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'verify')
        self.help_text = 'Mark a submitted run as verified. Usage is `{0} run_id`, where `run_id` is the unique ID ' \
                         'of the run to be verified. (See the GSheet for a list of IDs.) You may also use ' \
                         '`{0} run_id no` to un-verify a run.'
        self.admin_only = True

    @property
    def short_help_text(self) -> str:
        return 'Mark a submitted run as verified.'

    async def _do_execute(self, cmd: Command) -> None:
        if not 1 <= len(cmd.args) <= 2:
            await cmd.channel.send(
                'Error: `{0}` requires either one or two arguments.'.format(self.mention)
            )
            return

        verify = True
        if len(cmd.args) == 2:
            if cmd.args[1].lower() == 'no':
                verify = False
            else:
                await cmd.channel.send(
                    'Error: I don\'t recognize the parameter {}.'.format(cmd.args[1])
                )
                return

        run_id = cmd.args[0]
        await speedrundb.set_verified(run_id=run_id, verified=verify)

        if verify:
            confirm_text = 'Verified run with ID {}.'.format(run_id)
        else:
            confirm_text = 'Removed verification for run with ID {}.'.format(run_id)

        await cmd.channel.send(confirm_text)
