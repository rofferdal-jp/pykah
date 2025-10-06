MAX_PLAYERS = 10

class Player:
    def __init__(self, name, chip_stack):
        self.name = name
        self.chip_stack = chip_stack

    def __str__(self):
        return(self.name + " - stack: " + str(self.chip_stack))

def create_players(num = 4, start_stack = 1000):
    if num > MAX_PLAYERS or num < 1:
        raise Exception("Number of players must be between 1 and " + str(MAX_PLAYERS))
    player_names = ["Arthur", "Brady", "Charly", "Don", "Eric", "Fred", "Ginny", "Heather", "Ivan", "Joker"]
    players = []
    for x in range(num):
        players.append(Player(player_names[x], start_stack))
    return players

