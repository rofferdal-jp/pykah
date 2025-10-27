# pykah
A simple 5-card draw poker game built with Python and Pygame

## Description
This is a simple implementation of 5-card draw poker where you play against a dealer. The game evaluates poker hands and determines the winner based on standard poker hand rankings.

## Requirements
- Python 3.x
- pygame

## Installation
1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## How to Play
Run the game:
```bash
python poker.py
```

### Game Rules
1. Click **DEAL** to start a new game
2. You and the dealer each receive 5 cards
3. Click on cards in your hand to select them for replacement (they will turn green)
4. Click **DRAW** to replace your selected cards with new ones from the deck
5. The dealer's cards are revealed and hands are compared
6. The player with the better poker hand wins!
7. Click **NEW GAME** to play again

### Poker Hand Rankings (highest to lowest)
- Straight Flush
- Four of a Kind
- Full House
- Flush
- Straight
- Three of a Kind
- Two Pair
- One Pair
- High Card

## Features
- Simple, intuitive interface
- Standard 52-card deck
- Automatic hand evaluation
- Visual card selection
- Clear display of results and hand rankings
