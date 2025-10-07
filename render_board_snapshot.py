import pygame
from pykah.pokah_board import Board
from pykah.drawing import draw_board

pygame.init()
SCREEN_SIZE = (1400, 800)
# create a surface to draw on
surface = pygame.Surface(SCREEN_SIZE)

# Create board and deal hole cards
board = Board('You', num_players=5, start_stack=1000, big_blind=10)
# Deal hole cards to each player
for p in board.players:
    hand = board.deck.deal(2)
    p.hole_cards = list(hand.cards)
# Deal some community cards for visualization
board.community_cards = list(board.deck.deal(3).cards)

# Draw and save snapshot
draw_board(surface, board)
path = 'board_snapshot.png'
pygame.image.save(surface, path)
print('Saved snapshot to', path)

pygame.quit()

