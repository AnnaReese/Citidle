import math
import os
import pytest
from game import distance as dist


def test_normalize_basic():
    # punctuation removed and collapsed
    assert dist.normalize_name("St. Louis") == "st louis"
    assert dist.normalize_name("New York City") == "new york"


def test_normalize_empty_and_city_removal():
    assert dist.normalize_name("") == ""
    # the word 'city' is removed by normalization
    assert dist.normalize_name("Oklahoma City") == "oklahoma"


def test_alias_lookup_and_index():
    idx, names = dist.build_city_index()

    # alias NYC should find New York records
    matches, _ = dist.find_cities("NYC", idx, names)
    assert matches, "NYC should return at least one match"
    assert any(m.name.lower().startswith("new york") for m in matches)

    # alias 'st louis' should find St. Louis even if user types punctuation
    matches_sl, _ = dist.find_cities("st. louis", idx, names)
    assert matches_sl, "st. louis should return at least one match"
    assert any("louis" in m.name.lower() for m in matches_sl)


def test_state_disambiguation_portland():
    idx, names = dist.build_city_index()

    # user typing 'Portland, OR' should return Portland in Oregon
    matches, _ = dist.find_cities("Portland, OR", idx, names)
    assert matches, "Portland, OR should return at least one match"
    assert any(m.state.lower() in ("or", "oregon") for m in matches)


def test_index_has_entries_and_known_city():
    idx, names = dist.build_city_index()
    # index should contain many normalized names and include New York
    assert names
    assert any(n.startswith("new york") for n in names)


def test_find_unknown_returns_empty():
    idx, names = dist.build_city_index()
    matches, _ = dist.find_cities("thiscitydoesnotexist", idx, names)
    assert matches == []


def test_distance_symmetry_and_nonnegativity():
    idx, names = dist.build_city_index()
    a_matches, _ = dist.find_cities("NYC", idx, names)
    b_matches, _ = dist.find_cities("LA", idx, names)
    assert a_matches and b_matches
    a = a_matches[0]
    b = b_matches[0]

    dab = dist.distance_between_records(a, b)
    dba = dist.distance_between_records(b, a)
    assert dab >= 0
    assert dba >= 0
    assert math.isclose(dab, dba, rel_tol=1e-6)


def test_build_city_index_missing_file_raises():
    bad = "/nonexistent/path/to/cities.csv"
    with pytest.raises(FileNotFoundError):
        dist.build_city_index(bad)


def test_canonical_alias_entries():
    # ensure important aliases were canonicalized as expected
    assert hasattr(dist, "CANONICAL_ALIASES")
    ca = dist.CANONICAL_ALIASES
    # st. louis alias should canonicalize to 'st louis'
    assert ca.get("st louis") == "st louis"
    # nyc alias should canonicalize to 'new york' (city removed)
    assert ca.get("nyc") == "new york"


def test_all_canonical_alias_targets_exist_in_index():
    """Ensure every canonical alias target exists as a key in the built index.

    This surfaces typos or alias targets that point to names not present in
    `data/cities.csv`.
    """
    idx, names = dist.build_city_index()
    missing = []
    # iterate unique canonical targets
    for target in set(dist.CANONICAL_ALIASES.values()):
        if target not in idx:
            missing.append(target)
    assert not missing, f"Canonical alias targets missing from index: {missing}"

