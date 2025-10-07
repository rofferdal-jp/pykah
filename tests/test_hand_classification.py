import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pykah.pokah_board import Board
from pykah.game import Game
import pydealer


def make_card(value, suit):
    return pydealer.Card(value, suit)


class TestHandClassification(unittest.TestCase):
    def setUp(self):
        self.board = Board('Tester', 2, 1000, 10)
        # Make both players AI for headless tests
        for p in self.board.players:
            p.is_human = False
        self.game = Game(self.board)

    def run_and_get_hand_type(self, community, hole0, hole1):
        # assign
        self.board.community_cards = [make_card(v, s) for v, s in community]
        self.board.players[0].hole_cards = [make_card(v, s) for v, s in hole0]
        self.board.players[1].hole_cards = [make_card(v, s) for v, s in hole1]
        winners = self.game.resolve_showdown([0, 1])
        return self.board.winning_hand_type, winners

    def test_high_card(self):
        community = [( '2','Hearts'), ('7','Clubs'), ('9','Diamonds'), ('Jack','Spades'), ('3','Hearts')]
        hole0 = [('Ace','Hearts'), ('4','Clubs')]
        hole1 = [('King','Clubs'), ('5','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        self.assertEqual(hand, 'High Card')
        self.assertIn(0, winners)

    def test_pair(self):
        community = [('2','Hearts'), ('7','Clubs'), ('9','Diamonds'), ('Jack','Spades'), ('3','Hearts')]
        hole0 = [('Ace','Hearts'), ('2','Clubs')]  # pair of 2s
        hole1 = [('King','Clubs'), ('5','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        self.assertEqual(hand, 'Pair')
        self.assertIn(0, winners)

    def test_two_pair(self):
        community = [('2','Hearts'), ('7','Clubs'), ('9','Diamonds'), ('7','Spades'), ('3','Hearts')]
        hole0 = [('2','Clubs'), ('9','Clubs')]  # two pair: 2s and 9s
        hole1 = [('King','Clubs'), ('5','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        self.assertEqual(hand, 'Two Pair')
        self.assertIn(0, winners)

    def test_trips(self):
        community = [('2','Hearts'), ('2','Diamonds'), ('9','Diamonds'), ('7','Spades'), ('3','Hearts')]
        hole0 = [('2','Clubs'), ('Ace','Clubs')]  # trips of 2s
        hole1 = [('King','Clubs'), ('5','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        self.assertEqual(hand, 'Three of a Kind')
        self.assertIn(0, winners)

    def test_straight(self):
        # community: 5,6,7,8 and hole gives 9 to complete 5-9 straight
        community = [('5','Hearts'), ('6','Clubs'), ('7','Diamonds'), ('King','Spades'), ('2','Hearts')]
        hole0 = [('8','Hearts'), ('9','Clubs')]  # straight 5-9
        hole1 = [('Ace','Clubs'), ('3','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        self.assertEqual(hand, 'Straight')
        self.assertIn(0, winners)

    def test_flush(self):
        community = [('2','Hearts'), ('6','Hearts'), ('9','Hearts'), ('King','Spades'), ('3','Clubs')]
        hole0 = [('Ace','Hearts'), ('4','Hearts')]  # flush in hearts
        hole1 = [('King','Clubs'), ('5','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        self.assertEqual(hand, 'Flush')
        self.assertIn(0, winners)

    def test_full_house(self):
        community = [('2','Hearts'), ('2','Clubs'), ('9','Diamonds'), ('9','Spades'), ('3','Hearts')]
        hole0 = [('2','Diamonds'), ('Ace','Clubs')]  # full house 2s full of 9s
        hole1 = [('King','Clubs'), ('5','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        # Note: _evaluate_poker_hand_fallback should see full house
        self.assertEqual(hand, 'Full House')
        self.assertIn(0, winners)

    def test_quads(self):
        community = [('2','Hearts'), ('2','Clubs'), ('2','Diamonds'), ('King','Spades'), ('3','Hearts')]
        hole0 = [('2','Spades'), ('Ace','Clubs')]  # four 2s
        hole1 = [('King','Clubs'), ('5','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        self.assertEqual(hand, 'Four of a Kind')
        self.assertIn(0, winners)

    def test_straight_flush(self):
        # community has 6,7,8 of clubs and hole gives 9 and 5 of clubs for straight flush 5-9
        community = [('6','Clubs'), ('7','Clubs'), ('8','Clubs'), ('King','Spades'), ('2','Hearts')]
        hole0 = [('5','Clubs'), ('9','Clubs')]  # straight flush 5-9 clubs
        hole1 = [('Ace','Clubs'), ('3','Diamonds')]
        hand, winners = self.run_and_get_hand_type(community, hole0, hole1)
        self.assertEqual(hand, 'Straight Flush')
        self.assertIn(0, winners)


if __name__ == '__main__':
    unittest.main(verbosity=2)

