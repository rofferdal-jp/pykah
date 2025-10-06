import pygame
from pygame import font

# Initialize font module once
pygame.font.init()
# Create font object once, reuse in draw_board
PLAYER_FONT = pygame.font.SysFont('Arial', 20)

board_surface = (200, 200, 1300, 600)
player_positions = ((160, 400, 120, 100), (300, 270, 120, 100),
                    (440, 200, 120, 100), (580, 170, 120, 100), (720, 150, 120, 100),
                    (860, 150, 120, 100), (1000, 170, 120, 100), (1140, 200, 120, 100),
                    (1280, 270, 120, 100), (1420, 400, 120, 100))
name_color = (128, 128, 255)
stack_color = (128, 128, 128)

def draw_board(screen, board):
    # Draw the board surface
    pygame.draw.ellipse(screen, (0, 100, 0), board_surface)

    for p in range(board.num_players):
        pygame.draw.rect(screen, (0, 0, 0), player_positions[p], 0, 5)
        pygame.draw.rect(screen, (128, 255, 128), player_positions[p], 3, 5)
        # Draw player name and stack
        player = board.players[p]
        name_text = PLAYER_FONT.render(player.name, True, name_color)
        stack_text = PLAYER_FONT.render(f"chip stack:", True, stack_color)
        stack_value = PLAYER_FONT.render(f"{player.chip_stack}", True, stack_color)
        rect = player_positions[p]
        screen.blit(name_text, (rect[0] + 10, rect[1] + 10))
        screen.blit(stack_text, (rect[0] + 10, rect[1] + 40))
        screen.blit(stack_value, (rect[0] + 10, rect[1] + 65))
