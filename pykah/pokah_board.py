import pydealer
from pydealer.const import POKER_RANKS
from pykah.player import create_players


class Board:
    def __init__(self, human_name, num_players, start_stack, big_blind):
        self.num_players = num_players
        self.start_stack = start_stack
        self.big_blind = big_blind
        self.deck = pydealer.Deck(ranks=POKER_RANKS)
        self.deck.shuffle()
        # Pass start_stack through so players get correct starting chips
        self.players = create_players(num_players, human_name, start_stack)

        # Per-hand state - updated by the Game
        self.community_cards = []  # list of pydealer.Card
        self.pot = 0
        self.current_bet = 0
        self.dealer_index = 0

    def reset_for_new_hand(self):
        # Reset per-hand state; keep player chip stacks
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        # Reset player hole cards
        for p in self.players:
            p.reset_for_new_hand()

    def print_board(self):
        print("Board with " + str(self.num_players) + " players:")
        for p in self.players:
            print(p)
