# holdem_state_machine.py
# Texas Hold'em No Limit State Machine
import enum

class GameState(enum.Enum):
    SETUP = 1
    NEW_HAND = 2
    PRE_FLOP = 3
    FLOP = 4
    TURN = 5
    RIVER = 6
    SHOWDOWN = 7
    END_HAND = 8

class TexasHoldemStateMachine:
    def __init__(self):
        self.state = GameState.SETUP
        self.players = []
        self.chip_stack = 0
        self.big_blind = 0
        self.human_name = ""
        self.num_players = 0
        self.state_history = [self.state]

    def set_state(self, new_state):
        self.state = new_state
        self.state_history.append(self.state)
        print(f"State changed to: {self.state.name}")

    def setup(self, num_players, chip_stack, big_blind, human_name):
        self.num_players = num_players
        self.chip_stack = chip_stack
        self.big_blind = big_blind
        self.human_name = human_name
        self.players = [f"Player {i+1}" for i in range(self.num_players-1)]
        self.players.append(self.human_name)
        self.set_state(GameState.NEW_HAND)

    def play_hand(self):
        self.set_state(GameState.PRE_FLOP)
        self.set_state(GameState.FLOP)
        self.set_state(GameState.TURN)
        self.set_state(GameState.RIVER)
        self.set_state(GameState.SHOWDOWN)
        self.set_state(GameState.END_HAND)

    def reset_for_new_hand(self):
        self.set_state(GameState.NEW_HAND)

    def run_once(self, num_players, chip_stack, big_blind, human_name):
        self.set_state(GameState.SETUP)
        self.setup(num_players, chip_stack, big_blind, human_name)
        self.play_hand()

