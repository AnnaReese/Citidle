"""City name normalization, lookup, and distance utilities used by the game.

This module provides:
- normalize_name(name): normalize user input to a canonical key (includes alias expansion)
- build_city_index(csv_path): load `data/cities.csv` and build normalized lookup
- find_cities(query, ...): exact lookup (some aliases supported)
-- haversine_distance(lat1, lng1, lat2, lng2): compute great-circle distance (returns miles)

Drop this into `game/distance.py` — other game modules (engine) can import these helpers.
"""

from __future__ import annotations  # allow postponed evaluation of annotations

import csv  # reading CSV file of cities
import math  # trig and math for haversine calculation
import os  # filesystem checks
import re  # regex cleaning for normalization
from collections import defaultdict  # build index mapping
from dataclasses import dataclass  # simple data container for city records
from pathlib import Path  # construct path to data/cities.csv
from typing import Dict, List, Tuple  # type annotations

# note: fuzzy/misspelling matching intentionally omitted — only aliases are supported, might add later


# Path to CSV (data/cities.csv relative to repository root)
DEFAULT_CITIES_CSV = str(Path(__file__).resolve().parents[1] / "data" / "cities.csv")


# Small alias map for common short forms and nicknames.
# Keys are common user inputs (lowercased, punctuation-free) that map to
# the canonical CSV city name (lowercased). Normalize_name will expand
# aliases before finishing normalization so these should use the CSV form.
ALIASES: Dict[str, str] = {
	# New York
	"nyc": "new york city",
	"new york": "new york city",

	# Los Angeles
	"la": "los angeles",
	"lax": "los angeles",

	# Chicago
	"chi": "chicago",

	# Houston
	"hou": "houston",
	"htx": "houston",

	# Phoenix
	"phx": "phoenix",

	# Philadelphia
	"philly": "philadelphia",

	# San Diego
	"sd": "san diego",
	"sandiego": "san diego",

	# Dallas
	"dal": "dallas",

	# San Jose
	"sj": "san jose",

	# Austin
	"atx": "austin",

	# Jacksonville
	"jax": "jacksonville",

	# Fort Worth
	"ft worth": "fort worth",

	# Indianapolis
	"indy": "indianapolis",

	# Charlotte
	"clt": "charlotte",

	# San Francisco
	"sf": "san francisco",
	"san fran": "san francisco",

	# Seattle
	"sea": "seattle",

	# Denver
	"den": "denver",

	# Washington DC
	"dc": "washington",
	"washington dc": "washington",

	# Nashville
	"nash": "nashville",

	# Oklahoma City
	"okc": "oklahoma city",

	# Boston
	"bos": "boston",

	# Portland
	"pdx": "portland",

	# Las Vegas
	"vegas": "las vegas",

	# Detroit
	"det": "detroit",

	# Louisville
	"lou": "louisville",

	# Baltimore
	"bmore": "baltimore",

	# Milwaukee
	"mke": "milwaukee",

	# Albuquerque
	"abq": "albuquerque",

	# Sacramento
	"sac": "sacramento",

	# Kansas City
	"kc": "kansas city",

	# Atlanta
	"atl": "atlanta",

	# Omaha
	"oma": "omaha",

	# Colorado Springs
	"cos": "colorado springs",

	# Virginia Beach
	"va beach": "virginia beach",

	# Miami
	"mia": "miami",

	# Oakland
	"oak": "oakland",

	# Minneapolis / Saint Paul
	"mpls": "minneapolis",
	"st paul": "saint paul",

	# New Orleans
	"nola": "new orleans",

	# St. Louis / Saint Louis
	"st louis": "st. louis",
	"saint louis": "st. louis",

	# St. Petersburg
	"st petersburg": "st. petersburg",
}


# Regex helpers — _punct_re removes punctuation, _multi_space_re collapses repeated whitespace
_punct_re = re.compile(r"[^\w\s]")
_multi_space_re = re.compile(r"\s+")


@dataclass
class CityRecord:
	name: str
	state: str
	lat: float
	lng: float
	population: int


def normalize_name(name: str) -> str:
	"""Normalize a city name into a compact lookup key.

	Steps:
	- lowercase and strip
	- remove punctuation
	- expand simple aliases
	- remove trailing word 'city'
	- collapse whitespace
	"""
	if not name:
		return ""
	s = name.strip().lower()
	s = s.replace("&", " and ")
	s = _punct_re.sub(" ", s) # replaces punctuation characters in the string s with spaces
	if s in ALIASES:
		s = ALIASES[s] # expand alias
		# If the alias value contains punctuation (e.g. "st. louis"), remove it
		# so the final normalized key matches the index (which had punctuation removed).
		s = _punct_re.sub(" ", s)
	s = re.sub(r"\bcity\b", "", s) # removes the word "city" from the string s, but only when it appears as a whole word
	s = _multi_space_re.sub(" ", s).strip() # collapses extra whitespace into single spaces and trims the ends of the string
	return s


