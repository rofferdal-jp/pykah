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
    # Ensure the pygame font subsystem and the shared PLAYER_FONT/CARD_FONT are initialized.

    global PLAYER_FONT, CARD_FONT
    if PLAYER_FONT is None or CARD_FONT is None:
        if not pygame.font.get_init():
            pygame.font.init()
        if PLAYER_FONT is None:
            PLAYER_FONT = pygame.font.SysFont(PLAYER_FONT_NAME, PLAYER_FONT_SIZE)
        if CARD_FONT is None:
            CARD_FONT = pygame.font.SysFont(PLAYER_FONT_NAME, CARD_FONT_SIZE)


def draw_card(screen, card, x, y, width, height, border_radius=5, border_width=2, font_override=None):
    # Draw a single card at the specified position with consistent styling

    ensure_font()

    card_rect = (x, y, width, height)

    # Draw card background and border
    pygame.draw.rect(screen, (255, 255, 255), card_rect, 0, border_radius)
    pygame.draw.rect(screen, (0, 0, 0), card_rect, border_width, border_radius)

    # Get card information
    card_str = getattr(card, 'abbrev', None) or getattr(card, 'name', str(card))

    # Parse card value and suit
    if hasattr(card, 'value') and hasattr(card, 'suit'):
        # Use card object attributes
        value = card.value
        suit = card.suit
    else:
        # Parse from string representation (e.g., "As", "Kh", "10d", "Jc")
        if len(card_str) >= 2:
            if card_str[-1].lower() in 'shdc':
                value = card_str[:-1]
                suit_char = card_str[-1].lower()
                suit_map = {'s': 'Spades', 'h': 'Hearts', 'd': 'Diamonds', 'c': 'Clubs'}
                suit = suit_map.get(suit_char, 'Spades')
            else:
                value = card_str
                suit = 'Spades'  # default
        else:
            value = card_str
            suit = 'Spades'  # default

    # Convert value to display format
    value_display = value
    if value == '10':
        value_display = 'T'
    elif value == 'Jack':
        value_display = 'J'
    elif value == 'Queen':
        value_display = 'Q'
    elif value == 'King':
        value_display = 'K'
    elif value == 'Ace':
        value_display = 'A'

    # Suit symbols and colors
    suit_symbols = {
        'Spades': '♠',
        'Hearts': '♥',
        'Diamonds': '♦',
        'Clubs': '♣'
    }

    suit_colors = {
        'Spades': (0, 0, 0),      # Black
        'Hearts': (255, 0, 0),    # Red
        'Diamonds': (255, 0, 0),  # Red
        'Clubs': (0, 0, 0)        # Black
    }

    suit_symbol = suit_symbols.get(suit, '?')
    suit_color = suit_colors.get(suit, (0, 0, 0))

    font_to_use = font_override or CARD_FONT

    # Render value and suit
    value_surf = font_to_use.render(value_display, True, suit_color)
    suit_surf = font_to_use.render(suit_symbol, True, suit_color)

    # Calculate positioning for stacked layout (value on top, suit below)
    total_height = value_surf.get_height() + suit_surf.get_height() + 2  # 2px gap
    start_y = y + (height - total_height) // 2

    # Center horizontally
    value_x = x + (width - value_surf.get_width()) // 2
    suit_x = x + (width - suit_surf.get_width()) // 2

    # Draw value and suit
    screen.blit(value_surf, (value_x, start_y))
    screen.blit(suit_surf, (suit_x, start_y + value_surf.get_height() + 2))

