"""Map rendering utilities for Citidle.

This module provides functions to render the US map with color-coded
markers based on guess proximity. Closer guesses are shown in warmer/darker
colors (like Globle).

TODO: Implement actual map rendering (SVG, Matplotlib, or web canvas).
      For now, this provides color utilities and stub functions.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# Color palette for proximity tiers (hex colors for rendering)
# Warmer = closer, Cooler = farther
TIER_COLORS: Dict[str, str] = {
    "correct": "#00FF00",    # bright green for correct guess
    "very_hot": "#FF0000",   # dark red - very close
    "hot": "#FF4500",        # orange-red
    "warm": "#FFA500",       # orange
    "cool": "#FFD700",       # gold/yellow
    "cold": "#87CEEB",       # sky blue
    "very_cold": "#E0E0E0",  # light gray - very far
}


def get_color_for_tier(tier: str) -> str:
    """Return the hex color for a given proximity tier.

    Args:
        tier: One of the tier names from engine.DISTANCE_TIERS.

    Returns:
        A hex color string (e.g., "#FF0000").
    """
    return TIER_COLORS.get(tier, "#E0E0E0")


def get_color_for_distance(distance_miles: float) -> str:
    """Return the hex color for a given distance in miles.

    This is a convenience function that maps distance -> tier -> color.
    """
    from game.engine import get_color_tier
    tier = get_color_tier(distance_miles)
    return get_color_for_tier(tier)


def render_map_stub(
    guesses: List[Tuple[str, str, float, str]]
) -> str:
    """Stub function for map rendering.

    Args:
        guesses: List of (city_name, state, distance_miles, color_tier) tuples.

    Returns:
        A placeholder string describing what would be rendered.

    TODO: Replace with actual SVG/canvas rendering.
    """
    if not guesses:
        return "[Empty US Map - no guesses yet]"

    lines = ["[US Map with guesses:]"]
    for city, state, dist, tier in guesses:
        color = get_color_for_tier(tier)
        lines.append(f"  • {city}, {state}: {dist:.0f} mi ({tier}, {color})")
    return "\n".join(lines)


def get_us_map_bounds() -> Dict[str, float]:
    """Return approximate bounding box for continental US.

    Useful for setting up map view coordinates.
    """
    return {
        "min_lat": 24.396308,   # southernmost point (Key West area)
        "max_lat": 49.384358,   # northernmost point (48 states)
        "min_lng": -125.0,      # westernmost point
        "max_lng": -66.93457,   # easternmost point
    }


# Placeholder for future implementation
def render_map_svg(guesses: List[dict]) -> str:
    """Generate an SVG map with colored markers for guesses.

    TODO: Implement SVG generation with US state boundaries and city markers.

    Args:
        guesses: List of guess dicts from engine.get_game_summary().

    Returns:
        An SVG string.
    """
    raise NotImplementedError("SVG map rendering not yet implemented")


def render_map_html(guesses: List[dict]) -> str:
    """Generate HTML with an interactive map (e.g., Leaflet.js).

    TODO: Implement interactive map with Leaflet or similar.

    Args:
        guesses: List of guess dicts from engine.get_game_summary().

    Returns:
        An HTML string with embedded map.
    """
    raise NotImplementedError("HTML map rendering not yet implemented")
