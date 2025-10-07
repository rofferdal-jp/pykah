import pygame
from pykah.pokah_board import Board
import pykah.drawing as drawing

pygame.init()
SCREEN_SIZE = (1400, 800)
# create a surface to draw on
surface = pygame.Surface(SCREEN_SIZE)

# Create board with 10 players and deal hole cards
board = Board('You', num_players=10, start_stack=1000, big_blind=10)
for p in board.players:
    p.hole_cards = list(board.deck.deal(2).cards)
# Deal some community cards for visualization
board.community_cards = list(board.deck.deal(3).cards)

# Draw board to surface
drawing.draw_board(surface, board)
# Save snapshot
path = 'board_snapshot_prompt.png'
pygame.image.save(surface, path)

print('Saved snapshot to', path)
print('PROMPT_AREA =', drawing.PROMPT_AREA)
print('HUMAN_RECT =', drawing.HUMAN_RECT)

pygame.quit()
