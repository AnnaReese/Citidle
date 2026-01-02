"""Flask web server for Citidle.

Provides REST API endpoints and serves the web UI.

Run with:
    python web.py
    # or
    flask --app web run --debug

Then open http://localhost:5000 in your browser.
"""

from __future__ import annotations

import os
import json
from datetime import date
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from game.daily import get_daily_city, get_all_cities, get_time_until_reset, get_cst_date
from game.distance import find_cities, build_city_index, distance_between_records
from game.engine import get_color_tier

# Get absolute path to static folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)  # Enable CORS for development

# Cache the city index at startup
_index, _names = build_city_index()


def _city_to_dict(city) -> dict:
    """Convert a CityRecord to a JSON-serializable dict."""
    return {
        "name": city.name,
        "state": city.state,
        "lat": city.lat,
        "lng": city.lng,
        "population": city.population,
    }


@app.route("/")
def index():
    """Serve the main game page."""
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/game/info")
def game_info():
    """Return game metadata (number of cities, time until reset)."""
    time_left = get_time_until_reset()
    total_seconds = int(time_left.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return jsonify({
        "total_cities": len(get_all_cities()),
        "cst_date": get_cst_date().isoformat(),
        "time_until_reset": {
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "total_seconds": total_seconds,
        },
    })


@app.route("/api/game/target-hash")
def target_hash():
    """Return a hash of today's target for client-side win verification.
    
    This allows the client to verify a win without revealing the answer.
    """
    target = get_daily_city()
    # Simple hash: just use the city name + state lowercased
    target_key = f"{target.name.lower()},{target.state.lower()}"
    return jsonify({"target_hash": hash(target_key) % 10000000})


@app.route("/api/guess", methods=["POST"])
def submit_guess():
    """Process a guess and return the result.
    
    Request body: {"guess": "city name"}
    Response: {"success": bool, "result": {...} or "error": "..."}
    """
    data = request.get_json()
    if not data or "guess" not in data:
        return jsonify({"success": False, "error": "Missing 'guess' in request body"}), 400
    
    guess_text = data["guess"].strip()
    if not guess_text:
        return jsonify({"success": False, "error": "Empty guess"}), 400
    
    # Find the guessed city
    matches, _ = find_cities(guess_text, _index, _names)
    if not matches:
        return jsonify({
            "success": False, 
            "error": "City not found. Make sure it's a US city with 300k+ population.",
            "guess": guess_text,
        })
    
    guessed_city = matches[0]
    target = get_daily_city()
    
    # Calculate distance and color tier
    dist = distance_between_records(guessed_city, target)
    tier = get_color_tier(dist)
    is_correct = (
        guessed_city.name.lower() == target.name.lower()
        and guessed_city.state.lower() == target.state.lower()
    )
    
    result = {
        "city": _city_to_dict(guessed_city),
        "distance_miles": round(dist, 1),
        "color_tier": tier,
        "is_correct": is_correct,
    }
    
    # If correct, include the target info
    if is_correct:
        result["target"] = _city_to_dict(target)
    
    return jsonify({"success": True, "result": result})


@app.route("/api/reveal", methods=["POST"])
def reveal_answer():
    """Reveal today's answer (for giving up).
    
    Request body: {"confirm": true}
    """
    data = request.get_json()
    if not data or not data.get("confirm"):
        return jsonify({"success": False, "error": "Must confirm reveal"}), 400
    
    target = get_daily_city()
    return jsonify({
        "success": True,
        "target": _city_to_dict(target),
    })


@app.route("/api/cities")
def list_cities():
    """Return list of all valid city names (for autocomplete)."""
    cities = get_all_cities()
    return jsonify({
        "cities": [f"{c.name}, {c.state}" for c in cities]
    })


if __name__ == "__main__":
    # Use port 5001 to avoid conflict with macOS AirPlay Receiver (port 5000)
    # Debug mode only for local development
    print("Starting Citidle web server...")
    print("Open http://localhost:5001 in your browser")
    app.run(debug=True, host="127.0.0.1", port=5001)
else:
    # Production mode (gunicorn) - no debug
    pass
