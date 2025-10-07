import random
from collections import defaultdict

import pydealer
from pydealer.const import POKER_RANKS

from pykah.pokah_board import Board
from pykah.player import Player
from pykah.init_prompt import prompt_input

# Try to import eval7 for hand evaluation; otherwise use a simple fallback
try:
    import eval7
    HAVE_EVAL7 = True
except Exception:
    HAVE_EVAL7 = False

# Mapping helpers to convert pydealer Card to eval7 notation
VALUE_MAP = {
    '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    '10': 'T', 'Jack': 'J', 'Queen': 'Q', 'King': 'K', 'Ace': 'A'
}
SUIT_MAP = {
    'Spades': 's', 'Hearts': 'h', 'Diamonds': 'd', 'Clubs': 'c'
}


def card_to_eval7_str(card):
    """Convert a pydealer.Card to eval7 two-char string like 'As' or 'Td'."""
    v = VALUE_MAP.get(card.value, card.value[0].upper())
    s = SUIT_MAP.get(card.suit, card.suit[0].lower())
    return v + s


def evaluate_hand(cards):
    """Return an integer score for the best 5-card poker hand among given cards.
    If eval7 is available, use it for accurate Texas Hold'em evaluation. Otherwise
    use a proper poker hand evaluation.
    """
    if HAVE_EVAL7:
        # eval7 expects strings like 'As', and has an evaluator: eval7.evaluate
        eval_cards = [eval7.Card(card_to_eval7_str(c)) for c in cards]
        # Build Deck/Hand for evaluator; eval7 evaluate takes list of card objects
        # For Hold'em: evaluate 7-card best-hand score as integer (lower is better in eval7)
        score = eval7.evaluate(eval_cards)
        return score
    else:
        # Proper poker hand evaluation fallback
        return _evaluate_poker_hand_fallback(cards)


def _evaluate_poker_hand_fallback(cards):
    """Fallback poker hand evaluation when eval7 is not available.
    Returns a tuple where higher values indicate better hands.
    Format: (hand_rank, primary_value, secondary_value, kickers...)
    """
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


