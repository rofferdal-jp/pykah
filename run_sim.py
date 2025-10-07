# Headless simulation of one poker hand using the Game class
from pykah.pokah_board import Board
from pykah.game import Game

# Create a board with 5 players, start stack 1000, big blind 10
board = Board(human_name='AI', num_players=5, start_stack=1000, big_blind=10)
# Make all players non-human so no prompt_input UI is invoked
for p in board.players:
    p.is_human = False

game = Game(board)

winners = game.start_hand(prompt_human=False)
print('Winners indices:', winners)
print('Final stacks:')
for i, p in enumerate(board.players):
    print(i, p.name, p.chip_stack)
print('Community cards:')
print([c.name for c in board.community_cards])
print('Pot after hand (should be 0):', board.pot)

