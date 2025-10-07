#!/usr/bin/env python3

import sys
import os

import pykah.game_logic.cards

# Add the parent directory to the path so we can import the game modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pykah.game as game
import pydealer

def create_card(value, suit):
    return pydealer.Card(value, suit)

def debug_hand_evaluation():
    print("Debugging hand evaluation issues...")

    # Test 1: Full house vs flush
    print("\n1. Testing full house vs flush:")
    community_cards = [
        create_card('7', 'Hearts'), create_card('7', 'Spades'), create_card('King', 'Hearts'),
        create_card('Queen', 'Hearts'), create_card('Jack', 'Hearts')
    ]

    # Player with full house (7s full of Kings)
    full_house_hand = [create_card('7', 'Clubs'), create_card('King', 'Spades')] + community_cards
    full_house_score = pykah.game_logic.cards.evaluate_hand(full_house_hand)

    # Player with flush (hearts)
    flush_hand = [create_card('10', 'Hearts'), create_card('9', 'Hearts')] + community_cards
    flush_score = pykah.game_logic.cards.evaluate_hand(flush_hand)

    print(f"Full house score: {full_house_score}")
    print(f"Flush score: {flush_score}")
    print(f"Full house > Flush: {full_house_score > flush_score}")

    # Test 2: Same pair different kickers
    print("\n2. Testing same pair different kickers:")
    community_cards2 = [
        create_card('2', 'Spades'), create_card('3', 'Diamonds'), create_card('4', 'Clubs'),
        create_card('5', 'Hearts'), create_card('6', 'Spades')
    ]

    # Both players have pair of 8s, but different kickers
    eights_ace_hand = [create_card('8', 'Hearts'), create_card('Ace', 'Clubs')] + community_cards2
    eights_king_hand = [create_card('8', 'Spades'), create_card('King', 'Diamonds')] + community_cards2

    eights_ace_score = pykah.game_logic.cards.evaluate_hand(eights_ace_hand)
    eights_king_score = pykah.game_logic.cards.evaluate_hand(eights_king_hand)

    print(f"8s with Ace score: {eights_ace_score}")
    print(f"8s with King score: {eights_king_score}")
    print(f"8s+Ace > 8s+King: {eights_ace_score > eights_king_score}")

    # Test 3: Pocket pairs on board with trips
    print("\n3. Testing pocket pairs on board with trips:")
    community_cards3 = [
        create_card('Ace', 'Spades'), create_card('King', 'Diamonds'), create_card('Queen', 'Clubs'),
        create_card('10', 'Hearts'), create_card('9', 'Spades')
    ]

    # Aces (should make trips)
    aces_hand = [create_card('Ace', 'Hearts'), create_card('Ace', 'Clubs')] + community_cards3
    aces_score = pykah.game_logic.cards.evaluate_hand(aces_hand)

    # Jacks (just a pair)
    jacks_hand = [create_card('Jack', 'Hearts'), create_card('Jack', 'Clubs')] + community_cards3
    jacks_score = pykah.game_logic.cards.evaluate_hand(jacks_hand)

    print(f"Aces score: {aces_score}")
    print(f"Jacks score: {jacks_score}")
    print(f"Aces > Jacks: {aces_score > jacks_score}")

if __name__ == "__main__":
    debug_hand_evaluation()
