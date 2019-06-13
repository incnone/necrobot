from necrobot.user import userlib

from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.user.necrouser import NecroUser


class Submit(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'submit')
        self.help_text = 'Submit a PB run for a given category. Usage is `{0} category_name category_score vod_url`, ' \
                         'where category_name is the name of the category (e.g. `speed` or `score`); category_score ' \
                         'is the time or score you got, and vod_url is a full URL link to the vod for the run.' \
                         .format(self.mention)

    @property
    def short_help_text(self) -> str:
        return 'Submit a PB run.'

    async def _do_execute(self, command: Command) -> None:
        if len(command.args) != 3:
            await command.channel.send(
                'Error: `{0}` requires exactly 3 arguments. Use `.help submit` for more info.'.format(self.mention)
            )

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

        # TODO convert category_name to a RaceInfo object
        # TODO convert score appropriately depending on category
        # speedrundb.submit(necro_user, category_race_info, category_score, vod_url)
