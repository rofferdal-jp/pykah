import pydealer
from pydealer.const import POKER_RANKS

# Mapping helpers to convert pydealer Card to eval7 notation
VALUE_MAP = {
    '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    '10': 'T', 'Jack': 'J', 'Queen': 'Q', 'King': 'K', 'Ace': 'A'
}
SUIT_MAP = {
    'Spades': 's', 'Hearts': 'h', 'Diamonds': 'd', 'Clubs': 'c'
}

def evaluate_hand(cards):
    # Simple evaluation instead of using a library
    return __simply_evaluate_poker_hand(cards)

def __simply_evaluate_poker_hand(cards):
    from collections import Counter

    # Convert card values to numeric for comparison
    value_map = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
    }

    # Get numeric values and suits
    values = [value_map[card.value] for card in cards]
    suits = [card.suit for card in cards]

    # Count occurrences of each value
    value_counts = Counter(values)
    counts = sorted(value_counts.values(), reverse=True)

    # Sort values by count (for ties) then by value
    sorted_by_count = sorted(value_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

    # Check for flush
    suit_counts = Counter(suits)
    is_flush = max(suit_counts.values()) >= 5
    flush_suit = None
    if is_flush:
        for suit, count in suit_counts.items():
            if count >= 5:
                flush_suit = suit
                break

    # Check for straight - need exactly 5 consecutive cards
    unique_values = sorted(set(values))
    is_straight = False
    straight_high = 0

    # Check for regular straight - need 5 consecutive unique values
    if len(unique_values) >= 5:
        for i in range(len(unique_values) - 4):
            if unique_values[i+4] - unique_values[i] == 4:
                is_straight = True
                straight_high = unique_values[i+4]
                break

    # Check for A-2-3-4-5 straight (wheel) - special case
    if set([14, 2, 3, 4, 5]).issubset(set(values)):
        is_straight = True
        straight_high = 5  # In wheel, 5 is the high card

    # Hand rankings (higher number = better hand)
    if is_straight and is_flush:
        # Check if the straight uses flush cards
        flush_values = sorted([v for i, v in enumerate(values) if suits[i] == flush_suit])
        if len(flush_values) >= 5:
            # Check if we have a straight flush
            flush_unique = sorted(set(flush_values))
            straight_flush = False
            sf_high = 0

            if len(flush_unique) >= 5:
                for i in range(len(flush_unique) - 4):
                    if flush_unique[i+4] - flush_unique[i] == 4:
                        straight_flush = True
                        sf_high = flush_unique[i+4]
                        break

                # Check for wheel in flush
                if set([14, 2, 3, 4, 5]).issubset(set(flush_values)):
                    straight_flush = True
                    sf_high = 5

            if straight_flush:
                if sf_high == 14:  # Royal flush
                    return (9, 14)
                else:  # Straight flush
                    return (8, sf_high)

    # Check individual hand types
    if counts == [4, 1, 1, 1] or counts == [4, 2, 1] or counts == [4, 3]:  # Four of a kind
        quad_value = sorted_by_count[0][0]
        kickers = sorted([item[0] for item in sorted_by_count[1:]], reverse=True)
        return (7, quad_value, *kickers)

    elif counts == [3, 2] or counts == [3, 2, 1, 1] or counts == [3, 2, 2]:  # Full house
        trips_value = sorted_by_count[0][0]
        pair_value = sorted_by_count[1][0]
        return (6, trips_value, pair_value)

    elif is_flush:  # Flush
        flush_values = sorted([v for i, v in enumerate(values) if suits[i] == flush_suit], reverse=True)[:5]
        return (5, *flush_values)

    elif is_straight:  # Straight
        return (4, straight_high)

    elif counts == [3, 1, 1, 1, 1] or counts == [3, 1, 1, 1]:  # Three of a kind
        trips_value = sorted_by_count[0][0]
        kickers = sorted([item[0] for item in sorted_by_count[1:]], reverse=True)[:2]
        return (3, trips_value, *kickers)

    # Two pair detection
    elif len([v for v, cnt in value_counts.items() if cnt == 2]) >= 2:
        pairs = sorted([v for v, cnt in value_counts.items() if cnt == 2], reverse=True)
        high_pair = pairs[0]
        low_pair = pairs[1]
        # Kicker is the highest remaining value not part of the two pairs
        remaining_values = [v for v in value_counts.keys() if v not in (high_pair, low_pair)]
        kicker = max(remaining_values) if remaining_values else 0
        return (2, high_pair, low_pair, kicker)

    # One pair
    elif counts == [2, 1, 1, 1, 1, 1] or counts == [2, 1, 1, 1, 1] or counts == [2, 1, 1, 1]:  # One pair
        pair_value = sorted_by_count[0][0]
        kickers = sorted([item[0] for item in sorted_by_count[1:]], reverse=True)[:3]
        return (1, pair_value, *kickers)

    else:  # High card
        high_cards = sorted(values, reverse=True)[:5]
        return (0, *high_cards)

# Very simple heuristic for hand strength
# Returns a float between 0 and 1 indicating hand strength
# This is a naive implementation and can be improved
def evaluate_hand_strength(community_cards, hole_cards) -> float:
    cards = hole_cards + community_cards
    if len(cards) >= 5:
        # check for any pair in combined cards
        ranks = [c.value for c in cards]
        from collections import Counter
        cnt = Counter(ranks)
        if any(v >= 2 for v in cnt.values()):
            return 0.8
        return 0.3
    else:
        # preflop heuristic: pocket pair strong, high cards moderate
        v0 = hole_cards[0].value if len(hole_cards) > 0 else None
        v1 = hole_cards[1].value if len(hole_cards) > 1 else None
        if v0 and v1:
            if v0 == v1:
                return 0.85
            if v0 in ("Ace", "King") or v1 in ("Ace", "King"):
                return 0.6
        return 0.35

def name_winning_hand(seven_cards) -> str:
    # _evaluate_poker_hand_fallback returns tuple with hand_rank as first element
    try:
        rank = __simply_evaluate_poker_hand(seven_cards)[0]
    except Exception:
        rank = None

    if rank >= 8:
        hand_name = 'Straight Flush'
    elif rank == 7:
        hand_name = 'Four of a Kind'
    elif rank == 6:
        hand_name = 'Full House'
    elif rank == 5:
        hand_name = 'Flush'
    elif rank == 4:
        hand_name = 'Straight'
    elif rank == 3:
        hand_name = 'Three of a Kind'
    elif rank == 2:
        hand_name = 'Two Pair'
    elif rank == 1:
        hand_name = 'Pair'
    else:
        hand_name = 'High Card'
    return hand_name
