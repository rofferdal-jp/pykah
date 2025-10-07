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
    use a simplified high-card based score (sufficient for initial testing).
    """
    if HAVE_EVAL7:
        # eval7 expects strings like 'As', and has an evaluator: eval7.evaluate
        eval_cards = [eval7.Card(card_to_eval7_str(c)) for c in cards]
        # Build Deck/Hand for evaluator; eval7 evaluate takes list of card objects
        # For Hold'em: evaluate 7-card best-hand score as integer (lower is better in eval7)
        score = eval7.evaluate(eval_cards)
        return score
    else:
        # Simple fallback: sort by card value ranks and produce a tuple
        rank_values = POKER_RANKS['values']
        numeric = sorted([rank_values.get(c.value, 0) for c in cards], reverse=True)
        # return tuple for comparisons
        return tuple(numeric)


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
        players = self.board.players
        num = self.board.num_players

        folded = set()
        all_in = set()

        # Track players with chips > 0 as active candidates
        for i, p in enumerate(players):
            if p.chip_stack <= 0:
                all_in.add(i)

        current_bet = self.board.current_bet

        # Order of action: starting_index, starting_index+1, ... wrapping
        idx = starting_index
        last_raiser = None
        # players_needed_to_act: when becomes zero and no new raises, round ends
        players_to_act = set(i for i in range(num) if i not in folded and players[i].chip_stack > 0)

        # We'll loop until each active non-all-in player has had chance to match current_bet
        while True:
            p = players[idx]
            if idx not in folded and idx not in all_in and p.chip_stack > 0:
                to_call = current_bet - contributions.get(idx, 0)
                if p.is_human:
                    # Prompt for action
                    prompt = f"Your turn. To call: {to_call}. Options: fold(f), check(k), call(c), raise(r amount), allin(a)"
                    # Pass the board so the prompt window shows the table and hole cards
                    action = prompt_input(prompt, "c", numeric=False, board=self.board)
                    action = action.strip().lower()
                    if action in ("f", "fold"):
                        folded.add(idx)
                    elif action in ("k", "check"):
                        if to_call > 0:
                            # invalid, treat as call
                            pay = min(p.chip_stack, to_call)
                            p.chip_stack -= pay
                            contributions[idx] += pay
                            self.board.pot += pay
                            if p.chip_stack == 0:
                                all_in.add(idx)
                        # else nothing
                    elif action in ("c", "call"):
                        pay = min(p.chip_stack, to_call)
                        p.chip_stack -= pay
                        contributions[idx] += pay
                        self.board.pot += pay
                        if p.chip_stack == 0:
                            all_in.add(idx)
                    elif action.startswith("r") or action.startswith("raise"):
                        parts = action.split()
                        amount = None
                        if len(parts) > 1:
                            try:
                                amount = int(parts[1])
                            except Exception:
                                amount = None
                        if amount is None:
                            amount = self.min_raise
                        # total new contribution should be contributions[idx] + to_call + amount
                        pay = min(p.chip_stack, to_call + amount)
                        p.chip_stack -= pay
                        contributions[idx] += pay
                        current_bet = contributions[idx]
                        self.board.current_bet = current_bet
                        self.board.pot += pay
                        last_raiser = idx
                        if p.chip_stack == 0:
                            all_in.add(idx)
                    elif action in ("a", "allin"):
                        pay = p.chip_stack
                        p.chip_stack = 0
                        contributions[idx] += pay
                        if contributions[idx] > current_bet:
                            current_bet = contributions[idx]
                            self.board.current_bet = current_bet
                            last_raiser = idx
                        self.board.pot += pay
                        all_in.add(idx)
                    else:
                        # default to call
                        pay = min(p.chip_stack, to_call)
                        p.chip_stack -= pay
                        contributions[idx] += pay
                        self.board.pot += pay
                        if p.chip_stack == 0:
                            all_in.add(idx)
                else:
                    # Simple AI: evaluate hand strength roughly
                    ai_strength = self.estimate_hand_strength(idx)
                    # heuristic thresholds
                    if to_call <= 0:
                        # can check
                        if ai_strength > 0.7 and p.chip_stack > self.min_raise:
                            # raise
                            amount = min(self.min_raise * 2, p.chip_stack)
                            pay = min(p.chip_stack, amount)
                            p.chip_stack -= pay
                            contributions[idx] += pay
                            current_bet = contributions[idx]
                            self.board.current_bet = current_bet
                            self.board.pot += pay
                            last_raiser = idx
                            if p.chip_stack == 0:
                                all_in.add(idx)
                        else:
                            # check
                            pass
                    else:
                        # need to call or fold
                        if ai_strength > 0.5:
                            pay = min(p.chip_stack, to_call)
                            p.chip_stack -= pay
                            contributions[idx] += pay
                            self.board.pot += pay
                            if p.chip_stack == 0:
                                all_in.add(idx)
                        else:
                            folded.add(idx)
            # Move to next player
            idx = (idx + 1) % num

            # Termination conditions:
            # If only one non-folded player remains -> round ends early
            active = [i for i in range(num) if i not in folded]
            if len(active) <= 1:
                break
            # If every non-folded, non-all-in player's contribution equals current_bet, and
            # no one can/has raised further -> end round
            waiting = [i for i in active if i not in all_in and contributions.get(i, 0) < current_bet]
            if not waiting:
                break

        active_players = [i for i in range(num) if i not in folded]
        return contributions, active_players

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
        for i in active_players:
            p = self.board.players[i]
            seven = p.hole_cards + self.board.community_cards
            score = evaluate_hand(seven)
            if best_score is None or score < best_score:
                best_score = score
                winners = [i]
            elif score == best_score:
                winners.append(i)

        # Split pot equally among winners
        if winners:
            share = self.board.pot // len(winners)
            for w in winners:
                self.board.players[w].chip_stack += share
        # Reset pot
        self.board.pot = 0
        return winners

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

        # Flop
        self.deal_community(3)
        # betting starting at small blind (dealer+1)
        start = (self.board.dealer_index + 1) % num
        contributions, active = self.betting_round(start, contributions)
        if len(active) <= 1:
            winners = active
            self.resolve_showdown(winners)
            return winners

        # Turn
        self.deal_community(1)
        contributions, active = self.betting_round(start, contributions)
        if len(active) <= 1:
            winners = active
            self.resolve_showdown(winners)
            return winners

        # River
        self.deal_community(1)
        contributions, active = self.betting_round(start, contributions)
        if len(active) <= 1:
            winners = active
            self.resolve_showdown(winners)
            return winners

        # Showdown
        winners = self.resolve_showdown(active)
        return winners