def build_city_index(csv_path: str = DEFAULT_CITIES_CSV) -> Tuple[Dict[str, List[CityRecord]], List[str]]:
	"""Load cities CSV and return a normalized index and list of normalized names.

	Returns:
	  - index: normalized_name -> list[CityRecord]
	  - normalized_names: sorted list of normalized keys (useful for fuzzy matching)
	"""
	# mapping: normalized_name -> list of CityRecord objects
	# declares a typed dictionary and initializes it so lists are created automatically
	index: Dict[str, List[CityRecord]] = defaultdict(list)
	# keep a set of normalized keys we've seen (useful if needed elsewhere)
	normalized_names = set()

	# ensure the CSV exists before trying to open it
	if not os.path.exists(csv_path):
		raise FileNotFoundError(f"cities csv not found: {csv_path}")

	# open CSV and iterate rows as dictionaries
	with open(csv_path, newline="", encoding="utf-8") as fh:
		reader = csv.DictReader(fh)
		for row in reader:
			# read canonical fields from the CSV row (strip whitespace)
			canonical = row.get("name", "").strip()
			state = row.get("state", "").strip()

			# parse numeric fields, using safe defaults when missing
			lat = float(row.get("lat") or 0)
			lng = float(row.get("lng") or 0)
			pop = int(float(row.get("population") or 0))

			# build a typed record for easier downstream usage
			rec = CityRecord(name=canonical, state=state, lat=lat, lng=lng, population=pop)

			# normalize the canonical name to a lookup key (handles aliases)
			normalized = normalize_name(canonical)

			# add the record to the main index under the normalized key
			index[normalized].append(rec)
			normalized_names.add(normalized)

			# also index by "name, state" to support disambiguation when user provides a state
			# e.g. user might type "portland, or" to mean Portland, Oregon
			if state:
				# index with comma (legacy form) e.g. 'portland, or'
				state_key = f"{normalized}, {state.lower()}"
				index[state_key] = index.get(state_key, []) + [rec]
				# also index without comma (matches normalized user input like 'portland or')
				state_key_space = f"{normalized} {state.lower()}"
				index[state_key_space] = index.get(state_key_space, []) + [rec]

	# return the mapping and a sorted list of normalized keys
	return index, sorted(normalized_names)


def find_cities(query: str, index=None, normalized_names=None):
	"""Find cities for a user query using only exact normalization and aliases.

	Returns (matches, suggestions)
	- matches: list[CityRecord] (exact matches by normalized key)
	- suggestions: empty list (kept for API compatibility)
	"""
	if index is None:
		index, _ = build_city_index() # returns multiple values and keeps only the first one

	qnorm = normalize_name(query)
	matches = index.get(qnorm, [])

	# allow user to type 'name, state' like 'portland, or' or 'portland, oregon'
	if not matches and "," in qnorm:
		parts = [p.strip() for p in qnorm.split(",")]
		if len(parts) >= 2:
			key = f"{parts[0]}, {parts[1]}"
			matches = index.get(key, [])

	return matches, []


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
	"""Return great-circle distance between two points in miles.

	This function always returns distance in miles.
	"""
	# convert degrees to radians
	rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lng1, lat2, lng2))
	dlat = rlat2 - rlat1
	dlng = rlon2 - rlon1
	a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng / 2) ** 2
	c = 2 * math.asin(min(1, math.sqrt(a)))
	# Earth's radius in kilometers
	radius_km = 6371.0
	dist_km = radius_km * c
	# convert kilometers to miles
	return dist_km * 0.621371


# accept two CityRecord objects and return distance in miles
def distance_between_records(a: CityRecord, b: CityRecord) -> float:
	"""Return distance between two CityRecord objects in miles."""
	return haversine_distance(a.lat, a.lng, b.lat, b.lng)


if __name__ == "__main__":
	# simple demo when run as a script: build the index and show matching behavior
	idx, names = build_city_index()
	# example inputs to demonstrate normalization and alias handling
	examples = [
		"New York",
		"new york city",
		"NYC",
		"St Louis",
		"Saint Louis",
		"St. Paul",
		"saint paul",
		"Los Angeles",
		"LA",
		"San Francisco",
		"SF",
	]
	for ex in examples:
		# normalize user input and lookup in the built index
		matches, _ = find_cities(ex, idx, names)
		print(f">>> {ex!r}: {len(matches)} match(es)") # prints the value of ex using its Python representation (!r) followed by how many items are in matches
		for m in matches[:3]:
			# show the canonical CSV name, state, and population for the match
			print("   ", m.name, m.state, m.population)

