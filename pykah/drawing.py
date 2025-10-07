import math

import pygame
from pygame import font
import numpy as np

board_surface = (200, 100, 1000, 500)

name_color = (128, 128, 255)
stack_color = (128, 128, 128)

# Lazily initialized font object - created once and reused
PLAYER_FONT = None
CARD_FONT = None
PLAYER_FONT_NAME = 'Arial'
PLAYER_FONT_SIZE = 16
CARD_FONT_SIZE = 20

# Cache player positions per player count so we don't recompute every frame
_player_positions_cache = {}

# Expose human rect and prompt area so the prompt UI can position itself relative to the human
HUMAN_RECT = None
PROMPT_AREA = None


def ensure_font():
    """Ensure the pygame font subsystem and the shared PLAYER_FONT/CARD_FONT are initialized.
    This is safe to call multiple times; the font objects are created only once.
    """
    global PLAYER_FONT, CARD_FONT
    if PLAYER_FONT is None or CARD_FONT is None:
        if not pygame.font.get_init():
            pygame.font.init()
        if PLAYER_FONT is None:
            PLAYER_FONT = pygame.font.SysFont(PLAYER_FONT_NAME, PLAYER_FONT_SIZE)
        if CARD_FONT is None:
            CARD_FONT = pygame.font.SysFont(PLAYER_FONT_NAME, CARD_FONT_SIZE)


def compute_player_positions(num_players=10):
    """Compute num_players positions distributed evenly along the lower half of the
    ellipse defined by board_surface. Returns a tuple of (x, y, w, h) rects.

    Ensures one of the positions (the bottom-most) will be assigned to the human
    player (index 0) by rotating the computed positions so the bottom-most position
    is first.
    """
    center_x = board_surface[0] + board_surface[2] // 2
    center_y = board_surface[1] + board_surface[3] // 2
    radius_x = board_surface[2] // 2
    radius_y = board_surface[3] // 2
    rect_w, rect_h = 120, 120

    # Parameterize the lower half of the ellipse with high resolution
    t = np.linspace(math.pi, 2 * math.pi, 3000)
    x = center_x + radius_x * np.cos(t)
    y = center_y + radius_y * np.sin(t)

    # Compute cumulative arc length along the sampled curve
    dx = np.diff(x)
    dy = np.diff(y)
    dist = np.sqrt(dx ** 2 + dy ** 2)
    arc = np.concatenate(([0], np.cumsum(dist)))
    total_arc = arc[-1]

    # Evenly spaced arc lengths for all player positions
    target_arcs = np.linspace(0, total_arc, num_players)

    # For each target arc length, find the index in the sampled arc closest to it
    indices = np.searchsorted(arc, target_arcs)
    indices = np.clip(indices, 0, len(x) - 1)

    positions = []
    for idx in indices:
        px = int(x[idx] - rect_w // 2)
        py = int(y[idx] - rect_h // 2)
        positions.append((px, py, rect_w, rect_h))

    # Find the bottom-most position (max y + rect_h) to place the human
    bottom_index = max(range(len(positions)), key=lambda i: positions[i][1] + positions[i][3])

    # Rotate so bottom_index becomes 0
    rotated = positions[bottom_index:] + positions[:bottom_index]

    return tuple(rotated)


player_positions = None

def draw_board(screen, board):
    # Draw the board surface
    pygame.draw.ellipse(screen, (0, 100, 0), board_surface)

    # Ensure the font is ready and reuse the same font object every frame
    ensure_font()

    global _player_positions_cache, HUMAN_RECT, PROMPT_AREA
    if board.num_players not in _player_positions_cache:
        _player_positions_cache[board.num_players] = compute_player_positions(board.num_players)

    player_positions = _player_positions_cache[board.num_players]

    # Update HUMAN_RECT (player 0 is human and now placed at bottom-most position)
    HUMAN_RECT = player_positions[0]

    for p in range(board.num_players):
        rect = player_positions[p]
        pygame.draw.rect(screen, (0, 0, 0), rect, 0, 5)
        pygame.draw.rect(screen, (128, 255, 128), rect, 3, 5)
        # Draw player name and stack
        player = board.players[p]
        name_text = PLAYER_FONT.render(player.name, True, name_color)
        stack_text = PLAYER_FONT.render("chip stack:", True, stack_color)
        stack_value = PLAYER_FONT.render(f"{player.chip_stack}", True, stack_color)
        screen.blit(name_text, (rect[0] + 10, rect[1] + 10))
        screen.blit(stack_text, (rect[0] + 10, rect[1] + 40))
        screen.blit(stack_value, (rect[0] + 10, rect[1] + 65))

    # Draw the human player's hole cards centered below the board
    try:
        human = board.players[0]
    except Exception:
        human = None

    PROMPT_AREA = None
    if human and hasattr(human, 'hole_cards') and human.hole_cards:
        # Card visuals
        CARD_W, CARD_H = 60, 90
        GAP = 10
        num_cards = len(human.hole_cards)
        total_w = num_cards * CARD_W + (num_cards - 1) * GAP
        center_x = board_surface[0] + board_surface[2] // 2
        start_x = center_x - total_w // 2
        cards_y = board_surface[1] + board_surface[3] + 20  # 20px below the board

        for i, c in enumerate(human.hole_cards):
            cx = start_x + i * (CARD_W + GAP)
            card_rect = (cx, cards_y, CARD_W, CARD_H)
            # Draw card background and border
            pygame.draw.rect(screen, (255, 255, 255), card_rect, 0, 5)
            pygame.draw.rect(screen, (0, 0, 0), card_rect, 2, 5)
            # Card label (use the pydealer abbrev or name)
            label = getattr(c, 'abbrev', None) or getattr(c, 'name', str(c))
            # Center the label in the card
            text_surf = CARD_FONT.render(label, True, (0, 0, 0))
            tx = cx + (CARD_W - text_surf.get_width()) // 2
            ty = cards_y + (CARD_H - text_surf.get_height()) // 2
            screen.blit(text_surf, (tx, ty))

        # Define prompt area below the human's hole cards
        # Make prompt area at least a reasonable width so the prompt text fits
        min_prompt_w = 400
        prompt_w = max(total_w, min_prompt_w)
        # center prompt area under the table
        prompt_x = center_x - prompt_w // 2
        prompt_y = cards_y + CARD_H + 8
        prompt_h = 80
        PROMPT_AREA = (prompt_x, prompt_y, prompt_w, prompt_h)

    # Also draw community cards (if any) near the center of the table
    if hasattr(board, 'community_cards') and board.community_cards:
        CARD_W, CARD_H = 50, 75
        GAP = 8
        num = len(board.community_cards)
        total_w = num * CARD_W + (num - 1) * GAP
        center_x = board_surface[0] + board_surface[2] // 2
        start_x = center_x - total_w // 2
        # Position slightly above the center of the ellipse
        y = board_surface[1] + board_surface[3] // 2 - CARD_H // 2
        for i, c in enumerate(board.community_cards):
            cx = start_x + i * (CARD_W + GAP)
            card_rect = (cx, y, CARD_W, CARD_H)
            pygame.draw.rect(screen, (255, 255, 255), card_rect, 0, 5)
            pygame.draw.rect(screen, (0, 0, 0), card_rect, 2, 5)
            label = getattr(c, 'abbrev', None) or getattr(c, 'name', str(c))
            text_surf = CARD_FONT.render(label, True, (0, 0, 0))
            tx = cx + (CARD_W - text_surf.get_width()) // 2
            ty = y + (CARD_H - text_surf.get_height()) // 2
            screen.blit(text_surf, (tx, ty))