class Game:
    def __init__(self, board: Board):
        self.board = board
        self.deck = board.deck
        self.min_raise = board.big_blind or 10

    def reset_hand_state(self):
        self.board.reset_for_new_hand()
        # Rebuild deck and shuffle
        self.board.deck = pydealer.Deck(ranks=POKER_RANKS)
        self.board.deck.shuffle()
        self.deck = self.board.deck

        # Initialize contribution tracking for proper chip conservation
        self.board.previous_contributions = {}

    def rotate_button(self):
        self.board.dealer_index = (self.board.dealer_index + 1) % self.board.num_players

    def post_blinds(self):
        sb = max(1, self.board.big_blind // 2)
        bb = self.board.big_blind
        num = self.board.num_players
        small_index = (self.board.dealer_index + 1) % num
        big_index = (self.board.dealer_index + 2) % num
        players = self.board.players

        # Deduct blinds respecting players' stacks
        def take(idx, amt):
            p = players[idx]
            taken = min(amt, p.chip_stack)
            p.chip_stack -= taken
            return taken

        sb_taken = take(small_index, sb)
        bb_taken = take(big_index, bb)
        contributions = defaultdict(int)
        contributions[small_index] += sb_taken
        contributions[big_index] += bb_taken
        self.board.current_bet = bb_taken
        self.board.pot += sb_taken + bb_taken
        return contributions

    def deal_hole_cards(self):
        # Deal 2 hole cards to each player
        for p in self.board.players:
            hand = self.deck.deal(2)
            # stack returned is a pydealer.Stack; convert to list of Card
            p.hole_cards = list(hand.cards)

    def deal_community(self, n):
        # Burn 1 card for realism (optional)
        _ = self.deck.deal(1)
        cards = self.deck.deal(n)
        self.board.community_cards.extend(list(cards.cards))

    def betting_round(self, starting_index, contributions=None):
        """Run a betting round; contributions is a dict of prior contributions in this hand.
        Returns updated contributions and list of active player indices (not folded).
        Human player is prompted via prompt_input when it's their turn.
        AI uses a simple heuristic.
        """
        if contributions is None:
            contributions = defaultdict(int)

        # Store initial pot amount to track what was added this round
        initial_pot = self.board.pot

        # Sync contributions to board for visual display
        self.board.current_round_contributions = dict(contributions)

        players = self.board.players
        num = self.board.num_players

        folded = set(self.board.folded_players)  # Persist folds from earlier rounds in the same hand
        all_in = set()

        # Track players with chips > 0 as active candidates
        for i, p in enumerate(players):
            if p.chip_stack <= 0:
                all_in.add(i)

        current_bet = self.board.current_bet

        # Order of action: starting_index, starting_index+1, ... wrapping
        idx = starting_index
        last_raiser = None

        # Track who has acted in this betting round
        has_acted = set()

        # Active players who can make decisions (not folded, not all-in)
        active_decision_makers = [i for i in range(num)
                                if i not in folded and i not in all_in and players[i].chip_stack > 0]

        # We'll loop until all active players have had a chance to act and match the current bet
        while True:
            p = players[idx]

            # Only process players who are not folded, not all-in, and have chips
            if idx not in folded and idx not in all_in and p.chip_stack > 0:
                to_call = current_bet - contributions.get(idx, 0)

                if p.is_human:
                    # Update board contributions before prompting so display is current
                    self.board.current_round_contributions = dict(contributions)

                    # Determine valid actions based on current betting situation
                    valid_actions = []
                    action_descriptions = []

                    # Fold is always available (unless already all-in)
                    if p.chip_stack > 0:
                        valid_actions.append("fold(f)")
                        action_descriptions.append("fold(f)")

                    if to_call <= 0:
                        # No bet to call - can check
                        valid_actions.append("check(k)")
                        action_descriptions.append("check(k)")

                        # Can also raise if have chips
                        if p.chip_stack > 0:
                            valid_actions.append("raise(r amount)")
                            action_descriptions.append("raise(r amount)")
                    else:
                        # There's a bet to call
                        if p.chip_stack >= to_call:
                            # Can afford to call
                            valid_actions.append("call(c)")
                            action_descriptions.append(f"call(c) {to_call}")

                            # Can also raise if have chips left after calling
                            if p.chip_stack > to_call:
                                valid_actions.append("raise(r amount)")
                                action_descriptions.append("raise(r amount)")
                        # If can't afford full call, only fold or all-in available

                    # All-in is available if have chips
                    if p.chip_stack > 0:
                        valid_actions.append("allin(a)")
                        action_descriptions.append(f"allin(a) {p.chip_stack}")

                    # Create prompt with only valid actions
                    if to_call > 0:
                        prompt = f"Your turn. To call: {to_call}. Valid options: {', '.join(action_descriptions)}"
                    else:
                        prompt = f"Your turn. Valid options: {', '.join(action_descriptions)}"

                    # Pass the board so the prompt window shows the table and hole cards
                    action = prompt_input(prompt, "c" if to_call > 0 else "k", numeric=False, board=self.board)
                    action = action.strip().lower()

                    # Validate and process action
                    if action in ("f", "fold"):
                        if p.chip_stack > 0:  # Only allow fold if not already all-in
                            folded.add(idx)
                            self.board.folded_players.add(idx)
                            self.board.last_actions[idx] = "fold"
                        else:
                            # Invalid action - default to check/call
                            if to_call <= 0:
                                self.board.last_actions[idx] = "check"
                            else:
                                # Forced all-in
                                pay = p.chip_stack
                                p.chip_stack = 0
                                contributions[idx] += pay
                                all_in.add(idx)
                                self.board.last_actions[idx] = "all-in"
                    elif action in ("k", "check"):
                        if to_call <= 0:
                            # Valid check
                            self.board.last_actions[idx] = "check"
                        else:
                            # Invalid check when there's a bet - treat as call
                            pay = min(p.chip_stack, to_call)
                            p.chip_stack -= pay
                            contributions[idx] += pay
                            self.board.pot += pay
                            if p.chip_stack == 0:
                                all_in.add(idx)
                            self.board.last_actions[idx] = "call"
                    elif action in ("c", "call"):
                        if to_call > 0:
                            pay = min(p.chip_stack, to_call)
                            p.chip_stack -= pay
                            contributions[idx] += pay
                            self.board.pot += pay
                            if p.chip_stack == 0:
                                all_in.add(idx)
                            self.board.last_actions[idx] = "call"
                        else:
                            # Invalid call when nothing to call - treat as check
                            self.board.last_actions[idx] = "check"
                    elif action.startswith("r") or action.startswith("raise"):
                        # Parse raise amount
                        parts = action.split()
                        amount = None
                        if len(parts) > 1:
                            try:
                                amount = int(parts[1])
                            except Exception:
                                amount = None
                        if amount is None:
                            amount = self.min_raise

                        # Validate raise is legal
                        total_needed = to_call + amount
                        if p.chip_stack >= total_needed and amount >= self.min_raise:
                            pay = min(p.chip_stack, total_needed)
                            p.chip_stack -= pay
                            contributions[idx] += pay
                            current_bet = contributions[idx]
                            self.board.current_bet = current_bet
                            self.board.pot += pay
                            last_raiser = idx
                            # Reset has_acted since there's a new bet everyone needs to respond to
                            # but keep the current player as acted since they just raised
                            has_acted.clear()
                            has_acted.add(idx)
                            if p.chip_stack == 0:
                                all_in.add(idx)
                            self.board.last_actions[idx] = "raise"
                        else:
                            # Invalid raise - default to call or check
                            if to_call > 0:
                                pay = min(p.chip_stack, to_call)
                                p.chip_stack -= pay
                                contributions[idx] += pay
                                self.board.pot += pay
                                if p.chip_stack == 0:
                                    all_in.add(idx)
                                self.board.last_actions[idx] = "call"
                            else:
                                self.board.last_actions[idx] = "check"
                    elif action in ("a", "allin"):
                        if p.chip_stack > 0:
                            pay = p.chip_stack
                            p.chip_stack = 0
                            contributions[idx] += pay
                            if contributions[idx] > current_bet:
                                current_bet = contributions[idx]
                                self.board.current_bet = current_bet
                                last_raiser = idx
                                # Reset has_acted since there's a new bet everyone needs to respond to
                                has_acted.clear()
                                has_acted.add(idx)
                            self.board.pot += pay
                            all_in.add(idx)
                            self.board.last_actions[idx] = "all-in"
                        else:
                            # Already all-in, treat as check
                            self.board.last_actions[idx] = "check"
                    else:
                        # Invalid action - default to best legal action
                        if to_call <= 0:
                            self.board.last_actions[idx] = "check"
                        elif p.chip_stack >= to_call:
                            pay = min(p.chip_stack, to_call)
                            p.chip_stack -= pay
                            contributions[idx] += pay
                            self.board.pot += pay
                            if p.chip_stack == 0:
                                all_in.add(idx)
                            self.board.last_actions[idx] = "call"
                        else:
                            # Can't afford call, fold
                            folded.add(idx)
                            self.board.folded_players.add(idx)
                            self.board.last_actions[idx] = "fold"

                    # Update board contributions after human action
                    self.board.current_round_contributions = dict(contributions)
                else:
                    # AI player logic - follow proper Texas Hold'em rules
                    ai_strength = self.estimate_hand_strength(idx)

                    if to_call <= 0:
                        # No bet to call - can check or raise
                        if ai_strength > 0.7 and p.chip_stack >= self.min_raise:
                            # Strong hand - raise
                            amount = min(self.min_raise * 2, p.chip_stack)
                            pay = min(p.chip_stack, amount)
                            p.chip_stack -= pay
                            contributions[idx] += pay
                            current_bet = contributions[idx]
                            self.board.current_bet = current_bet
                            self.board.pot += pay
                            last_raiser = idx
                            # Reset has_acted since there's a new bet everyone needs to respond to
                            has_acted.clear()
                            has_acted.add(idx)
                            if p.chip_stack == 0:
                                all_in.add(idx)
                            self.board.last_actions[idx] = "raise"
                        else:
                            # Check with weaker hands or insufficient chips
                            self.board.last_actions[idx] = "check"
                    else:
                        # There's a bet to call - decide between fold, call, raise
                        if p.chip_stack < to_call:
                            # Can't afford full call
                            if ai_strength > 0.6:
                                # Good hand but short on chips - go all-in
                                pay = p.chip_stack
                                p.chip_stack = 0
                                contributions[idx] += pay
                                if contributions[idx] > current_bet:
                                    current_bet = contributions[idx]
                                    self.board.current_bet = current_bet
                                    last_raiser = idx
                                    # Reset has_acted since there's a new bet everyone needs to respond to
                                    has_acted.clear()
                                    has_acted.add(idx)
                            else:
                                # Weak hand and can't afford call - fold
                                folded.add(idx)
                                self.board.folded_players.add(idx)
                                self.board.last_actions[idx] = "fold"
                        else:
                            # Can afford to call
                            if ai_strength > 0.8 and p.chip_stack > to_call + self.min_raise:
                                # Very strong hand - raise
                                raise_amount = min(self.min_raise * 2, p.chip_stack - to_call)
                                pay = min(p.chip_stack, to_call + raise_amount)
                                p.chip_stack -= pay
                                contributions[idx] += pay
                                current_bet = contributions[idx]
                                self.board.current_bet = current_bet
                                self.board.pot += pay
                                last_raiser = idx
                                # Reset has_acted since there's a new bet everyone needs to respond to
                                has_acted.clear()
                                has_acted.add(idx)
                                if p.chip_stack == 0:
                                    all_in.add(idx)
                                self.board.last_actions[idx] = "raise"
                            elif ai_strength > 0.4:
                                # Decent hand - call
                                pay = min(p.chip_stack, to_call)
                                p.chip_stack -= pay
                                contributions[idx] += pay
                                self.board.pot += pay
                                if p.chip_stack == 0:
                                    all_in.add(idx)
                                self.board.last_actions[idx] = "call"
                            else:
                                # Weak hand - fold
                                folded.add(idx)
                                self.board.folded_players.add(idx)
                                self.board.last_actions[idx] = "fold"

                    # Update board contributions after AI action
                    self.board.current_round_contributions = dict(contributions)

                # Mark this player as having acted
                has_acted.add(idx)

            # Move to next player
            idx = (idx + 1) % num

            # Termination conditions:
            # 1. If only one non-folded player remains -> round ends early
            active = [i for i in range(num) if i not in folded]
            if len(active) <= 1:
                break

            # 2. Check if betting round is complete:
            # All active players (not folded, not all-in) have acted and either:
            # - All have equal contributions (no outstanding bets), OR
            # - All who can act have matched the current bet
            active_decision_makers = [i for i in range(num)
                                    if i not in folded and i not in all_in and players[i].chip_stack > 0]

            if not active_decision_makers:
                # No one left to make decisions
                break

            # Check if all active decision makers have acted
            all_have_acted = all(i in has_acted for i in active_decision_makers)

            # Check if all active players have matching contributions
            all_matched_bet = all(contributions.get(i, 0) == current_bet for i in active_decision_makers)

            if all_have_acted and all_matched_bet:
                break

        # Add all contributions from this betting round to the pot
        # NOTE: Chips are already added to pot during individual betting actions
        # No additional pot calculation needed here to avoid double-counting

        # Store contributions for next round
        self.board.previous_contributions = dict(contributions)

        # Clear current round contributions display after betting round
        self.board.current_round_contributions = {}

        active_players = [i for i in range(num) if i not in folded]
        return contributions, active_players

    def consolidate_bets_to_pot(self, contributions):
        """Ensure all bets from the betting round are properly transferred to the pot.
        This function verifies that all contributions have been added to the pot and
        clears the current round contributions display.
        """
        # Calculate total contributions this round
        total_contributions = sum(contributions.values())

        # The pot should already contain all contributions since we add them during betting
        # This is a safety check to ensure consistency
        if hasattr(self.board, 'pot_before_round'):
            expected_pot = self.board.pot_before_round + total_contributions
            if self.board.pot != expected_pot:
                # If there's a discrepancy, correct it
                self.board.pot = expected_pot

        # Clear current round contributions display after betting round
        # (Keep contributions dict for next round but clear display)
        self.board.current_round_contributions = {}

        # Store pot amount before next round for verification
        self.board.pot_before_round = self.board.pot

    def estimate_hand_strength(self, player_index):
        """Return a heuristic strength in [0,1] for the player's current hand.
        If eval7 exists, use evaluator to compute the rank among all possible boards (simple Monte Carlo could be added later).
        For now use a rough heuristic: pair or better -> strong; high card -> weak.
        """
        p = self.board.players[player_index]
        cards = p.hole_cards + self.board.community_cards
        if len(cards) >= 5:
            # Use evaluator if present
            if HAVE_EVAL7:
                # compute numeric score: lower is better in eval7; convert to inverse
                e_cards = [eval7.Card(card_to_eval7_str(c)) for c in cards]
                score = eval7.evaluate(e_cards)
                # transform into 0..1 (approx) using a large constant; lower -> stronger
                return 1.0 / (1 + score)
            else:
                # fallback: check for any pair in combined cards
                ranks = [c.value for c in cards]
                from collections import Counter
                cnt = Counter(ranks)
                if any(v >= 2 for v in cnt.values()):
                    return 0.8
                return 0.3
        else:
            # preflop heuristic: pocket pair strong, high cards moderate
            v0 = p.hole_cards[0].value if len(p.hole_cards) > 0 else None
            v1 = p.hole_cards[1].value if len(p.hole_cards) > 1 else None
            if v0 and v1:
                if v0 == v1:
                    return 0.85
                if v0 in ("Ace", "King") or v1 in ("Ace", "King"):
                    return 0.6
            return 0.35

    def resolve_showdown(self, active_players):
        """Evaluate hands among active_players (indices) and award pot to best player(s).
        This implementation uses a single pot; side pots are not yet implemented.
        """
        best_score = None
        winners = []

        # Set showdown mode for visual display
        self.board.showdown_mode = True
        self.board.showdown_players = active_players[:]

        for i in active_players:
            p = self.board.players[i]
            seven = p.hole_cards + self.board.community_cards
            score = evaluate_hand(seven)

            # Handle comparison based on evaluation method
            if HAVE_EVAL7:
                # eval7: lower score is better
                if best_score is None or score < best_score:
                    best_score = score
                    winners = [i]
                elif score == best_score:
                    winners.append(i)
            else:
                # fallback: higher score is better
                if best_score is None or score > best_score:
                    best_score = score
                    winners = [i]
                elif score == best_score:
                    winners.append(i)

        # Set winner information for display
        self.board.winners = winners[:]
        self.board.is_split_pot = len(winners) > 1

        # Determine human-readable winning hand type using fallback evaluator
        if winners:
            # Use the first winner to determine the hand type (all winners share the same ranking)
            winner_idx = winners[0]
            winner = self.board.players[winner_idx]
            seven = winner.hole_cards + self.board.community_cards
            # _evaluate_poker_hand_fallback returns tuple with hand_rank as first element
            try:
                rank = _evaluate_poker_hand_fallback(seven)[0]
            except Exception:
                rank = None

            if rank is None:
                self.board.winning_hand_type = ""
            else:
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
                self.board.winning_hand_type = hand_name

        # Split pot equally among winners with remainder handling to conserve chips
        if winners:
            total_pot = self.board.pot
            share = total_pot // len(winners)
            remainder = total_pot - share * len(winners)
            for idx, w in enumerate(winners):
                self.board.players[w].chip_stack += share
                # Distribute remainder chips to earliest winners by seat order (deterministic)
                if remainder > 0:
                    self.board.players[w].chip_stack += 1
                    remainder -= 1
        # Reset pot
        self.board.pot = 0
        self.board.hand_complete = True
        return winners

    def play(self):
        """Main game loop - play specified number of hands."""
        for _ in range(self.board.num_hands):
            # Each player posts an ante if configured
            if self.board.ante > 0:
                self.post_antes()

            # Start a new hand
            self.start_hand()

            # Rotate dealer button (skipped if only one player)
            if self.board.num_players > 1:
                self.rotate_button()

        # At end of game, determine overall winner(s) if multiple hands played
        if self.board.num_hands > 1:
            self.determine_overall_winner()

    def post_antes(self):
        """Collect antes from all players and add to pot.
        Antes are small forced bets posted by all players before the hand begins.
        """
        total_ante = 0
        for p in self.board.players:
            if p.chip_stack > 0:
                ante = min(self.board.ante, p.chip_stack)
                p.chip_stack -= ante
                total_ante += ante

        # Add total ante to pot
        self.board.pot += total_ante

    def determine_overall_winner(self):
        """Determine the overall winner(s) across multiple hands.
        This function identifies the player(s) with the most chips after the
        specified number of hands.
        """
        max_chips = 0
        winners = []

        for p in self.board.players:
            if p.chip_stack > max_chips:
                max_chips = p.chip_stack
                winners = [p]
            elif p.chip_stack == max_chips:
                winners.append(p)

        # Display overall winner(s)
        if winners:
            winner_names = ", ".join([w.name for w in winners])
            self.board.add_message(f"Overall winner(s): {winner_names} with {max_chips} chips each!")

    def start_hand(self, prompt_human=True):
        # Prepare new hand
        self.reset_hand_state()
        num = self.board.num_players
        players = self.board.players

        # Clear player hole cards
        for p in players:
            p.reset_for_new_hand()

        # NOTE: Do not rotate dealer automatically at hand start so player 0 can remain
        # at the dealer position (human sits on dealer button by default).

        # Post blinds
        contributions = self.post_blinds()

        # Deal hole cards
        self.deal_hole_cards()

        # Pre-flop betting: starting after big blind
        start = (self.board.dealer_index + 3) % num
        contributions, active = self.betting_round(start, contributions)
        if len(active) <= 1:
            winners = active
            self.resolve_showdown(winners)
            return winners

        # Flop - reset current bet for new betting round
        self.board.current_bet = 0
        # Reset contributions as chips from previous round are now committed to pot
        contributions = defaultdict(int)
        self.deal_community(3)
        # betting starting at small blind (dealer+1)
        start = (self.board.dealer_index + 1) % num
        contributions, active = self.betting_round(start, contributions)
        if len(active) <= 1:
            winners = active
            self.resolve_showdown(winners)
            return winners

        # Turn - reset current bet for new betting round
        self.board.current_bet = 0
        # Reset contributions as chips from previous round are now committed to pot
        contributions = defaultdict(int)
        self.deal_community(1)
        contributions, active = self.betting_round(start, contributions)
        if len(active) <= 1:
            winners = active
            self.resolve_showdown(winners)
            return winners

        # River - reset current bet for new betting round
        self.board.current_bet = 0
        # Reset contributions as chips from previous round are now committed to pot
        contributions = defaultdict(int)
        self.deal_community(1)
        contributions, active = self.betting_round(start, contributions)
        if len(active) <= 1:
            winners = active
            self.resolve_showdown(winners)
            return winners

        # Showdown
        winners = self.resolve_showdown(active)
        return winners
