MAX_PLAYERS = 10

class Player:
    def __init__(self, name, is_human, chip_stack, board_position):
        self.name = name
        self.is_human = is_human
        self.chip_stack = chip_stack
        self.board_position = board_position

    def __str__(self):
        if self.is_human:
            return self.name + " (human) - stack: " + str(self.chip_stack)
        return self.name + " - stack: " + str(self.chip_stack)

def create_players(num, human_name, start_stack = 1000):
    if num > MAX_PLAYERS or num < 1:
        raise Exception("Number of players must be between 1 and " + str(MAX_PLAYERS))
    player_names = ["Arthur", "Brady", "Charly", "Don", "Eric", "Fred", "Ginny", "Heather", "Ivan", "Joker"]
    if human_name is None or human_name.strip() == "":
        human_name = player_names[0]
    players = [(Player(human_name, True, start_stack, 0))]
    for pos in range(1, num):
        players.append(Player(player_names[pos], False, start_stack, pos))
    return players

