import os
import pygame
import pykah.drawing as drawing
from pykah.pokah_board import Board

pygame.init()
SCREEN_SIZE = (1400, 800)
surface = pygame.Surface(SCREEN_SIZE)

board = Board('You', num_players=10, start_stack=1000, big_blind=10)
# Ensure each player has hole cards
for p in board.players:
    p.hole_cards = list(board.deck.deal(2).cards)
board.community_cards = list(board.deck.deal(3).cards)

# Draw
drawing.draw_board(surface, board)
# Save file
path = 'board_snapshot_prompt.png'
pygame.image.save(surface, path)

# Gather file info
exists = os.path.exists(path)
size = os.path.getsize(path) if exists else None

print('Saved snapshot to', path, '(exists:', exists, ', size:', size, 'bytes)')
print('drawing.PROMPT_AREA =', drawing.PROMPT_AREA)
print('drawing.HUMAN_RECT =', drawing.HUMAN_RECT)

pygame.quit()