def compute_player_positions(num_players=10):
    # Compute player positions around the board surface ellipse

    center_x = board_surface[0] + board_surface[2] // 2
    center_y = board_surface[1] + board_surface[3] // 2
    radius_x = board_surface[2] // 2
    radius_y = board_surface[3] // 2
    rect_w, rect_h = 120, 120

    # For AI players, use the entire upper arch (from π to 2π)
    # We need (num_players - 1) positions since human is positioned separately
    ai_player_count = num_players - 1

    if ai_player_count > 0:
        # Parameterize the upper arch of the ellipse with high resolution
        # Use π to 2π to get the upper half of the ellipse
        t = np.linspace(math.pi, 2 * math.pi, 3000)
        x = center_x + radius_x * np.cos(t)
        y = center_y + radius_y * np.sin(t)

        # Compute cumulative arc length along the sampled curve
        dx = np.diff(x)
        dy = np.diff(y)
        dist = np.sqrt(dx ** 2 + dy ** 2)
        arc = np.concatenate(([0], np.cumsum(dist)))
        total_arc = arc[-1]

        # Evenly spaced arc lengths for AI player positions
        target_arcs = np.linspace(0, total_arc, ai_player_count)

        # For each target arc length, find the index in the sampled arc closest to it
        indices = np.searchsorted(arc, target_arcs)
        indices = np.clip(indices, 0, len(x) - 1)

        ai_positions = []
        for idx in indices:
            px = int(x[idx] - rect_w // 2)
            py = int(y[idx] - rect_h // 2)
            ai_positions.append((px, py, rect_w, rect_h))
    else:
        ai_positions = []

    # Create the full positions list with placeholder for human (index 0)
    # Human position will be set dynamically in draw_board
    positions = [(0, 0, rect_w, rect_h)]  # Placeholder for human player
    positions.extend(ai_positions)

    return tuple(positions)


player_positions = None

def draw_board(screen, board):
    # Draw the board surface
    pygame.draw.ellipse(screen, (0, 100, 0), board_surface)

    # Ensure the font is ready and reuse the same font object every frame
    ensure_font()

    global _player_positions_cache, HUMAN_RECT, PROMPT_AREA
    if board.num_players not in _player_positions_cache:
        _player_positions_cache[board.num_players] = compute_player_positions(board.num_players)

    player_positions = list(_player_positions_cache[board.num_players])

    # Calculate blind positions
    num = board.num_players
    dealer_index = board.dealer_index
    small_blind_index = (dealer_index + 1) % num
    big_blind_index = (dealer_index + 2) % num

    # Calculate human player position above hole cards
    try:
        human = board.players[0]
        if human and hasattr(human, 'hole_cards') and human.hole_cards:
            # Card position calculations
            CARD_W, CARD_H = 60, 90
            GAP = 10
            num_cards = len(human.hole_cards)
            total_w = num_cards * CARD_W + (num_cards - 1) * GAP
            center_x = board_surface[0] + board_surface[2] // 2
            cards_y = board_surface[1] + board_surface[3] + 20  # 20px below the board

            # Position human player rect above the hole cards
            rect_w, rect_h = 120, 120
            human_x = center_x - rect_w // 2
            human_y = cards_y - rect_h - 10  # 10px above the cards
            player_positions[0] = (human_x, human_y, rect_w, rect_h)
    except Exception:
        pass

    # Update HUMAN_RECT
    HUMAN_RECT = player_positions[0]

    for p in range(board.num_players):
        player_rect = player_positions[p]
        pygame.draw.rect(screen, (0, 0, 0), player_rect, 0, 5)

        # Draw wider outline for human player (player 0)
        if p == 0:  # Human player
            pygame.draw.rect(screen, (255, 255, 255), player_rect, 6, 5)  # Wider white outline for human
        else:
            pygame.draw.rect(screen, (128, 255, 128), player_rect, 3, 5)  # Normal outline for AI players

        # Draw player name and stack
        player = board.players[p]
        name_text = PLAYER_FONT.render(player.name, True, name_color)
        stack_text = PLAYER_FONT.render("chip stack:", True, stack_color)
        stack_value = PLAYER_FONT.render(f"{player.chip_stack}", True, stack_color)
        screen.blit(name_text, (player_rect[0] + 10, player_rect[1] + 10))
        screen.blit(stack_text, (player_rect[0] + 10, player_rect[1] + 40))
        screen.blit(stack_value, (player_rect[0] + 10, player_rect[1] + 65))

        # Draw bet amounts and actions in the same position
        if hasattr(board, 'current_round_contributions') and p in board.current_round_contributions:
            bet_amount = board.current_round_contributions[p]
            if bet_amount > 0:
                # Calculate position much closer to player rect
                board_center_x = board_surface[0] + board_surface[2] // 2
                board_center_y = board_surface[1] + board_surface[3] // 2
                player_center_x = player_rect[0] + player_rect[2] // 2
                player_center_y = player_rect[1] + player_rect[3] // 2

                # Position bet amount only 25% of the way from player to board center
                bet_x = int(player_center_x + 0.25 * (board_center_x - player_center_x))
                bet_y = int(player_center_y + 0.35 * (board_center_y - player_center_y))

                # Draw bet amount in yellow
                bet_text = PLAYER_FONT.render(f"bet: {bet_amount}", True, (255, 255, 0))
                text_x = bet_x - bet_text.get_width() // 2
                text_y = bet_y - bet_text.get_height() // 2
                screen.blit(bet_text, (text_x, text_y))

                # Draw last action - above bet for human player, below for AI players
                if hasattr(board, 'last_actions') and p in board.last_actions:
                    action = board.last_actions[p]
                    action_text = PLAYER_FONT.render(action, True, (160, 160, 160))
                    action_x = bet_x - action_text.get_width() // 2

                    if p == 0:  # Human player - action above bet
                        action_y = bet_y - action_text.get_height() - 5
                    else:  # AI players - action below bet
                        action_y = bet_y + bet_text.get_height() + 5

                    screen.blit(action_text, (action_x, action_y))

        # Show last action even if no bet (for checks, folds, etc.)
        elif hasattr(board, 'last_actions') and p in board.last_actions:
            action = board.last_actions[p]
            # Calculate position much closer to player rect
            board_center_x = board_surface[0] + board_surface[2] // 2
            board_center_y = board_surface[1] + board_surface[3] // 2
            player_center_x = player_rect[0] + player_rect[2] // 2
            player_center_y = player_rect[1] + player_rect[3] // 2

            # Position action text
            action_x = int(player_center_x + 0.25 * (board_center_x - player_center_x))
            action_y = int(player_center_y + 0.35 * (board_center_y - player_center_y))

            # Draw action in light gray (including "fold")
            action_text = PLAYER_FONT.render(action, True, (160, 160, 160))
            text_x = action_x - action_text.get_width() // 2
            text_y = action_y - action_text.get_height() // 2
            screen.blit(action_text, (text_x, text_y))

        # Check for winner display - override action display
        if hasattr(board, 'winners') and p in board.winners:
            # Calculate position for winner text
            board_center_x = board_surface[0] + board_surface[2] // 2
            board_center_y = board_surface[1] + board_surface[3] // 2
            player_center_x = player_rect[0] + player_rect[2] // 2
            player_center_y = player_rect[1] + player_rect[3] // 2

            winner_x = int(player_center_x + 0.25 * (board_center_x - player_center_x))
            winner_y = int(player_center_y + 0.35 * (board_center_y - player_center_y))

            # Show "WON!" or "SPLIT" in bright golden letters
            if hasattr(board, 'is_split_pot') and board.is_split_pot:
                winner_text = PLAYER_FONT.render("SPLIT", True, (255, 215, 0))  # Golden color
            else:
                winner_text = PLAYER_FONT.render("WON!", True, (255, 215, 0))  # Golden color

            text_x = winner_x - winner_text.get_width() // 2
            text_y = winner_y - winner_text.get_height() // 2
            screen.blit(winner_text, (text_x, text_y))

        # Draw showdown cards for players in showdown mode
        if hasattr(board, 'showdown_mode') and board.showdown_mode and p in board.showdown_players:
            player_obj = board.players[p]
            if hasattr(player_obj, 'hole_cards') and player_obj.hole_cards:
                # Position cards next to the player rectangle
                CARD_W, CARD_H = 40, 60
                GAP = 5
                cards_start_x = player_rect[0] + player_rect[2] + 10  # Right side of player rect
                cards_y = player_rect[1] + player_rect[3] // 2 - CARD_H // 2  # Vertically centered

                for i, card in enumerate(player_obj.hole_cards):
                    card_x = cards_start_x + i * (CARD_W + GAP)
                    draw_card(screen, card, card_x, cards_y, CARD_W, CARD_H, border_radius=3, border_width=1, font_override=PLAYER_FONT)

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
            draw_card(screen, c, cx, cards_y, CARD_W, CARD_H, border_radius=5, border_width=2)

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
    community_top = None
    if hasattr(board, 'community_cards') and board.community_cards:
        CARD_W, CARD_H = 50, 75
        GAP = 8
        num = len(board.community_cards)
        total_w = num * CARD_W + (num - 1) * GAP
        center_x = board_surface[0] + board_surface[2] // 2
        start_x = center_x - total_w // 2
        # Position the community cards just below the middle of the table so winner overlay
        # can be rendered above them without obscuring the cards.
        center_y = board_surface[1] + board_surface[3] // 2
        y = center_y + 10  # top of community cards placed 10px below the vertical middle
        community_top = y
        for i, c in enumerate(board.community_cards):
            cx = start_x + i * (CARD_W + GAP)
            draw_card(screen, c, cx, y, CARD_W, CARD_H, border_radius=5, border_width=2)

    # Draw dealer button, small blind, and big blind markers
    # Draw these inside the player rectangles in the upper right corner
    BUTTON_RADIUS = 12
    MARKER_INSET = 5  # Distance from player rect edge (inside)

    for p in range(board.num_players):
        player_rect = player_positions[p]

        # Calculate position in upper right corner of player rectangle
        marker_x = player_rect[0] + player_rect[2] - BUTTON_RADIUS - MARKER_INSET

        # Dealer button (white circle with "D")
        if p == dealer_index:
            marker_y = player_rect[1] + BUTTON_RADIUS + MARKER_INSET
            pygame.draw.circle(screen, (255, 255, 255), (marker_x, marker_y), BUTTON_RADIUS)
            pygame.draw.circle(screen, (0, 0, 0), (marker_x, marker_y), BUTTON_RADIUS, 2)
            dealer_text = PLAYER_FONT.render("D", True, (0, 0, 0))
            text_x = marker_x - dealer_text.get_width() // 2
            text_y = marker_y - dealer_text.get_height() // 2
            screen.blit(dealer_text, (text_x, text_y))

        # Small blind marker (yellow circle with "SB")
        if p == small_blind_index:
            marker_y = player_rect[1] + BUTTON_RADIUS + MARKER_INSET
            # If also dealer, position SB below the dealer button
            if p == dealer_index:
                marker_y += BUTTON_RADIUS * 2 + 5
            pygame.draw.circle(screen, (255, 255, 0), (marker_x, marker_y), BUTTON_RADIUS)
            pygame.draw.circle(screen, (0, 0, 0), (marker_x, marker_y), BUTTON_RADIUS, 2)
            sb_text = PLAYER_FONT.render("SB", True, (0, 0, 0))
            text_x = marker_x - sb_text.get_width() // 2
            text_y = marker_y - sb_text.get_height() // 2
            screen.blit(sb_text, (text_x, text_y))

        # Big blind marker (red circle with "BB")
        if p == big_blind_index:
            marker_y = player_rect[1] + BUTTON_RADIUS + MARKER_INSET
            # If also dealer, position BB below the dealer button
            if p == dealer_index:
                marker_y += BUTTON_RADIUS * 2 + 5
            # If also small blind (heads-up), position BB below SB
            if p == small_blind_index:
                marker_y += BUTTON_RADIUS * 2 + 5
            pygame.draw.circle(screen, (255, 100, 100), (marker_x, marker_y), BUTTON_RADIUS)
            pygame.draw.circle(screen, (0, 0, 0), (marker_x, marker_y), BUTTON_RADIUS, 2)
            bb_text = PLAYER_FONT.render("BB", True, (0, 0, 0))
            text_x = marker_x - bb_text.get_width() // 2
            text_y = marker_y - bb_text.get_height() // 2
            screen.blit(bb_text, (text_x, text_y))

    # Draw pot display in the lower right part of the board
    pot_amount = getattr(board, 'pot', 0)
    if pot_amount > 0:
        # Position in lower right area of the board surface
        pot_box_w = 150
        pot_box_h = 60
        pot_x = board_surface[0] + board_surface[2] - pot_box_w - 20  # 20px from right edge
        pot_y = board_surface[1] + board_surface[3] - pot_box_h - 20  # 20px from bottom edge

        # Draw pot box background
        pygame.draw.rect(screen, (50, 50, 50), (pot_x, pot_y, pot_box_w, pot_box_h), 0, 5)
        pygame.draw.rect(screen, (255, 215, 0), (pot_x, pot_y, pot_box_w, pot_box_h), 3, 5)  # Golden border

        # Draw pot label and amount
        pot_label = PLAYER_FONT.render("POT", True, (255, 215, 0))
        pot_value = PLAYER_FONT.render(f"{pot_amount}", True, (255, 255, 255))

        # Center the text in the pot box
        label_x = pot_x + (pot_box_w - pot_label.get_width()) // 2
        label_y = pot_y + 8
        value_x = pot_x + (pot_box_w - pot_value.get_width()) // 2
        value_y = pot_y + pot_box_h - pot_value.get_height() - 8

        screen.blit(pot_label, (label_x, label_y))
        screen.blit(pot_value, (value_x, value_y))

    # End-of-hand overlay
    if getattr(board, 'hand_complete', False):
        overlay_w = 500
        overlay_h = 100  # Slightly taller to fit winner + hand type + prompt
        center_x = board_surface[0] + board_surface[2] // 2
        # Position overlay above the community cards so the cards remain visible
        if community_top is not None:
            oy = community_top - overlay_h - 10
        else:
            center_y = board_surface[1] + board_surface[3] // 2
            oy = center_y - overlay_h // 2
        ox = center_x - overlay_w // 2
        # clamp overlay to not go above board surface
        top_limit = board_surface[1] + 5
        if oy < top_limit:
            oy = top_limit
        pygame.draw.rect(screen, (0, 0, 0), (ox, oy, overlay_w, overlay_h), 0, 10)
        pygame.draw.rect(screen, (255, 215, 0), (ox, oy, overlay_w, overlay_h), 3, 10)
        # Build text lines
        lines = []
        if board.winners:
            if board.is_split_pot:
                winner_names = ", ".join(board.players[i].name for i in board.winners)
                lines.append(f"Split Pot: {winner_names}")
            else:
                winner_names = ", ".join(board.players[i].name for i in board.winners)
                lines.append(f"Winner: {winner_names}")
            # Show winning hand type if available
            if getattr(board, 'winning_hand_type', None):
                lines.append(f"Hand: {board.winning_hand_type}")
        else:
            lines.append("Hand Complete")
        lines.append("Press any key for next hand")
        # Render lines vertically centered inside the shorter overlay
        y_cursor = oy + 10
        for line in lines:
            text_surf = PLAYER_FONT.render(line, True, (255, 255, 255))
            tx = center_x - text_surf.get_width() // 2
            screen.blit(text_surf, (tx, y_cursor))
            y_cursor += text_surf.get_height() + 6
