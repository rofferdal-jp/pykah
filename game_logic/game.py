from game_logic.player import Player

class Game:
    def __init__(self, num_players, initial_chip_stack, big_blind, human_name):
        self.num_players = num_players
        self.initial_chip_stack = initial_chip_stack
        self.big_blind = big_blind
        self.small_blind = big_blind // 2
        self.total_chips = num_players * initial_chip_stack
        self.players = []
        # Initialize players: first is human, rest are CPU
        for i in range(num_players):
            if i == 0:
                name = human_name
                is_human = True
            else:
                name = f"CPU_{i}"
                is_human = False
            player = Player(name, is_human, initial_chip_stack, i)
            self.players.append(player)

    def __repr__(self):
        return (f"Game(num_players={self.num_players}, initial_chip_stack={self.initial_chip_stack}, "
                f"big_blind={self.big_blind}, small_blind={self.small_blind}, total_chips={self.total_chips}, "
                f"players={self.players})")

