from collections import defaultdict

import pydealer
from pydealer.const import POKER_RANKS

from pykah.game_logic.cards import evaluate_hand, evaluate_hand_strength, name_winning_hand
from pykah.pokah_board import Board
from pykah.init_prompt import prompt_input

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
        hole_cards = p.hole_cards
        community_cards = self.board.community_cards
        return evaluate_hand_strength(community_cards, hole_cards)

    def resolve_showdown(self, active_players):
        # Set showdown mode for visual display
        self.board.showdown_mode = True
        self.board.showdown_players = active_players[:]

        winners = self.determine_winners(active_players)

        # Set winner information for display
        self.board.winners = winners[:]
        self.board.is_split_pot = len(winners) > 1

        # Determine human-readable winning hand type using fallback evaluator
        if winners:
            # Use the first winner to determine the hand type (all winners share the same ranking)
            winner_idx = winners[0]
            winner = self.board.players[winner_idx]
            self.board.winning_hand_type = name_winning_hand(winner.hole_cards + self.board.community_cards)

        # Split pot equally among winners with remainder handling to conserve chips
        return self.pay_pot_to_winners(winners)

    def pay_pot_to_winners(self, winners):
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

    def determine_winners(self, active_players):
        winners = []
        best_score = None

        for i in active_players:
            p = self.board.players[i]
            seven = p.hole_cards + self.board.community_cards
            score = evaluate_hand(seven)

            # Compare hand scores to find winner(s)
            if best_score is None or score > best_score:
                best_score = score
                winners = [i]
            elif score == best_score:
                winners.append(i)
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
