import unittest
from base import WholeHistoryRating
from exception import UnstableRatingException


class WHRTest(unittest.TestCase):
    whr = None

    def setUp(self):
        self.whr = WholeHistoryRating(w=50.0, prior_stdev=300.0)

    def setup_game_with_elo(self, white_elo, black_elo):
        game = self.whr.create_game('black', 'white', 'W', 1)
        game.black_player.player_days[0].elo = black_elo
        game.white_player.player_days[0].elo = white_elo
        return game

    def test_even_game_between_equal_strength_players_should_have_white_winrate_of_50_percent(self):
        game = self.setup_game_with_elo(500, 500)
        self.assertAlmostEqual(game.white_win_probability, 0.5)

    def test_higher_rank_should_confer_advantage(self):
        game = self.setup_game_with_elo(600, 500)
        self.assertTrue(game.white_win_probability > 0.5)

    def test_winrates_are_equal_for_same_elo_delta(self):
        game = self.setup_game_with_elo(100, 200)
        game2 = self.setup_game_with_elo(200, 300)
        self.assertAlmostEqual(game.white_win_probability, game2.white_win_probability)

    def test_winrates_for_twice_as_strong_player(self):
        game = self.setup_game_with_elo(100, 200)
        self.assertAlmostEqual(0.359935, game.white_win_probability)

    def test_winrates_should_be_inversely_proportional_with_unequal_ranks(self):
        game = self.setup_game_with_elo(600, 500)
        self.assertAlmostEqual(game.white_win_probability, 1 - game.black_win_probability)

    def test_output(self):
        self.whr.create_game("shusaku", "shusai", "B", 1, 0)
        self.whr.create_game("shusaku", "shusai", "W", 2, 0)
        self.whr.create_game("shusaku", "shusai", "W", 3, 0)
        self.whr.create_game("shusaku", "shusai", "W", 4, 0)
        self.whr.create_game("shusaku", "shusai", "W", 4, 0)
        self.whr.iterate(50)

        shusaku_ratings = [(a, int(round(b)), int(round(c)),) for a, b, c in self.whr.ratings_for_player('shusaku')]
        shusai_ratings = [(a, int(round(b)), int(round(c)),) for a, b, c in self.whr.ratings_for_player('shusai')]
        self.assertEqual(
            [(1, -86, 161), (2, -98, 160), (3, -108, 161), (4, -114, 164)],
            shusaku_ratings
        )
        self.assertEqual(
            [(1, 86, 161), (2, 98, 160), (3, 108, 161), (4, 114, 164)],
            shusai_ratings
        )

    def test_unstable_exception_raised_in_certain_cases(self):
        for _ in range(10):
            self.whr.create_game("anchor", "player", "B", 1, 0)
            self.whr.create_game("anchor", "player", "W", 1, 0)

        for _ in range(10):
            self.whr.create_game("anchor", "player", "B", 180, 600)
            self.whr.create_game("anchor", "player", "W", 180, 600)

        self.assertRaises(UnstableRatingException, self.whr.iterate, 10)
