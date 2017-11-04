from typing import Dict, List, Tuple

from necrobot.automatch import ilpmatch, automatchutil
from necrobot.database import leaguedb
from necrobot.ladder import ratingutil
from necrobot.match import cmd_match, matchutil
from necrobot.user import userlib

from necrobot.config import Config
from necrobot.botbase.commandtype import CommandType
from necrobot.match.matchinfo import MatchInfo
from necrobot.ladder.rating import Rating
from necrobot.league.leaguemgr import LeagueMgr


MAX_LEADERBOARD_RANK = 20


# General commands
class LadderDrop(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dropcurrent')
        self.help_text = 'Drop out of all currently scheduled ladder matches.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class LadderRegister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register')
        self.help_text = 'Register yourself for the Necrobot ladder.'

    async def _do_execute(self, cmd):
        user = await userlib.get_user(discord_id=int(cmd.author.id))

        if await leaguedb.is_registered(user.user_id):
            await self.client.send_message(
                cmd.channel,
                '{0}: You are already registered for the ladder.'.format(cmd.author.mention)
            )
        else:
            await leaguedb.register_user(user.user_id)
            await self.client.send_message(
                cmd.channel,
                '{0} has registered for the ladder. '.format(cmd.author.mention)
            )


class LadderUnregister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unregister')
        self.help_text = 'Unregister for the ladder.'

    async def _do_execute(self, cmd):
        user = await userlib.get_user(discord_id=int(cmd.author.id))

        if await leaguedb.is_registered(user.user_id):
            await leaguedb.unregister_user(user.user_id)
            await self.client.send_message(
                cmd.channel,
                '{0}: You are no longer registered for the ladder.'.format(cmd.author.mention)
            )
        else:
            await self.client.send_message(
                cmd.channel,
                '{0}: You are not registered for the ladder.'.format(cmd.author.mention)
            )


class SetAutomatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setautomatch')
        self.help_text = '`{0} n`: Tells the bot you want `n` automatches per week. (`n` must be between 0 and {1}.)'\
                         .format(self.mention, Config.AUTOMATCH_MAX_MATCHES)

    async def _do_execute(self, cmd):
        user = await userlib.get_user(discord_id=int(cmd.author.id))

        if not await leaguedb.is_registered(user.user_id):
            await self.client.send_message(
                cmd.channel,
                '{0}: You are not registered for the ladder. Please register with `.register`.'
                .format(cmd.author.mention)
            )
            return

        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`. Please specify a number of races per week.'.format(self.mention)
            )
            return

        try:
            num_matches = int(cmd.args[0])
        except ValueError:
            await self.client.send_message(
                cmd.channel,
                'Error: Could\'t parse {0} as a number.'.format(cmd.args[0])
            )
            return

        if not (0 <= num_matches <= Config.AUTOMATCH_MAX_MATCHES):
            await self.client.send_message(
                cmd.channel,
                'Error: Number of automatches per week must be between 0 and {0}.'.format(Config.AUTOMATCH_MAX_MATCHES)
            )
            return

        await leaguedb.set_automatches(user.user_id, num_matches)
        await self.client.send_message(
            cmd.channel,
            '{auth}: You\'re now requesting {num} {matches} per week.'
            .format(
                auth=cmd.author.mention,
                num=num_matches,
                matches='match' if num_matches == 1 else 'matches'
            )
        )


class Ranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ranked')
        self.help_text = 'Create a ranked ladder match (`{0} opponent_name`).'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Create ranked ladder match.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`. '
                '(Enclose racer names with spaces inside quotes.)'.format(self.mention)
            )
            return

        await cmd_match.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_members=[cmd.author],
            racer_names=[cmd.args[0]],
            match_info=MatchInfo(ranked=True)
        )


class GetRating(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'rating')
        self.help_text = '`{} username` returns the rating of the discord user `username` (or your own by default).'\
                         .format(self.mention)

    @property
    def short_help_text(self):
        return 'Get ladder rating.'

    async def _do_execute(self, cmd):
        if len(cmd.args) == 0:
            user = await userlib.get_user(discord_id=int(cmd.author.id))
        elif len(cmd.args) == 1:
            user = await userlib.get_user(any_name=cmd.args[0])
            if user is None:
                await self.client.send_message(
                    cmd.channel,
                    'Couldn\'t find user {0}.'.format(cmd.args[0])
                )
                return
        else:
            await self.client.send_message(
                cmd.channel,
                'Error: Too many args for `{0}`. (Enclose names with spaces in quotes.)'.format(self.mention)
            )
            return

        rating = await leaguedb.get_rating(user_id=user.user_id)
        if rating is not None:
            await self.client.send_message(
                cmd.channel,
                '**{0}**: {1}'.format(user.display_name, rating.displayed_rating))
        else:
            await self.client.send_message(
                cmd.channel,
                '**{0}**: Unrated.'.format(user.display_name))


class Unranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unranked')
        self.help_text = 'Create an unranked ladder match (`{0} opponent_name`).'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Create unranked match.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`. '
                '(Enclose racer names with spaces inside quotes.)'.format(self.mention)
            )
            return

        await cmd_match.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_members=[cmd.author],
            racer_names=[cmd.args[0]],
            match_info=MatchInfo(ranked=False)
        )


class Leaderboard(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'leaderboard')
        self.help_text = 'View the ladder leaderboard.'.format(self.mention)

    async def _do_execute(self, cmd):
        leaderboard = await leaguedb.get_ratings()
        leaderboard_list = \
            sorted(
                list(leaderboard.items()),
                key=lambda x: x[1].displayed_rating,
                reverse=True
            )    # type: List[Tuple[int, Rating]]
        leaderboard_list = leaderboard_list[:MAX_LEADERBOARD_RANK]
        leaderboard_entry_fmt = '{rank}. {name:>{name_width}}: {rating}\n'
        msg = '```\n'

        named_leaderboards = []     # type: List[Tuple[str, Rating]]
        name_width = 0
        for entry in leaderboard_list:
            user = await userlib.get_user(user_id=entry[0])
            name_width = max(name_width, len(user.display_name))
            named_leaderboards.append((user.display_name, entry[1]))

        rank = 0
        for entry in named_leaderboards:
            rank += 1
            msg += leaderboard_entry_fmt.format(
                rank=rank,
                name=entry[0],
                rating=entry[1].displayed_rating,
                name_width=name_width
            )

        msg += '```'
        await self.client.send_message(cmd.channel, msg)


# Admin commands
class Automatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'automatch')
        self.help_text = 'Make automated ladder matches.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        # Get ratings and number of desired automatches
        ratings = await leaguedb.get_ratings(require_registered=True)           # type: Dict[int, Rating]
        num_automatches = await leaguedb.get_automatches(require_registered=True)   # type: Dict[int, int]

        # Compute costs and cost multipliers
        costs = dict()              # type: Dict[Tuple[int, int], float]
        cost_multipliers = dict()   # type: Dict[int, float]
        for player1, rating in ratings.items():
            # Compute cost multiplier for this player
            cost_multipliers[player1] = await automatchutil.get_cost_multiplier(player1)

            # Compute costs of matchups against higher-id players
            for player2 in ratings.keys():
                if player1 < player2:
                    costs[(player1, player2)] = await automatchutil.get_cost(player1, player2)

        # Get the matchups (as a List[Tuple[int, int]])
        matches_by_id = ilpmatch.get_matchups(
            ratings=ratings,
            max_matches=num_automatches,
            costs=costs,
            cost_multipliers=cost_multipliers
        )

        # Create the matchups as Match objects
        match_info = LeagueMgr().league.match_info
        match_info.ranked = True
        matches = []
        for match_by_id in matches_by_id:
            match = await matchutil.make_match(
                racer_1_id=match_by_id[0],
                racer_2_id=match_by_id[1],
                match_info=match_info,
                register=False
            )
            matches.append(match)

        # Sort the matchup list
        matches = sorted(matches, key=lambda m: m.matchroom_name)

        # Create channels for the matches
        for match in matches:
            new_room = await matchutil.make_match_room(match=match, register=True)
            await new_room.send_channel_start_text()

        # Report what we've done
        await self.client.send_message(
            cmd.channel,
            'Matches created.'.format(self.mention)
        )


class CloseFinished(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'closefinished')
        self.help_text = 'Close all finished match rooms.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class DropRacer(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dropracer')
        self.help_text = 'Drop a racer from all their current matches. ' \
                         'Usage is `{0} rtmp_name`.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Drop a racer from current races.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class ForceRanked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-ranked')
        self.help_text = 'Create a ranked ladder match between two racers with ' \
                         '`{0} racer_1_name racer_2_name`.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Create ranked ladder match.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) != 2:
            await self.client.send_message(
                cmd.channel,
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        await cmd_match.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_names=[cmd.args[0], cmd.args[1]],
            match_info=MatchInfo(ranked=True)
        )


class ComputeRatings(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'compute-ratings')
        self.help_text = "Recompute all ratings."

    async def _do_execute(self, cmd):
        ratings = await ratingutil.compute_ratings()  # type: Dict[int, Rating]
        await leaguedb.set_ratings(ratings)

        await self.client.send_message(cmd.channel, 'Ratings recomputed.')
