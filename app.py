#!/usr/bin/env python3
"""Citidle - A daily US city guessing game.

This is the main entry point for the Citidle application.
Run with: python app.py

Currently provides a simple CLI interface. Future versions will add:
- Flask/FastAPI web server
- REST API endpoints
- Web UI

Usage:
    python app.py          # Play today's game in CLI mode
    python app.py --help   # Show help
"""

from __future__ import annotations

import sys

from game.daily import get_daily_city, get_all_cities, get_time_until_reset
from game.engine import GameState, get_game_summary, start_game, submit_guess
from map.renderer import get_color_for_tier, render_map_stub


def format_time_remaining(td) -> str:
    """Format a timedelta as hours and minutes."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m"


def print_welcome():
    """Print welcome message and instructions."""
    print("=" * 50)
    print("  🏙️  CITIDLE - Guess the US City!  🏙️")
    print("=" * 50)
    print()
    print("Guess the mystery US city (population 300k+).")
    print("You have unlimited guesses until you find it!")
    print()
    print("After each guess, you'll see how close you are:")
    print("  🟢 correct  - You got it!")
    print("  🔴 very_hot - Within 50 miles")
    print("  🟠 hot      - Within 150 miles")
    print("  🟡 warm     - Within 300 miles")
    print("  🔵 cool     - Within 600 miles")
    print("  ⚪ cold     - Within 1000 miles")
    print("  ⬜ very_cold - More than 1000 miles")
    print()
    print("Type 'quit' to exit, 'map' to see your guesses.")
    print("-" * 50)
    print()


def print_guess_result(result, guess_num: int):
    """Print the result of a guess."""
    tier_emoji = {
        "correct": "🟢",
        "very_hot": "🔴",
        "hot": "🟠",
        "warm": "🟡",
        "cool": "🔵",
        "cold": "⚪",
        "very_cold": "⬜",
    }
    emoji = tier_emoji.get(result.color_tier, "❓")
    city_str = f"{result.city.name}, {result.city.state}"

    if result.is_correct:
        print(f"\n{emoji} Guess #{guess_num}: {city_str}")
        print("🎉 CORRECT! You found it! 🎉")
    else:
        print(f"\n{emoji} Guess #{guess_num}: {city_str}")
        print(f"   Distance: {result.distance_miles:.0f} miles ({result.color_tier})")


def print_map(state: GameState):
    """Print a text representation of the map with guesses."""
    guesses = [
        (g.city.name, g.city.state, g.distance_miles, g.color_tier)
        for g in state.guesses
    ]
    print()
    print(render_map_stub(guesses))
    print()


def play_cli():
    """Run the CLI game loop."""
    print_welcome()

    state = start_game()
    num_cities = len(get_all_cities())
    time_left = format_time_remaining(get_time_until_reset())
    print(f"Today's city is waiting... (1 of {num_cities} possible cities)")
    print(f"⏰ Next city in: {time_left} (resets at midnight CST)")
    print()

    while not state.is_won:
        try:
            guess = input("Enter your guess: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nThanks for playing! See you tomorrow. 👋")
            sys.exit(0)

        if not guess:
            continue

        if guess.lower() == "quit":
            print(f"\nThe answer was: {state.target.name}, {state.target.state}")
            print("Thanks for playing! See you tomorrow. 👋")
            sys.exit(0)

        if guess.lower() == "map":
            print_map(state)
            continue

        result = submit_guess(state, guess)

        if result is None:
            print("❌ City not found. Try another city name.")
            continue

        print_guess_result(result, state.guess_count)

    # Game won
    print()
    print(f"You found {state.target.name}, {state.target.state} in {state.guess_count} guess{'es' if state.guess_count != 1 else ''}!")
    print()
    print_map(state)
    time_left = format_time_remaining(get_time_until_reset())
    print(f"🌆 Share your result! Next city in: {time_left} (midnight CST)")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        sys.exit(0)

    play_cli()


if __name__ == "__main__":
    main()
