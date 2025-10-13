import unittest
from game_logic.game import Game
from game_logic.player import Player

class TestGameAndPlayer(unittest.TestCase):
    def test_game_initialization(self):
        num_players = 4
        initial_chip_stack = 1500
        big_blind = 50
        human_name = "Alice"
        game = Game(num_players, initial_chip_stack, big_blind, human_name)
        self.assertEqual(game.num_players, num_players)
        self.assertEqual(game.initial_chip_stack, initial_chip_stack)
        self.assertEqual(game.big_blind, big_blind)
        self.assertEqual(game.small_blind, 25)
        self.assertEqual(game.total_chips, 6000)
        self.assertEqual(len(game.players), num_players)
        # First player is human
        self.assertTrue(game.players[0].is_human)
        self.assertEqual(game.players[0].name, human_name)
        self.assertEqual(game.players[0].chip_stack, initial_chip_stack)
        self.assertEqual(game.players[0].position, 0)
        # Rest are CPU
        for i, player in enumerate(game.players[1:], 1):
            self.assertFalse(player.is_human)
            self.assertEqual(player.name, f"CPU_{i}")
            self.assertEqual(player.chip_stack, initial_chip_stack)
            self.assertEqual(player.position, i)
            self.assertEqual(player.hole_cards, [])

if __name__ == "__main__":
    unittest.main()

