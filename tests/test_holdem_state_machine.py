import unittest
from game_logic.holdem_state_machine import TexasHoldemStateMachine, GameState

class TestTexasHoldemStateMachine(unittest.TestCase):
    def test_state_transitions(self):
        print("Running state machine test...")
        sm = TexasHoldemStateMachine()
        sm.run_once(num_players=3, chip_stack=1000, big_blind=20, human_name="Tester")
        expected_states = [
            GameState.SETUP,
            GameState.NEW_HAND,
            GameState.PRE_FLOP,
            GameState.FLOP,
            GameState.TURN,
            GameState.RIVER,
            GameState.SHOWDOWN,
            GameState.END_HAND
        ]
        # Only check the last 8 states to allow for possible extra SETUP at start
        self.assertEqual(sm.state_history[-8:], expected_states)

if __name__ == "__main__":
    unittest.main()
