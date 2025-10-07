#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import the game modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pykah.game as game
import pydealer

def create_card(value, suit):
    return pydealer.Card(value, suit)

def analyze_specific_hands():
    print("Analyzing specific hands in detail...")

    # Test case 2: Same pair different kickers
    print("\n=== Same pair different kickers case ===")
    community_cards2 = [
        create_card('2', 'Spades'), create_card('3', 'Diamonds'), create_card('4', 'Clubs'),
        create_card('5', 'Hearts'), create_card('6', 'Spades')
    ]

    # 8s with Ace kicker: 8H, AC, 2S, 3D, 4C, 5H, 6S
    eights_ace_hand = [create_card('8', 'Hearts'), create_card('Ace', 'Clubs')] + community_cards2

    print("8s with Ace hand:")
    for card in eights_ace_hand:
        print(f"  {card.value} of {card.suit}")

    # Check what values this gives us
    value_map = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
    }
    values = [value_map[card.value] for card in eights_ace_hand]
    print(f"Numeric values: {sorted(values)}")

    unique_values = sorted(set(values))
    print(f"Unique values: {unique_values}")

    # Check if there's a straight
    if len(unique_values) >= 5:
        for i in range(len(unique_values) - 4):
            if unique_values[i+4] - unique_values[i] == 4:
                print(f"STRAIGHT DETECTED: {unique_values[i]} to {unique_values[i+4]}")
                break

    # This should NOT be a straight - we have 2,3,4,5,6,8,14
    # The consecutive run is 2,3,4,5,6 which IS a straight!
    # But the player has an 8, not a 7, so they're not using the straight

if __name__ == "__main__":
    analyze_specific_hands()
