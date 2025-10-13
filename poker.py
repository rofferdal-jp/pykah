"""
A simple 5-card draw poker game using pygame
"""
import pygame
import random
from collections import Counter

# Initialize pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GRAY = (128, 128, 128)

# Card dimensions
CARD_WIDTH = 60
CARD_HEIGHT = 90
CARD_SPACING = 10

# Font setup
pygame.font.init()
FONT = pygame.font.SysFont('Arial', 18)
TITLE_FONT = pygame.font.SysFont('Arial', 24, bold=True)


class Card:
    """Represents a playing card"""
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.rank_value = self.RANKS.index(rank)
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return self.__str__()


class Deck:
    """Represents a deck of playing cards"""
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        """Create a fresh deck of 52 cards"""
        self.cards = [Card(rank, suit) for suit in Card.SUITS for rank in Card.RANKS]
        self.shuffle()
    
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
    
    def deal(self, num=1):
        """Deal cards from the deck"""
        if num > len(self.cards):
            return []
        dealt_cards = self.cards[:num]
        self.cards = self.cards[num:]
        return dealt_cards


class Hand:
    """Represents a poker hand and evaluates it"""
    def __init__(self, cards):
        self.cards = cards
        self.rank_counts = Counter([card.rank for card in cards])
        self.suit_counts = Counter([card.suit for card in cards])
        self.rank_values = sorted([card.rank_value for card in cards], reverse=True)
    
    def is_flush(self):
        """Check if all cards have the same suit"""
        return len(self.suit_counts) == 1
    
    def is_straight(self):
        """Check if cards form a sequence"""
        if len(self.rank_counts) != 5:
            return False
        # Check regular straight
        if self.rank_values[0] - self.rank_values[4] == 4:
            return True
        # Check for A-2-3-4-5 (wheel/low straight)
        if self.rank_values == [12, 3, 2, 1, 0]:  # A(12), 5(3), 4(2), 3(1), 2(0)
            return True
        return False
    
    def get_hand_rank(self):
        """Evaluate the poker hand and return its rank"""
        counts = sorted(self.rank_counts.values(), reverse=True)
        
        is_flush = self.is_flush()
        is_straight = self.is_straight()
        
        if is_straight and is_flush:
            return (8, self.rank_values)  # Straight Flush
        elif counts == [4, 1]:
            return (7, self.rank_values)  # Four of a Kind
        elif counts == [3, 2]:
            return (6, self.rank_values)  # Full House
        elif is_flush:
            return (5, self.rank_values)  # Flush
        elif is_straight:
            return (4, self.rank_values)  # Straight
        elif counts == [3, 1, 1]:
            return (3, self.rank_values)  # Three of a Kind
        elif counts == [2, 2, 1]:
            return (2, self.rank_values)  # Two Pair
        elif counts == [2, 1, 1, 1]:
            return (1, self.rank_values)  # One Pair
        else:
            return (0, self.rank_values)  # High Card
    
    def get_hand_name(self):
        """Get the name of the poker hand"""
        rank, _ = self.get_hand_rank()
        names = [
            "High Card",
            "One Pair",
            "Two Pair",
            "Three of a Kind",
            "Straight",
            "Flush",
            "Full House",
            "Four of a Kind",
            "Straight Flush"
        ]
        return names[rank]


