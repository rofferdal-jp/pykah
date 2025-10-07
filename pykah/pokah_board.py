import pydealer
from pydealer.const import POKER_RANKS
from pykah.player import create_players


class Board:
    def __init__(self, human_name, num_players, start_stack, big_blind):
        self.num_players = num_players
        self.deck = pydealer.Deck(ranks=POKER_RANKS)
        self.players = create_players(num_players, human_name)

    def print_board(self):
        print("Board with " + str(self.num_players) + " players:")
        for p in self.players:
            print(p)
