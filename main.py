import pygame

from pykah.drawing import draw_board
from pykah.init_prompt import prompt_input
from pykah.pokah_board import Board

def main():

    num_players = prompt_input("Enter number of players (2-10)", "5", numeric=True)
    chip_stack = prompt_input("Enter starting chip stack", "1000", numeric=True)
    big_blind = prompt_input("Enter big blind amount", "10", numeric=True)
    human_name = prompt_input("Enter your name (leave blank for default)", "", numeric=False)
    if human_name == "":
        print("Hello. A default name will be assigned to you.")

    pygame.init()

    SCREEN_SIZE = (1400, 800)
    screen = pygame.display.set_mode(SCREEN_SIZE)

    board = Board(human_name, num_players, chip_stack, big_blind)
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