class PokerGame:
    """Main poker game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Simple Poker Game")
        self.clock = pygame.time.Clock()
        self.deck = Deck()
        self.player_cards = []
        self.dealer_cards = []
        self.selected_cards = []
        self.game_state = "start"  # start, playing, showdown
        self.running = True
        self.dealer_revealed = False
    
    def draw_card(self, card, x, y, face_up=True, selected=False):
        """Draw a single card on the screen"""
        # Draw card background
        color = GREEN if selected else WHITE
        pygame.draw.rect(self.screen, color, (x, y, CARD_WIDTH, CARD_HEIGHT))
        pygame.draw.rect(self.screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)
        
        if face_up:
            # Draw card value and suit
            suit_color = RED if card.suit in ['♥', '♦'] else BLACK
            rank_text = FONT.render(card.rank, True, suit_color)
            suit_text = FONT.render(card.suit, True, suit_color)
            
            # Position text
            self.screen.blit(rank_text, (x + 5, y + 5))
            self.screen.blit(suit_text, (x + 5, y + 25))
            
            # Draw small version in corner
            self.screen.blit(rank_text, (x + CARD_WIDTH - 20, y + CARD_HEIGHT - 30))
            self.screen.blit(suit_text, (x + CARD_WIDTH - 20, y + CARD_HEIGHT - 15))
        else:
            # Draw card back
            pygame.draw.rect(self.screen, BLUE, (x + 5, y + 5, CARD_WIDTH - 10, CARD_HEIGHT - 10))
    
    def draw_hand(self, cards, y, label, face_up=True):
        """Draw a hand of cards"""
        start_x = (WINDOW_WIDTH - (len(cards) * (CARD_WIDTH + CARD_SPACING))) // 2
        
        # Draw label
        label_text = TITLE_FONT.render(label, True, WHITE)
        self.screen.blit(label_text, (10, y - 30))
        
        # Draw cards
        for i, card in enumerate(cards):
            x = start_x + i * (CARD_WIDTH + CARD_SPACING)
            selected = i in self.selected_cards and label == "Your Hand"
            self.draw_card(card, x, y, face_up, selected)
    
    def deal_initial_hands(self):
        """Deal initial 5 cards to player and dealer"""
        self.deck.reset()
        self.player_cards = self.deck.deal(5)
        self.dealer_cards = self.deck.deal(5)
        self.selected_cards = []
        self.game_state = "playing"
        self.dealer_revealed = False
    
    def replace_cards(self):
        """Replace selected cards with new ones from deck"""
        for i in sorted(self.selected_cards, reverse=True):
            new_cards = self.deck.deal(1)
            if new_cards:  # Only replace if deck has cards
                self.player_cards[i] = new_cards[0]
        self.selected_cards = []
        self.game_state = "showdown"
        self.dealer_revealed = True
    
    def get_winner(self):
        """Determine the winner"""
        player_hand = Hand(self.player_cards)
        dealer_hand = Hand(self.dealer_cards)
        
        player_rank = player_hand.get_hand_rank()
        dealer_rank = dealer_hand.get_hand_rank()
        
        if player_rank > dealer_rank:
            return "Player wins!", player_hand.get_hand_name(), dealer_hand.get_hand_name()
        elif dealer_rank > player_rank:
            return "Dealer wins!", player_hand.get_hand_name(), dealer_hand.get_hand_name()
        else:
            return "It's a tie!", player_hand.get_hand_name(), dealer_hand.get_hand_name()
    
    def draw_button(self, text, x, y, width, height):
        """Draw a button and return its rect"""
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, WHITE, rect)
        pygame.draw.rect(self.screen, BLACK, rect, 2)
        
        button_text = FONT.render(text, True, BLACK)
        text_rect = button_text.get_rect(center=rect.center)
        self.screen.blit(button_text, text_rect)
        
        return rect
    
    def handle_card_click(self, pos):
        """Handle clicking on cards to select/deselect them"""
        if self.game_state != "playing":
            return
        
        start_x = (WINDOW_WIDTH - (len(self.player_cards) * (CARD_WIDTH + CARD_SPACING))) // 2
        y = 400
        
        for i in range(len(self.player_cards)):
            x = start_x + i * (CARD_WIDTH + CARD_SPACING)
            rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
            if rect.collidepoint(pos):
                if i in self.selected_cards:
                    self.selected_cards.remove(i)
                else:
                    self.selected_cards.append(i)
                break
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.screen.fill(GREEN)
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    
                    if self.game_state == "start":
                        deal_button = pygame.Rect(WINDOW_WIDTH // 2 - 60, WINDOW_HEIGHT // 2 - 25, 120, 50)
                        if deal_button.collidepoint(pos):
                            self.deal_initial_hands()
                    
                    elif self.game_state == "playing":
                        self.handle_card_click(pos)
                        
                        draw_button = pygame.Rect(WINDOW_WIDTH // 2 - 60, 520, 120, 40)
                        if draw_button.collidepoint(pos):
                            self.replace_cards()
                    
                    elif self.game_state == "showdown":
                        new_game_button = pygame.Rect(WINDOW_WIDTH // 2 - 60, 520, 120, 40)
                        if new_game_button.collidepoint(pos):
                            self.game_state = "start"
            
            # Drawing
            if self.game_state == "start":
                title = TITLE_FONT.render("5-Card Draw Poker", True, WHITE)
                self.screen.blit(title, (WINDOW_WIDTH // 2 - 100, 100))
                self.draw_button("DEAL", WINDOW_WIDTH // 2 - 60, WINDOW_HEIGHT // 2 - 25, 120, 50)
                
                instructions = [
                    "Instructions:",
                    "1. Click DEAL to start",
                    "2. Click cards to select/deselect",
                    "3. Click DRAW to replace selected cards",
                    "4. Try to beat the dealer!"
                ]
                for i, line in enumerate(instructions):
                    text = FONT.render(line, True, WHITE)
                    self.screen.blit(text, (WINDOW_WIDTH // 2 - 120, 300 + i * 25))
            
            elif self.game_state == "playing":
                # Draw dealer's hand (face down)
                self.draw_hand(self.dealer_cards, 50, "Dealer's Hand", False)
                
                # Draw player's hand (face up)
                self.draw_hand(self.player_cards, 400, "Your Hand", True)
                
                # Draw button
                self.draw_button("DRAW", WINDOW_WIDTH // 2 - 60, 520, 120, 40)
                
                # Instructions
                inst_text = FONT.render("Click cards to select, then click DRAW", True, WHITE)
                self.screen.blit(inst_text, (WINDOW_WIDTH // 2 - 160, 560))
            
            elif self.game_state == "showdown":
                # Draw both hands face up
                self.draw_hand(self.dealer_cards, 50, "Dealer's Hand", True)
                self.draw_hand(self.player_cards, 400, "Your Hand", True)
                
                # Show results
                winner, player_hand, dealer_hand = self.get_winner()
                result_text = TITLE_FONT.render(winner, True, WHITE)
                self.screen.blit(result_text, (WINDOW_WIDTH // 2 - 100, 250))
                
                player_hand_text = FONT.render(f"Your hand: {player_hand}", True, WHITE)
                dealer_hand_text = FONT.render(f"Dealer's hand: {dealer_hand}", True, WHITE)
                self.screen.blit(player_hand_text, (WINDOW_WIDTH // 2 - 120, 290))
                self.screen.blit(dealer_hand_text, (WINDOW_WIDTH // 2 - 120, 315))
                
                # New game button
                self.draw_button("NEW GAME", WINDOW_WIDTH // 2 - 60, 520, 120, 40)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()


def main():
    """Main entry point"""
    game = PokerGame()
    game.run()


if __name__ == "__main__":
    main()
