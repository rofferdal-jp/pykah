import pygame

from pykah.drawing import draw_board
from pykah.pokah_board import Board

def main():
    pygame.init()

    SCREEN_SIZE = (1600, 900)
    screen = pygame.display.set_mode(SCREEN_SIZE)

    board = Board(num_players=10)
    print("initial board:")
    board.print_board()

    running = True
    while running:

        screen.fill((0, 0, 0))

        # board surface
        draw_board(screen, board)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pygame.display.update()

    pygame.quit()

# Standard entry point structure
if __name__ == "__main__":
    main()

