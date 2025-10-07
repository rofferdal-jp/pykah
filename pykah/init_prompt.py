# Collect game settings via a simple pygame UI (drawn before the game starts)
import pygame

pygame.init()
_SCREEN_PROMPT = (1400, 800)
_screen_prompt = pygame.display.set_mode(_SCREEN_PROMPT)
_font = pygame.font.Font(None, 36)

def prompt_input(prompt, default, numeric=False):
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
        # draw a simple green board background and the prompt
        _screen_prompt.fill((0, 128, 0))
        label = _font.render(f"{prompt}  (default: {default})", True, (255, 255, 255))
        entry = _font.render(s, True, (255, 255, 255))
        _screen_prompt.blit(label, (50, 50))
        _screen_prompt.blit(entry, (50, 100))
        pygame.display.flip()
        clock.tick(30)

