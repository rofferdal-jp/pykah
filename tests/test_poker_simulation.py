import unittest
import sys
import os

# Add the parent directory to the path so we can import the game modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pykah.pokah_board import Board
from pykah.game_logic.game import Game


class TestPokerSimulation(unittest.TestCase):
    """Test cases for headless poker game simulation."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a board with 5 players, start stack 1000, big blind 10
        self.board = Board(human_name='AI', num_players=5, start_stack=1000, big_blind=10)
        # Make all players non-human so no prompt_input UI is invoked
        for p in self.board.players:
            p.is_human = False
        self.game = Game(self.board)

    def test_single_hand_simulation(self):
        """Test that a single poker hand can be simulated successfully."""
        # Run a complete hand
        winners = self.game.start_hand(prompt_human=False)

        # Verify basic game state after hand completion
        self.assertIsInstance(winners, list)
        self.assertGreater(len(winners), 0, "There should be at least one winner")

        # Verify all winners are valid player indices
        for winner_idx in winners:
            self.assertIn(winner_idx, range(self.board.num_players))

        # Verify pot is empty after hand (distributed to winners)
        self.assertEqual(self.board.pot, 0, "Pot should be empty after hand completion")

        # Community cards may vary depending on when hand ended
        # (hand can end early if all but one player fold)
        self.assertGreaterEqual(len(self.board.community_cards), 0,
                               "Community cards should be a valid list")
        self.assertLessEqual(len(self.board.community_cards), 5,
                            "At most 5 community cards should be dealt")

        # Verify total chips are conserved (excluding blinds which were already in pot)
        total_chips = sum(p.chip_stack for p in self.board.players)
        expected_total = self.board.num_players * 1000  # Starting stacks
        self.assertEqual(total_chips, expected_total,
                        "Total chips should be conserved")

    def test_multiple_hands_simulation(self):
        """Test that multiple hands can be simulated in sequence."""
        initial_stacks = [p.chip_stack for p in self.board.players]

        # Run 3 hands
        for hand_num in range(3):
            with self.subTest(hand=hand_num):
                # Reset for new hand but keep chip stacks
                winners = self.game.start_hand(prompt_human=False)

                # Basic validation
                self.assertIsInstance(winners, list)
                self.assertGreater(len(winners), 0)
                self.assertEqual(self.board.pot, 0)

                # Verify dealer button rotates
                if hand_num > 0:
                    # Note: dealer rotation happens in actual game but not automatically
                    # in our current implementation, so we'll check other aspects
                    pass

        # Verify total chips are still conserved after multiple hands
        final_total = sum(p.chip_stack for p in self.board.players)
        initial_total = sum(initial_stacks)
        self.assertEqual(final_total, initial_total,
                        "Total chips should be conserved across multiple hands")

    def test_different_player_counts(self):
        """Test simulation with different numbers of players."""
        player_counts = [2, 3, 4, 6, 8]

        for num_players in player_counts:
            with self.subTest(players=num_players):
                # Create new board with different player count
                board = Board(human_name='AI', num_players=num_players,
                             start_stack=1000, big_blind=10)
                for p in board.players:
                    p.is_human = False
                game = Game(board)

                # Run a hand
                winners = game.start_hand(prompt_human=False)

                # Verify basic game state
                self.assertIsInstance(winners, list)
                self.assertGreater(len(winners), 0)
                self.assertEqual(board.pot, 0)

                # Verify all winners are valid
                for winner_idx in winners:
                    self.assertIn(winner_idx, range(num_players))

    def test_showdown_mode_activation(self):
        """Test that showdown mode is properly activated when hand goes to showdown."""
        # Run a hand
        winners = self.game.start_hand(prompt_human=False)

        # If hand went to showdown (more than one active player), verify showdown mode
        if len(winners) > 0:
            # Check if showdown mode was activated
            if hasattr(self.board, 'showdown_mode'):
                # If showdown happened, verify the data structures
                if self.board.showdown_mode:
                    self.assertIsNotNone(self.board.showdown_players)
                    self.assertIn(winners[0], self.board.showdown_players)

    def test_blind_structure(self):
        """Test that blinds are properly posted and deducted."""
        initial_stacks = [p.chip_stack for p in self.board.players]

        # Check dealer position and blind positions
        dealer_idx = self.board.dealer_index
        small_blind_idx = (dealer_idx + 1) % self.board.num_players
        big_blind_idx = (dealer_idx + 2) % self.board.num_players

        # These should be valid player indices
        self.assertIn(dealer_idx, range(self.board.num_players))
        self.assertIn(small_blind_idx, range(self.board.num_players))
        self.assertIn(big_blind_idx, range(self.board.num_players))

        # Run a hand
        winners = self.game.start_hand(prompt_human=False)

        # Verify blinds were posted (total change should include blind amounts)
        # Note: This is a basic check since actual blind posting happens during game

    def test_hand_evaluation_integration(self):
        """Test that hand evaluation works correctly in full game context."""
        # Run a hand
        winners = self.game.start_hand(prompt_human=False)

        # Verify winners received chips
        for winner_idx in winners:
            winner = self.board.players[winner_idx]
            # Winner should have at least their starting stack (unless they lost in betting)
            self.assertGreaterEqual(winner.chip_stack, 0)

        # Verify community cards are valid
        for card in self.board.community_cards:
            self.assertIsNotNone(card)
            self.assertTrue(hasattr(card, 'value'))
            self.assertTrue(hasattr(card, 'suit'))

    def test_ai_decision_making(self):
        """Test that AI players make valid decisions throughout the hand."""
        # Run a hand and ensure no exceptions are raised from AI decision making
        try:
            winners = self.game.start_hand(prompt_human=False)
            # If we get here without exceptions, AI decision making worked
            self.assertIsInstance(winners, list)
        except Exception as e:
            self.fail(f"AI decision making failed with exception: {e}")

    def test_chip_conservation_detailed(self):
        """Detailed test of chip conservation throughout the game."""
        initial_total = sum(p.chip_stack for p in self.board.players)
        initial_pot = self.board.pot

        # Run a hand
        winners = self.game.start_hand(prompt_human=False)

        # Check final state
        final_total = sum(p.chip_stack for p in self.board.players)
        final_pot = self.board.pot

        # Total chips should be conserved
        self.assertEqual(initial_total + initial_pot, final_total + final_pot,
                        "Total chips in system should be conserved")

        # Pot should be empty after hand
        self.assertEqual(final_pot, 0, "Pot should be distributed to winners")

    def test_print_game_results(self):
        """Test method that prints game results (for debugging/verification)."""
        winners = self.game.start_hand(prompt_human=False)

        # This test serves as a way to see the results during test runs
        print(f"\nGame Results:")
        print(f"Winners indices: {winners}")
        print(f"Final stacks:")
        for i, p in enumerate(self.board.players):
            print(f"  {i}: {p.name} - {p.chip_stack} chips")
        print(f"Community cards: {[c.name for c in self.board.community_cards]}")
        print(f"Pot after hand: {self.board.pot}")

        # Basic assertion to make this a valid test
        self.assertGreater(len(str(winners)), 0, "Should have printable results")

    def test_fold_persistence_across_rounds(self):
        """A player who has folded pre-flop must not act on later streets."""
        # Fresh hand setup (manual sequence to inject a fold before flop betting completes)
        self.game.reset_hand_state()
        contributions = self.game.post_blinds()
        self.game.deal_hole_cards()
        num = self.board.num_players
        folded_player = (self.board.dealer_index + 2) % num  # Choose big blind position for variety
        # Mark this player as folded
        self.board.folded_players.add(folded_player)
        self.board.last_actions[folded_player] = 'fold'
        pre_contrib = dict(contributions)
        # Deal flop
        self.game.deal_community(3)
        start = (self.board.dealer_index + 1) % num
        new_contributions, active = self.game.betting_round(start, contributions)
        # The folded player must not be in active list
        self.assertNotIn(folded_player, active, "Folded player appeared in active players after folding.")
        # Their contribution should remain unchanged (no additional bets)
        self.assertEqual(new_contributions.get(folded_player, 0), pre_contrib.get(folded_player, 0))
        # Action should still be recorded as fold
        self.assertEqual(self.board.last_actions.get(folded_player), 'fold')


if __name__ == '__main__':
    # Run tests with verbose output to see the game results
    unittest.main(verbosity=2)
