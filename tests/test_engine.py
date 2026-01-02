"""Tests for game/engine.py - core game logic."""

from datetime import date

from game import engine
from game.daily import get_daily_city


def test_start_game_returns_game_state():
    """start_game should return a GameState with target and empty guesses."""
    state = engine.start_game()
    assert state is not None
    assert state.target is not None
    assert state.guesses == []
    assert state.is_won is False
    assert state.guess_count == 0


def test_submit_guess_valid_city():
    """Submitting a valid city should return a GuessResult."""
    state = engine.start_game()
    # Guess a city we know exists
    result = engine.submit_guess(state, "Los Angeles")
    assert result is not None
    assert result.city.name == "Los Angeles"
    assert result.distance_miles >= 0
    assert result.color_tier in [t[1] for t in engine.DISTANCE_TIERS]
    assert state.guess_count == 1


def test_submit_guess_invalid_city_returns_none():
    """Submitting an invalid city should return None."""
    state = engine.start_game()
    result = engine.submit_guess(state, "NotARealCity12345")
    assert result is None
    assert state.guess_count == 0  # guess not counted


def test_submit_guess_correct_wins_game():
    """Guessing the correct city should set is_won to True."""
    state = engine.start_game()
    target_name = state.target.name

    result = engine.submit_guess(state, target_name)
    assert result is not None
    assert result.is_correct is True
    assert state.is_won is True


def test_submit_guess_after_win_returns_none():
    """After winning, further guesses should return None."""
    state = engine.start_game()
    target_name = state.target.name

    # Win the game
    engine.submit_guess(state, target_name)
    assert state.is_won is True

    # Try to guess again
    result = engine.submit_guess(state, "Chicago")
    assert result is None


def test_get_color_tier():
    """get_color_tier should return correct tiers for various distances."""
    assert engine.get_color_tier(0) == "correct"
    assert engine.get_color_tier(25) == "very_hot"
    assert engine.get_color_tier(100) == "hot"
    assert engine.get_color_tier(200) == "warm"
    assert engine.get_color_tier(500) == "cool"
    assert engine.get_color_tier(800) == "cold"
    assert engine.get_color_tier(1500) == "very_cold"


def test_get_game_summary():
    """get_game_summary should return a dict with expected keys."""
    state = engine.start_game()
    engine.submit_guess(state, "Chicago")

    summary = engine.get_game_summary(state)
    assert isinstance(summary, dict)
    assert "is_won" in summary
    assert "guess_count" in summary
    assert "guesses" in summary
    assert summary["guess_count"] == 1
    assert len(summary["guesses"]) == 1


def test_guess_result_contains_distance():
    """GuessResult should contain distance_miles field."""
    state = engine.start_game()
    result = engine.submit_guess(state, "New York")

    if result:  # NYC might be the target, but should still have distance
        assert hasattr(result, "distance_miles")
        assert isinstance(result.distance_miles, float)
