"""AI player decision logic for poker betting rounds.

Extracted from Game.betting_round to keep game.py lean and focused on flow.
All functions here mutate the passed-in game/board state directly, mirroring the original in-place logic.
"""
from __future__ import annotations
from typing import Set, Dict
from collections import defaultdict

# AI decision thresholds & sizing constants
AI_RAISE_PREFLOP_THRESHOLD = 0.7      # Was hardcoded > 0.7
AI_ALLIN_SHORT_STACK_THRESHOLD = 0.6  # Was > 0.6 when short-stacked and facing a bet
AI_RERAISE_STRONG_THRESHOLD = 0.8     # Was > 0.8 to reraise after a bet
AI_CALL_MIN_THRESHOLD = 0.4           # Was > 0.4 to justify a call
AI_RAISE_MULTIPLIER = 2               # Was *2 for raise sizing heuristic

__all__ = [
    "AI_RAISE_PREFLOP_THRESHOLD",
    "AI_ALLIN_SHORT_STACK_THRESHOLD",
    "AI_RERAISE_STRONG_THRESHOLD",
    "AI_CALL_MIN_THRESHOLD",
    "AI_RAISE_MULTIPLIER",
    "ai_take_action",
]

def ai_take_action(game, idx: int, to_call: int, contributions: Dict[int, int], current_bet: int,
                   has_acted: Set[int], all_in: Set[int], folded: Set[int]) -> int:
    """Execute AI decision logic for a single player action.

    Parameters:
        game: Game instance (provides board, min_raise, strength eval)
        idx: player seat index
        to_call: chips needed to call current bet
        contributions: mapping of player index -> chips committed this round
        current_bet: current highest contribution to match
        has_acted: set of players who have acted this betting round
        all_in: set of indices that are all-in already
        folded: set of indices that have folded

    Returns:
        Possibly updated current_bet (if raise/all-in increases it)
    """
    board = game.board
    players = board.players
    p = players[idx]

    ai_strength = game.estimate_hand_strength(idx)

    # CASE 1: Nothing to call yet
    if to_call <= 0:
        if ai_strength > AI_RAISE_PREFLOP_THRESHOLD and p.chip_stack >= game.min_raise:
            # Raise size heuristic: min_raise * multiplier (capped by stack)
            amount = min(game.min_raise * AI_RAISE_MULTIPLIER, p.chip_stack)
            pay = min(p.chip_stack, amount)
            p.chip_stack -= pay
            contributions[idx] += pay
            current_bet = contributions[idx]
            board.current_bet = current_bet
            board.pot += pay
            # New bet means all other players must respond again
            has_acted.clear()
            has_acted.add(idx)
            if p.chip_stack == 0:
                all_in.add(idx)
            board.last_actions[idx] = "raise"
        else:
            board.last_actions[idx] = "check"
        board.current_round_contributions = dict(contributions)
        return current_bet

    # CASE 2: Facing a bet
    # Short stack (cannot afford full call)
    if p.chip_stack < to_call:
        if ai_strength > AI_ALLIN_SHORT_STACK_THRESHOLD:
            pay = p.chip_stack
            p.chip_stack = 0
            contributions[idx] += pay
            if contributions[idx] > current_bet:
                current_bet = contributions[idx]
                board.current_bet = current_bet
                has_acted.clear()
                has_acted.add(idx)
            board.pot += pay
            all_in.add(idx)
            board.last_actions[idx] = "all-in"
        else:
            folded.add(idx)
            board.folded_players.add(idx)
            board.last_actions[idx] = "fold"
        board.current_round_contributions = dict(contributions)
        return current_bet

    # Can afford to call
    if ai_strength > AI_RERAISE_STRONG_THRESHOLD and p.chip_stack > to_call + game.min_raise:
        # Raise
        raise_amount = min(game.min_raise * AI_RAISE_MULTIPLIER, p.chip_stack - to_call)
        pay = min(p.chip_stack, to_call + raise_amount)
        p.chip_stack -= pay
        contributions[idx] += pay
        current_bet = contributions[idx]
        board.current_bet = current_bet
        board.pot += pay
        has_acted.clear()
        has_acted.add(idx)
        if p.chip_stack == 0:
            all_in.add(idx)
        board.last_actions[idx] = "raise"
    elif ai_strength > AI_CALL_MIN_THRESHOLD:
        # Call
        pay = min(p.chip_stack, to_call)
        p.chip_stack -= pay
        contributions[idx] += pay
        board.pot += pay
        if p.chip_stack == 0:
            all_in.add(idx)
        board.last_actions[idx] = "call"
    else:
        # Fold
        folded.add(idx)
        board.folded_players.add(idx)
        board.last_actions[idx] = "fold"

    board.current_round_contributions = dict(contributions)
    return current_bet

