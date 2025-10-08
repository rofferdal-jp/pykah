import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import the game modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pykah.pokah_board import Board
from pykah.game_logic.game import Game
from pykah.game_logic.cards import evaluate_hand
import pydealer
from pydealer.const import POKER_RANKS


class TestHandEvaluation(unittest.TestCase):
    """Test cases for poker hand evaluation and showdown logic."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.board = Board("TestPlayer", 4, 1000, 20)
        self.game = Game(self.board)

    def create_card(self, value, suit):
        """Helper method to create a pydealer Card object."""
        return pydealer.Card(value, suit)

    def create_hand(self, cards_data):
        """Helper to create a list of cards from tuples of (value, suit)."""
        return [self.create_card(value, suit) for value, suit in cards_data]

    def test_pair_vs_pair_higher_wins(self):
        """Test that a higher pair beats a lower pair."""
        # Player 1: Pair of Kings (KK)
        # Player 2: Pair of 7s (77)
        # Community: A♠ 5♦ 3♣ 9♥ 2♠

        community_cards = self.create_hand([
            ('Ace', 'Spades'), ('5', 'Diamonds'), ('3', 'Clubs'),
            ('9', 'Hearts'), ('2', 'Spades')
        ])

        # Player with pair of Kings
        kings_hand = self.create_hand([('King', 'Hearts'), ('King', 'Clubs')]) + community_cards
        kings_score = evaluate_hand(kings_hand)

        # Player with pair of 7s
        sevens_hand = self.create_hand([('7', 'Hearts'), ('7', 'Clubs')]) + community_cards
        sevens_score = evaluate_hand(sevens_hand)

        # Kings should beat 7s
        # Note: eval7 uses lower scores for better hands, fallback uses tuples where higher is better
        try:
            import eval7
            # With eval7, lower score is better
            self.assertLess(kings_score, sevens_score,
                          f"Kings pair (score: {kings_score}) should beat 7s pair (score: {sevens_score})")
        except ImportError:
            # With fallback tuple comparison, higher tuple should be better
            self.assertGreater(kings_score, sevens_score,
                             f"Kings pair (score: {kings_score}) should beat 7s pair (score: {sevens_score})")

    def test_pair_vs_high_card(self):
        """Test that any pair beats high card."""
        community_cards = self.create_hand([
            ('5', 'Diamonds'), ('8', 'Clubs'), ('9', 'Hearts'),
            ('Jack', 'Spades'), ('Queen', 'Diamonds')
        ])

        # Player with pair of 2s
        pair_hand = self.create_hand([('2', 'Hearts'), ('2', 'Clubs')]) + community_cards
        pair_score = evaluate_hand(pair_hand)

        # Player with high card Ace
        high_card_hand = self.create_hand([('Ace', 'Hearts'), ('King', 'Clubs')]) + community_cards
        high_card_score = evaluate_hand(high_card_hand)

        try:
            import eval7
            self.assertLess(pair_score, high_card_score,
                          "Any pair should beat high card")
        except ImportError:
            self.assertGreater(pair_score, high_card_score,
                             "Any pair should beat high card")

    def test_two_pair_vs_one_pair(self):
        """Test that two pair beats one pair."""
        community_cards = self.create_hand([
            ('5', 'Diamonds'), ('8', 'Clubs'), ('King', 'Hearts'),
            ('Jack', 'Spades'), ('Queen', 'Diamonds')
        ])

        # Player with two pair (Kings and 5s)
        two_pair_hand = self.create_hand([('King', 'Spades'), ('5', 'Hearts')]) + community_cards
        two_pair_score = evaluate_hand(two_pair_hand)

        # Player with one pair (Queens)
        one_pair_hand = self.create_hand([('Queen', 'Hearts'), ('9', 'Clubs')]) + community_cards
        one_pair_score = evaluate_hand(one_pair_hand)

        try:
            import eval7
            self.assertLess(two_pair_score, one_pair_score,
                          "Two pair should beat one pair")
        except ImportError:
            self.assertGreater(two_pair_score, one_pair_score,
                             "Two pair should beat one pair")

    def test_trips_vs_two_pair(self):
        """Test that three of a kind beats two pair."""
        community_cards = self.create_hand([
            ('5', 'Diamonds'), ('5', 'Clubs'), ('King', 'Hearts'),
            ('Jack', 'Spades'), ('Queen', 'Diamonds')
        ])

        # Player with trips (three 5s)
        trips_hand = self.create_hand([('5', 'Hearts'), ('9', 'Clubs')]) + community_cards
        trips_score = evaluate_hand(trips_hand)

        # Player with two pair (Kings and Queens)
        two_pair_hand = self.create_hand([('King', 'Spades'), ('Queen', 'Hearts')]) + community_cards
        two_pair_score = evaluate_hand(two_pair_hand)

        try:
            import eval7
            self.assertLess(trips_score, two_pair_score,
                          "Three of a kind should beat two pair")
        except ImportError:
            self.assertGreater(trips_score, two_pair_score,
                             "Three of a kind should beat two pair")

    def test_straight_vs_trips(self):
        """Test that a straight beats three of a kind."""
        community_cards = self.create_hand([
            ('6', 'Diamonds'), ('7', 'Clubs'), ('8', 'Hearts'),
            ('Jack', 'Spades'), ('Jack', 'Diamonds')
        ])

        # Player with straight (5-6-7-8-9)
        straight_hand = self.create_hand([('5', 'Hearts'), ('9', 'Clubs')]) + community_cards
        straight_score = evaluate_hand(straight_hand)

        # Player with trips (three Jacks)
        trips_hand = self.create_hand([('Jack', 'Hearts'), ('2', 'Clubs')]) + community_cards
        trips_score = evaluate_hand(trips_hand)

        try:
            import eval7
            self.assertLess(straight_score, trips_score,
                          "Straight should beat three of a kind")
        except ImportError:
            self.assertGreater(straight_score, trips_score,
                             "Straight should beat three of a kind")

    def test_flush_vs_straight(self):
        """Test that a flush beats a straight."""
        community_cards = self.create_hand([
            ('6', 'Hearts'), ('7', 'Hearts'), ('8', 'Hearts'),
            ('Jack', 'Spades'), ('Queen', 'Diamonds')
        ])

        # Player with flush (5 hearts)
        flush_hand = self.create_hand([('5', 'Hearts'), ('9', 'Hearts')]) + community_cards
        flush_score = evaluate_hand(flush_hand)

        # Player with straight (5-6-7-8-9)
        straight_hand = self.create_hand([('5', 'Clubs'), ('9', 'Spades')]) + community_cards
        straight_score = evaluate_hand(straight_hand)

        try:
            import eval7
            self.assertLess(flush_score, straight_score,
                          "Flush should beat straight")
        except ImportError:
            self.assertGreater(flush_score, straight_score,
                             "Flush should beat straight")

    def test_resolve_showdown_integration(self):
        """Integration test for the complete showdown resolution."""
        # Set up a game scenario where player with Kings should beat player with 7s

        # Community cards: A♠ 5♦ 3♣ 9♥ 2♠
        self.board.community_cards = self.create_hand([
            ('Ace', 'Spades'), ('5', 'Diamonds'), ('3', 'Clubs'),
            ('9', 'Hearts'), ('2', 'Spades')
        ])

        # Player 0: Pair of Kings
        self.board.players[0].hole_cards = self.create_hand([('King', 'Hearts'), ('King', 'Clubs')])

        # Player 1: Pair of 7s
        self.board.players[1].hole_cards = self.create_hand([('7', 'Hearts'), ('7', 'Clubs')])

        # Run showdown between players 0 and 1
        winners = self.game.resolve_showdown([0, 1])

        # Player 0 (Kings) should win
        self.assertEqual(winners, [0], "Player with Kings should beat player with 7s")
        self.assertIn(0, self.board.winners)
        self.assertNotIn(1, self.board.winners)

    def test_split_pot_scenario(self):
        """Test scenario where two players tie and should split the pot."""
        # Community cards that create a tie scenario
        self.board.community_cards = self.create_hand([
            ('Ace', 'Spades'), ('King', 'Hearts'), ('Queen', 'Diamonds'),
            ('Jack', 'Clubs'), ('10', 'Spades')
        ])

        # Both players have the same straight (Broadway)
        self.board.players[0].hole_cards = self.create_hand([('9', 'Hearts'), ('8', 'Clubs')])
        self.board.players[1].hole_cards = self.create_hand([('9', 'Diamonds'), ('8', 'Spades')])

        winners = self.game.resolve_showdown([0, 1])

        # Both should win (tie)
        self.assertEqual(len(winners), 2, "Should be a tie between both players")
        self.assertIn(0, winners)
        self.assertIn(1, winners)
        self.assertTrue(self.board.is_split_pot)

    def test_evaluate_hand(self):
        community_cards = self.create_hand([
            ('Ace', 'Spades'), ('5', 'Diamonds'), ('3', 'Clubs'),
            ('9', 'Hearts'), ('2', 'Spades')
        ])

        # Higher pair should have higher score in fallback mode
        kings_hand = self.create_hand([('King', 'Hearts'), ('King', 'Clubs')]) + community_cards
        sevens_hand = self.create_hand([('7', 'Hearts'), ('7', 'Clubs')]) + community_cards

        kings_score = evaluate_hand(kings_hand)
        sevens_score = evaluate_hand(sevens_hand)

        # In fallback mode, this should be tuple comparison
        self.assertIsInstance(kings_score, tuple)
        self.assertIsInstance(sevens_score, tuple)

    def test_same_pair_different_kickers(self):
        """Test that when pairs are the same, kickers determine the winner."""
        community_cards = self.create_hand([
            ('2', 'Spades'), ('3', 'Diamonds'), ('4', 'Clubs'),
            ('9', 'Hearts'), ('10', 'Spades')  # No straight possible
        ])

        # Both players have pair of 8s, but different kickers
        # Player 1: 8s with Ace kicker
        eights_ace_hand = self.create_hand([('8', 'Hearts'), ('Ace', 'Clubs')]) + community_cards
        eights_ace_score = evaluate_hand(eights_ace_hand)

        # Player 2: 8s with King kicker
        eights_king_hand = self.create_hand([('8', 'Spades'), ('King', 'Diamonds')]) + community_cards
        eights_king_score = evaluate_hand(eights_king_hand)

        try:
            import eval7
            self.assertLess(eights_ace_score, eights_king_score,
                          "Pair of 8s with Ace kicker should beat pair of 8s with King kicker")
        except ImportError:
            self.assertGreater(eights_ace_score, eights_king_score,
                             "Pair of 8s with Ace kicker should beat pair of 8s with King kicker")

    def test_pocket_pairs_different_ranks(self):
        """Test various pocket pairs against each other."""
        community_cards = self.create_hand([
            ('2', 'Spades'), ('4', 'Diamonds'), ('6', 'Clubs'),
            ('8', 'Hearts'), ('10', 'Spades')  # No pairs, straights, or flushes on board
        ])

        test_pairs = [
            (('Jack', 'Hearts'), ('Jack', 'Clubs')),  # Jacks
            (('7', 'Hearts'), ('7', 'Clubs')),        # 7s
            (('Ace', 'Hearts'), ('Ace', 'Clubs')),    # Aces
            (('3', 'Hearts'), ('3', 'Clubs')),        # 3s
        ]

        scores = []
        for hole_cards in test_pairs:
            hand = self.create_hand([hole_cards[0], hole_cards[1]]) + community_cards
            score = evaluate_hand(hand)
            scores.append((hole_cards, score))

        # Aces should be best, then Jacks, then 7s, then 3s
        try:
            import eval7
            # Lower scores are better with eval7
            scores.sort(key=lambda x: x[1])
            self.assertEqual(scores[0][0][0][0], 'Ace')  # Aces should be first (best)
            self.assertEqual(scores[-1][0][0][0], '3')  # 3s should be last (worst)
        except ImportError:
            # Higher scores are better with fallback
            scores.sort(key=lambda x: x[1], reverse=True)
            self.assertEqual(scores[0][0][0][0], 'Ace')  # Aces should be first (best)
            self.assertEqual(scores[-1][0][0][0], '3')  # 3s should be last (worst)

    def test_high_card_vs_high_card_kickers(self):
        """Test high card hands with different kickers."""
        community_cards = self.create_hand([
            ('2', 'Spades'), ('4', 'Diamonds'), ('6', 'Clubs'),
            ('8', 'Hearts'), ('10', 'Spades')
        ])

        # Player 1: Ace high
        ace_high_hand = self.create_hand([('Ace', 'Hearts'), ('Jack', 'Clubs')]) + community_cards
        ace_high_score = evaluate_hand(ace_high_hand)

        # Player 2: King high
        king_high_hand = self.create_hand([('King', 'Hearts'), ('Queen', 'Clubs')]) + community_cards
        king_high_score = evaluate_hand(king_high_hand)

        try:
            import eval7
            self.assertLess(ace_high_score, king_high_score,
                          "Ace high should beat King high")
        except ImportError:
            self.assertGreater(ace_high_score, king_high_score,
                             "Ace high should beat King high")

    def test_showdown_with_three_players(self):
        """Test showdown resolution with three players."""
        # Set up community cards
        self.board.community_cards = self.create_hand([
            ('5', 'Diamonds'), ('8', 'Clubs'), ('9', 'Hearts'),
            ('Jack', 'Spades'), ('Queen', 'Diamonds')
        ])

        # Player 0: Pair of Queens (strongest)
        self.board.players[0].hole_cards = self.create_hand([('Queen', 'Hearts'), ('2', 'Clubs')])

        # Player 1: Pair of 8s (middle)
        self.board.players[1].hole_cards = self.create_hand([('8', 'Hearts'), ('7', 'Clubs')])

        # Player 2: High card Ace (weakest)
        self.board.players[2].hole_cards = self.create_hand([('Ace', 'Hearts'), ('King', 'Clubs')])

        winners = self.game.resolve_showdown([0, 1, 2])

        # Player 0 with pair of Queens should win
        self.assertEqual(winners, [0], "Player with pair of Queens should win")
        self.assertIn(0, self.board.winners)
        self.assertNotIn(1, self.board.winners)
        self.assertNotIn(2, self.board.winners)

    def test_complex_tie_scenario(self):
        """Test a complex tie scenario with identical hands."""
        # Community cards that create identical best hands
        self.board.community_cards = self.create_hand([
            ('Ace', 'Spades'), ('Ace', 'Hearts'), ('King', 'Diamonds'),
            ('King', 'Clubs'), ('Queen', 'Spades')
        ])

        # Both players play the board (two pair Aces and Kings)
        self.board.players[0].hole_cards = self.create_hand([('2', 'Hearts'), ('3', 'Clubs')])
        self.board.players[1].hole_cards = self.create_hand([('4', 'Diamonds'), ('5', 'Spades')])

        winners = self.game.resolve_showdown([0, 1])

        # Should be a tie
        self.assertEqual(len(winners), 2, "Should be a tie")
        self.assertIn(0, winners)
        self.assertIn(1, winners)
        self.assertTrue(self.board.is_split_pot)

    def test_full_house_vs_flush(self):
        """Test that full house beats flush."""
        community_cards = self.create_hand([
            ('7', 'Hearts'), ('7', 'Spades'), ('King', 'Hearts'),
            ('2', 'Hearts'), ('3', 'Hearts')  # Changed to avoid straight flush
        ])

        # Player with full house (7s full of Kings)
        full_house_hand = self.create_hand([('7', 'Clubs'), ('King', 'Spades')]) + community_cards
        full_house_score = evaluate_hand(full_house_hand)

        # Player with flush (hearts) - use 4H instead of 10H to avoid straight flush
        flush_hand = self.create_hand([('4', 'Hearts'), ('9', 'Hearts')]) + community_cards
        flush_score = evaluate_hand(flush_hand)

        try:
            import eval7
            self.assertLess(full_house_score, flush_score,
                          "Full house should beat flush")
        except ImportError:
            self.assertGreater(full_house_score, flush_score,
                             "Full house should beat flush")

    def test_quads_vs_full_house(self):
        """Test that four of a kind beats full house."""
        community_cards = self.create_hand([
            ('7', 'Hearts'), ('7', 'Spades'), ('7', 'Clubs'),
            ('King', 'Hearts'), ('King', 'Spades')
        ])

        # Player with quads (four 7s)
        quads_hand = self.create_hand([('7', 'Diamonds'), ('2', 'Clubs')]) + community_cards
        quads_score = evaluate_hand(quads_hand)

        # Player with full house (Kings full of 7s)
        full_house_hand = self.create_hand([('King', 'Clubs'), ('Queen', 'Diamonds')]) + community_cards
        full_house_score = evaluate_hand(full_house_hand)

        try:
            import eval7
            self.assertLess(quads_score, full_house_score,
                          "Four of a kind should beat full house")
        except ImportError:
            self.assertGreater(quads_score, full_house_score,
                             "Four of a kind should beat full house")

    def test_wheel_straight(self):
        """Test the wheel straight (A-2-3-4-5)."""
        community_cards = self.create_hand([
            ('2', 'Hearts'), ('3', 'Spades'), ('4', 'Clubs'),
            ('King', 'Hearts'), ('Queen', 'Spades')
        ])

        # Player with wheel straight
        wheel_hand = self.create_hand([('Ace', 'Hearts'), ('5', 'Diamonds')]) + community_cards
        wheel_score = evaluate_hand(wheel_hand)

        # Player with pair of Kings
        pair_hand = self.create_hand([('King', 'Spades'), ('Jack', 'Diamonds')]) + community_cards
        pair_score = evaluate_hand(pair_hand)

        try:
            import eval7
            self.assertLess(wheel_score, pair_score,
                          "Wheel straight should beat pair")
        except ImportError:
            self.assertGreater(wheel_score, pair_score,
                             "Wheel straight should beat pair")

    def test_pot_distribution_in_split(self):
        """Test that pot is correctly split among winners."""
        # Set up a scenario where two players tie
        self.board.pot = 100
        initial_chips_0 = self.board.players[0].chip_stack
        initial_chips_1 = self.board.players[1].chip_stack

        # Community cards that create a tie
        self.board.community_cards = self.create_hand([
            ('Ace', 'Spades'), ('King', 'Hearts'), ('Queen', 'Diamonds'),
            ('Jack', 'Clubs'), ('10', 'Spades')
        ])

        # Both players have the same straight
        self.board.players[0].hole_cards = self.create_hand([('9', 'Hearts'), ('8', 'Clubs')])
        self.board.players[1].hole_cards = self.create_hand([('9', 'Diamonds'), ('8', 'Spades')])

        winners = self.game.resolve_showdown([0, 1])

        # Check pot distribution
        self.assertEqual(len(winners), 2)
        self.assertEqual(self.board.players[0].chip_stack, initial_chips_0 + 50)
        self.assertEqual(self.board.players[1].chip_stack, initial_chips_1 + 50)
        self.assertEqual(self.board.pot, 0)

    def test_showdown_mode_activation(self):
        """Test that showdown mode is correctly activated."""
        self.assertFalse(self.board.showdown_mode)

        # Set up a simple showdown
        self.board.community_cards = self.create_hand([
            ('2', 'Spades'), ('3', 'Diamonds'), ('4', 'Clubs'),
            ('5', 'Hearts'), ('6', 'Spades')
        ])

        self.board.players[0].hole_cards = self.create_hand([('Ace', 'Hearts'), ('King', 'Clubs')])
        self.board.players[1].hole_cards = self.create_hand([('7', 'Hearts'), ('8', 'Clubs')])

        winners = self.game.resolve_showdown([0, 1])

        # Showdown mode should be activated
        self.assertTrue(self.board.showdown_mode)
        self.assertEqual(self.board.showdown_players, [0, 1])


if __name__ == '__main__':
    unittest.main()
