# main.py
# Texas Hold'em No Limit program

import sys
sys.path.append('.')
from game_logic.holdem_state_machine import TexasHoldemStateMachine

def main():
    print("Welcome to Texas Hold'em No Limit!")
    num_players = int(input("Enter number of players: "))
    chip_stack = int(input("Enter initial chip stack for each player: "))
    big_blind = int(input("Enter big blind amount: "))
    human_name = input("Enter your name: ")
    game = TexasHoldemStateMachine()
    game.set_state(game.state)
    game.setup(num_players, chip_stack, big_blind, human_name)
    while True:
        game.play_hand()
        again = input("Play another hand? (y/n): ")
        if again.lower() != 'y':
            break
        game.reset_for_new_hand()

if __name__ == "__main__":
    main()
