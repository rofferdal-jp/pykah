# Collect game settings via a simple pygame UI (drawn before the game starts)
import pygame

pygame.init()
_SCREEN_PROMPT = (1400, 800)
_screen_prompt = pygame.display.set_mode(_SCREEN_PROMPT)
_font = pygame.font.Font(None, 36)

from typing import Optional

# Import drawing.draw_board lazily to avoid circular imports at module import time
# We'll import inside the function when needed.

def prompt_input(prompt, default, numeric=False, board: Optional[object]=None):
    """Prompt the user for input using a simple pygame UI.
    If `board` is provided, the board will be drawn behind the prompt so the
    player can see the table and their cards while entering actions.

    Returns the entered string (or default if Enter with empty input) or int if numeric=True.
    """
    s = ""
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if numeric:
                        return int(s) if s.strip() else int(default)
                    return s.strip() if s.strip() else default
                elif event.key == pygame.K_BACKSPACE:
                    s = s[:-1]
                else:
                    if event.unicode:
                        s += event.unicode
        # draw background: if we have a board, draw it under the prompt
        if board is not None:
            try:
                # import here to avoid circular imports at module import time
                import pykah.drawing as drawing
                # Clear screen
                _screen_prompt.fill((0, 0, 0))
                # Let draw_board paint the table and cards
                drawing.draw_board(_screen_prompt, board)
                # Read the prompt area set by draw_board after drawing
                area = drawing.PROMPT_AREA
            except Exception:
                # fallback to plain green background
                _screen_prompt.fill((0, 128, 0))
                area = None
        else:
            _screen_prompt.fill((0, 128, 0))
            area = None

        # If PROMPT_AREA is available, draw the prompt inside it
        if area:
            try:
                px, py, pw, ph = area
                # Draw prompt background box
                pygame.draw.rect(_screen_prompt, (30, 30, 30), (px - 6, py - 6, pw + 12, ph + 12))
                # Render label and entry within box with padding
                label = _font.render(f"{prompt}  (default: {default})", True, (255, 255, 255))
                entry = _font.render(s, True, (255, 255, 255))
                _screen_prompt.blit(label, (px + 6, py + 6))
                _screen_prompt.blit(entry, (px + 6, py + 6 + label.get_height() + 6))
            except Exception:
                # fallback to top-left
                label = _font.render(f"{prompt}  (default: {default})", True, (255, 255, 255))
                entry = _font.render(s, True, (255, 255, 255))
                _screen_prompt.blit(label, (50, 50))
                _screen_prompt.blit(entry, (50, 100))
        else:
            label = _font.render(f"{prompt}  (default: {default})", True, (255, 255, 255))
            entry = _font.render(s, True, (255, 255, 255))
            _screen_prompt.blit(label, (50, 50))
            _screen_prompt.blit(entry, (50, 100))

        pygame.display.flip()
        clock.tick(30)
