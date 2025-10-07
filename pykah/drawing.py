import math

import pygame
from pygame import font
import numpy as np

# Initialize font module once
pygame.font.init()
# Create font object once, reuse in draw_board
PLAYER_FONT = pygame.font.SysFont('Arial', 16)

board_surface = (200, 100, 1000, 500)

name_color = (128, 128, 255)
stack_color = (128, 128, 128)

def compute_player_positions_old(num_players = 10):
    # Ellipse parameters (center and radii)
    center_x, center_y = 850, 500
    radius_x, radius_y = 650, 350
    rect_w, rect_h = 150, 150

    positions = [(center_x - rect_w // 2, center_y + radius_y - rect_h, rect_w, rect_h)]  # Human player position
    for i in range(1, num_players):
        angle = math.pi * (1 + i / (num_players - 1))  # pi to 2pi
        x = int(center_x + radius_x * math.cos(angle) - rect_w // 2)
        y = int(center_y + radius_y * math.sin(angle) - rect_h // 2)
        positions.append((x, y, rect_w, rect_h))
    positions = tuple(positions)

    return positions

def compute_player_positions(num_players=10):
    center_x, center_y = board_surface[0] + board_surface[2] // 2, board_surface[1] + board_surface[3] // 2
    radius_x, radius_y = board_surface[2] // 2, board_surface[3] // 2
    rect_w, rect_h = 120, 120
    num_comp_players = num_players - 1  # Exclude human player

    # Parameterize the lower half of the ellipse (pi to 2pi)
    t = np.linspace(np.pi, 2 * np.pi, 1000)
    x = center_x + radius_x * np.cos(t)
    y = center_y + radius_y * np.sin(t)

    # Compute cumulative arc length
    dx = np.diff(x)
    dy = np.diff(y)
    dist = np.sqrt(dx**2 + dy**2)
    arc = np.concatenate(([0], np.cumsum(dist)))
    total_arc = arc[-1]

    # Evenly spaced arc lengths
    target_arcs = np.linspace(0, total_arc, num_comp_players)

    # Find closest indices for each target arc length
    indices = np.searchsorted(arc, target_arcs)

    player_positions = [(center_x - rect_w // 2, center_y + radius_y - rect_h // 2, rect_w, rect_h)]  # Human player position

    for idx in indices:
        px = int(x[idx] - rect_w // 2)
        py = int(y[idx] - rect_h // 2)
        player_positions.append((px, py, rect_w, rect_h))

    return tuple(player_positions)

player_positions = None

def draw_board(screen, board):
    # Draw the board surface
    pygame.draw.ellipse(screen, (0, 100, 0), board_surface)

    global player_positions
    if player_positions is None:
        player_positions = compute_player_positions(board.num_players)

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
