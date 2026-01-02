"""Game engine for Citidle.

This module manages the core game loop:
- Start a new game (get today's target city)
- Accept guesses and compute proximity feedback
- Track guess history
- Detect win condition

TODO: Implement full game state management (sessions, persistence, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from game.daily import get_daily_city
from game.distance import (
    CityRecord,
    build_city_index,
    distance_between_records,
    find_cities,
)

# Color tiers based on distance (miles). Closer = darker/warmer color.
# These thresholds can be tuned for difficulty.
DISTANCE_TIERS: List[Tuple[float, str]] = [
    (0, "correct"),      # exact match
    (50, "very_hot"),    # < 50 miles
    (150, "hot"),        # < 150 miles
    (300, "warm"),       # < 300 miles
    (600, "cool"),       # < 600 miles
    (1000, "cold"),      # < 1000 miles
    (float("inf"), "very_cold"),  # >= 1000 miles
]


def get_color_tier(distance_miles: float) -> str:
    """Return the color tier name for a given distance in miles."""
    for threshold, tier in DISTANCE_TIERS:
        if distance_miles <= threshold:
            return tier
    return "very_cold"


@dataclass
class GuessResult:
    """Result of a single guess."""
    city: CityRecord
    distance_miles: float
    color_tier: str
    is_correct: bool


@dataclass
class GameState:
    """Current state of a Citidle game session."""
    target: CityRecord
    guesses: List[GuessResult] = field(default_factory=list)
    is_won: bool = False

    @property
    def guess_count(self) -> int:
        return len(self.guesses)


# Module-level index cache
_index = None
_names = None


def _get_index():
    global _index, _names
    if _index is None:
        _index, _names = build_city_index()
    return _index, _names


def start_game() -> GameState:
    """Start a new game for today's daily city.

    Returns a GameState with the target set and empty guess history.
    """
    target = get_daily_city()
    return GameState(target=target)


def submit_guess(state: GameState, guess_text: str) -> Optional[GuessResult]:
    """Process a guess and update game state.

    Args:
        state: The current GameState.
        guess_text: The user's guess (city name).

    Returns:
        A GuessResult if the guess matched a valid city, or None if not found.
        Updates state.guesses and state.is_won in place.
    """
    if state.is_won:
        return None  # game already won

    index, names = _get_index()
    matches, _ = find_cities(guess_text, index, names)

    if not matches:
        return None  # city not found

    # Take the first match (user can disambiguate with state if needed)
    guessed_city = matches[0]
    dist = distance_between_records(guessed_city, state.target)
    tier = get_color_tier(dist)
    is_correct = dist == 0 or (
        guessed_city.name.lower() == state.target.name.lower()
        and guessed_city.state.lower() == state.target.state.lower()
    )

    result = GuessResult(
        city=guessed_city,
        distance_miles=dist,
        color_tier=tier,
        is_correct=is_correct,
    )
    state.guesses.append(result)

    if is_correct:
        state.is_won = True

    return result


def get_game_summary(state: GameState) -> dict:
    """Return a summary of the game state (useful for API responses).

    Returns a dict with target (if won), guess count, and guess history.
    """
    return {
        "is_won": state.is_won,
        "guess_count": state.guess_count,
        "target": f"{state.target.name}, {state.target.state}" if state.is_won else None,
        "guesses": [
            {
                "city": f"{g.city.name}, {g.city.state}",
                "distance_miles": round(g.distance_miles, 1),
                "color_tier": g.color_tier,
                "is_correct": g.is_correct,
            }
            for g in state.guesses
        ],
    }
