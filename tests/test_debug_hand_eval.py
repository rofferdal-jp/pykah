#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import the game modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pykah.game_logic.game as game
import pydealer

def create_card(value, suit):
    return pydealer.Card(value, suit)

def test_kings_vs_sevens():
    print("Testing Kings vs 7s hand evaluation...")

    # Community cards: A♠ 5♦ 3♣ 9♥ 2♠
    community = [
        create_card('Ace', 'Spades'),
        create_card('5', 'Diamonds'),
        create_card('3', 'Clubs'),
        create_card('9', 'Hearts'),
        create_card('2', 'Spades')
    ]

    # Player with Kings
    kings_hand = [create_card('King', 'Hearts'), create_card('King', 'Clubs')] + community
    kings_score = game.evaluate_hand(kings_hand)

    # Player with 7s
    sevens_hand = [create_card('7', 'Hearts'), create_card('7', 'Clubs')] + community
    sevens_score = game.evaluate_hand(sevens_hand)

    print(f'Kings pair score: {kings_score}')
    print(f'Sevens pair score: {sevens_score}')
    print(f'Have eval7: {game.HAVE_EVAL7}')

    if game.HAVE_EVAL7:
        kings_wins = kings_score < sevens_score
        print(f'Kings < Sevens (eval7 lower is better): {kings_wins}')
    else:
        kings_wins = kings_score > sevens_score
        print(f'Kings > Sevens (fallback higher is better): {kings_wins}')

    print(f'Kings should win: {kings_wins}')
    return kings_wins

if __name__ == "__main__":
    test_kings_vs_sevens()
