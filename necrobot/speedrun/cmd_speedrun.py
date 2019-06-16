from necrobot.user import userlib

from necrobot.speedrun import categories, speedrundb

from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
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

    async def _do_execute(self, command: Command) -> None:
        if len(command.args) != 3:
            await command.channel.send(
                'Error: `{0}` requires exactly 3 arguments. Use `.help submit` for more info.'.format(self.mention)
            )
            return

        necro_user = await userlib.get_user(discord_id=command.author.id)   # type: NecroUser
        category_name = command.args[0]     # type: str
        category_score = command.args[1]    # type: str
        vod_url = command.args[2]           # type: str

        # User validity check
        if necro_user is None:
            await command.channel.send(
                'Error finding the User object for the command caller.'.format(self.mention)
            )
            return

        race_info = categories.get_raceinfo_for_keyword(category_name)
        if race_info is None:
            await command.channel.send(
                'Error: I don\'t recognize the category `{0}`. Use `.help {1}` for a list of categories.'
                .format(category_name, self.mention)
            )
            return

        converted_score = categories.convert_to_score(category_keyword=category_name, score=category_score)
        if converted_score is None:
            await command.channel.send(
                'Error: I wasn\'t able to interpret `{0}` as a valid time/score for the category `{1}`.'
                .format(category_score, category_name)
            )
            return

        await speedrundb.submit(
            necro_user=necro_user,
            category_race_info=race_info,
            category_score=converted_score,
            vod_url=vod_url
        )
