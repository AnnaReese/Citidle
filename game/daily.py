"""Daily target city selection for Citidle.

This module provides a deterministic way to select the daily target city
based on the current date in Central Standard Time (CST). All players get
the same city on the same day, with the daily reset occurring at midnight CST.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional

from game.distance import CityRecord, build_city_index

# Central Standard Time is UTC-6 (we use CST year-round for consistency,
# not CDT, to avoid daylight saving complexity)
CST = timezone(timedelta(hours=-6))

# Module-level cache for the city list (loaded once)
_cities_list: Optional[List[CityRecord]] = None


def _load_cities() -> List[CityRecord]:
    """Load and cache the list of eligible cities from the CSV.

    Returns a flat list of CityRecord objects (one per unique normalized key).
    """
    global _cities_list
    if _cities_list is None:
        index, _ = build_city_index()
        # Flatten: take the first record for each normalized key to avoid duplicates
        _cities_list = [records[0] for records in index.values() if records]
        # Sort by canonical name for deterministic ordering across runs
        _cities_list.sort(key=lambda c: (c.name.lower(), c.state.lower()))
    return _cities_list


def get_daily_city(for_date: Optional[date] = None) -> CityRecord:
    """Return the target city for the given date (defaults to today in CST).

    The selection is deterministic: the same date always yields the same city.
    This ensures all players worldwide get the same daily challenge, with the
    reset occurring at midnight Central Standard Time (CST / UTC-6).

    Args:
        for_date: The date to select a city for. Defaults to today in CST.

    Returns:
        A CityRecord representing the target city for the day.
    """
    cities = _load_cities()
    if for_date is None:
        # Get current date in CST (Central Standard Time, UTC-6)
        now_cst = datetime.now(CST)
        d = now_cst.date()
    else:
        d = for_date
    # Use SHA-256 hash of the ISO date string to pick an index
    hash_hex = hashlib.sha256(d.isoformat().encode("utf-8")).hexdigest()
    idx = int(hash_hex, 16) % len(cities)
    return cities[idx]


def get_cst_date() -> date:
    """Return the current date in Central Standard Time.
    
    Useful for displaying when the next reset occurs.
    """
    return datetime.now(CST).date()


def get_time_until_reset() -> timedelta:
    """Return the time remaining until the next daily reset (midnight CST).
    
    Returns:
        A timedelta representing time until midnight CST.
    """
    now_cst = datetime.now(CST)
    # Midnight CST tomorrow
    tomorrow_midnight = datetime.combine(
        now_cst.date() + timedelta(days=1),
        datetime.min.time(),
        tzinfo=CST
    )
    return tomorrow_midnight - now_cst


def get_all_cities() -> List[CityRecord]:
    """Return all eligible cities (useful for validation or admin tools)."""
    return list(_load_cities())
