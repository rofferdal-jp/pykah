import pygame

from pykah.pokah_board import Board

def main():
    pygame.init()

    SCREEN_SIZE = (1600, 900)
    screen = pygame.display.set_mode(SCREEN_SIZE)
    board_surface = (200, 200, 1300, 600)
    player_positions = ((160, 400, 120, 100), (300, 270, 120, 100),
                        (440, 200, 120, 100), (580, 170, 120, 100), (720, 150, 120, 100),
                        (860, 150, 120, 100), (1000, 170, 120, 100), (1140, 200, 120, 100),
                        (1280, 270, 120, 100), (1420, 400, 120, 100))

    board = Board(num_players=10)
    print("initial board:")
    board.print_board()

    running = True
    while running:

        screen.fill((0, 0, 0))

        # board surface
        pygame.draw.ellipse(screen, (0, 100, 0), board_surface)
        for p in range(board.num_players):
            pygame.draw.rect(screen, (0,0, 0), player_positions[p],0, 5)
            pygame.draw.rect(screen, (128,255, 128), player_positions[p],3, 5)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pygame.display.update()

    pygame.quit()

# Standard entry point structure
if __name__ == "__main__":
    main()

