"""Tests for game/daily.py - daily city selection."""

from datetime import date, datetime, timedelta

from game import daily


def test_get_daily_city_returns_city_record():
    """get_daily_city should return a CityRecord with expected fields."""
    city = daily.get_daily_city()
    assert city is not None
    assert hasattr(city, "name")
    assert hasattr(city, "state")
    assert hasattr(city, "lat")
    assert hasattr(city, "lng")
    assert hasattr(city, "population")


def test_get_daily_city_deterministic_for_same_date():
    """Same date should always return the same city."""
    test_date = date(2026, 1, 1)
    city1 = daily.get_daily_city(test_date)
    city2 = daily.get_daily_city(test_date)
    assert city1.name == city2.name
    assert city1.state == city2.state


def test_get_daily_city_different_dates_can_differ():
    """Different dates should (usually) return different cities.

    Note: There's a small chance two dates hash to the same city,
    but checking several dates should yield at least one difference.
    """
    cities = set()
    for day in range(1, 10):
        city = daily.get_daily_city(date(2026, 1, day))
        cities.add((city.name, city.state))
    # With 9 dates, we expect multiple unique cities (very high probability)
    assert len(cities) > 1


def test_get_all_cities_returns_list():
    """get_all_cities should return a non-empty list of CityRecord objects."""
    cities = daily.get_all_cities()
    assert isinstance(cities, list)
    assert len(cities) > 0
    assert all(hasattr(c, "name") for c in cities)


def test_cities_list_is_sorted():
    """The cities list should be sorted for deterministic ordering."""
    cities = daily.get_all_cities()
    names = [(c.name.lower(), c.state.lower()) for c in cities]
    assert names == sorted(names)


# --- Tests for CST timezone functions ---


def test_get_cst_date_returns_date():
    """get_cst_date should return a date object."""
    cst_date = daily.get_cst_date()
    assert isinstance(cst_date, date)


def test_get_cst_date_is_reasonable():
    """get_cst_date should return a date close to today (within 1 day).

    This accounts for timezone differences between local time and CST.
    """
    cst_date = daily.get_cst_date()
    today = date.today()
    delta = abs((cst_date - today).days)
    # Should be within 1 day of local date (timezone offset)
    assert delta <= 1


def test_get_time_until_reset_returns_timedelta():
    """get_time_until_reset should return a timedelta object."""
    time_left = daily.get_time_until_reset()
    assert isinstance(time_left, timedelta)


def test_get_time_until_reset_is_positive():
    """Time until reset should always be positive (future midnight)."""
    time_left = daily.get_time_until_reset()
    assert time_left.total_seconds() > 0


def test_get_time_until_reset_is_under_24_hours():
    """Time until reset should be less than 24 hours."""
    time_left = daily.get_time_until_reset()
    assert time_left.total_seconds() < 24 * 60 * 60


def test_cst_timezone_is_utc_minus_6():
    """CST timezone should be UTC-6."""
    assert daily.CST.utcoffset(None) == timedelta(hours=-6)


def test_daily_city_uses_cst_date():
    """When no date provided, get_daily_city should use CST date.

    Verify by checking that the city matches what we'd get for the CST date.
    """
    cst_date = daily.get_cst_date()
    city_default = daily.get_daily_city()
    city_for_cst = daily.get_daily_city(cst_date)
    assert city_default.name == city_for_cst.name
    assert city_default.state == city_for_cst.state
