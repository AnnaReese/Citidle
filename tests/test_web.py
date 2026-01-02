"""Tests for web.py - Flask API endpoints."""

import json
import pytest
from web import app, _city_to_dict
from game.daily import get_daily_city, get_cst_date


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestGameInfo:
    """Tests for /api/game/info endpoint."""

    def test_game_info_returns_200(self, client):
        """GET /api/game/info should return 200 OK."""
        response = client.get("/api/game/info")
        assert response.status_code == 200

    def test_game_info_returns_json(self, client):
        """GET /api/game/info should return valid JSON."""
        response = client.get("/api/game/info")
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_game_info_has_required_fields(self, client):
        """Response should contain total_cities, cst_date, time_until_reset."""
        response = client.get("/api/game/info")
        data = json.loads(response.data)
        
        assert "total_cities" in data
        assert "cst_date" in data
        assert "time_until_reset" in data
        
        assert isinstance(data["total_cities"], int)
        assert data["total_cities"] > 0

    def test_game_info_time_format(self, client):
        """time_until_reset should have hours, minutes, seconds."""
        response = client.get("/api/game/info")
        data = json.loads(response.data)
        
        time_data = data["time_until_reset"]
        assert "hours" in time_data
        assert "minutes" in time_data
        assert "seconds" in time_data
        assert "total_seconds" in time_data
        
        # All should be non-negative
        assert time_data["hours"] >= 0
        assert time_data["minutes"] >= 0
        assert time_data["seconds"] >= 0


class TestGuessEndpoint:
    """Tests for /api/guess endpoint."""

    def test_guess_requires_post(self, client):
        """GET /api/guess should not be allowed."""
        response = client.get("/api/guess")
        assert response.status_code == 405

    def test_guess_requires_json_body(self, client):
        """POST without JSON body should return 400 or 415."""
        response = client.post("/api/guess")
        # Flask returns 415 Unsupported Media Type when no JSON is provided
        assert response.status_code in [400, 415]

    def test_guess_requires_guess_field(self, client):
        """POST without 'guess' field should return 400."""
        response = client.post(
            "/api/guess",
            data=json.dumps({"city": "Los Angeles"}),
            content_type="application/json"
        )
        assert response.status_code == 400

    def test_guess_empty_string_returns_error(self, client):
        """Empty guess string should return error."""
        response = client.post(
            "/api/guess",
            data=json.dumps({"guess": "   "}),
            content_type="application/json"
        )
        assert response.status_code == 400

    def test_guess_valid_city_returns_success(self, client):
        """Valid city guess should return success with result."""
        response = client.post(
            "/api/guess",
            data=json.dumps({"guess": "Los Angeles"}),
            content_type="application/json"
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "result" in data

    def test_guess_result_has_required_fields(self, client):
        """Guess result should contain city, distance, tier, is_correct."""
        response = client.post(
            "/api/guess",
            data=json.dumps({"guess": "Chicago"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        result = data["result"]
        
        assert "city" in result
        assert "distance_miles" in result
        assert "color_tier" in result
        assert "is_correct" in result
        
        # City should have name, state, lat, lng, population
        city = result["city"]
        assert "name" in city
        assert "state" in city
        assert "lat" in city
        assert "lng" in city

    def test_guess_invalid_city_returns_error(self, client):
        """Invalid city should return success=False with error message."""
        response = client.post(
            "/api/guess",
            data=json.dumps({"guess": "NotARealCity12345"}),
            content_type="application/json"
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data

    def test_guess_correct_city_sets_is_correct(self, client):
        """Guessing the correct city should return is_correct=True."""
        target = get_daily_city()
        
        response = client.post(
            "/api/guess",
            data=json.dumps({"guess": target.name}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert data["result"]["is_correct"] is True
        assert "target" in data["result"]

    def test_guess_with_state_disambiguation(self, client):
        """Guessing with state (e.g., 'Portland, OR') should work."""
        response = client.post(
            "/api/guess",
            data=json.dumps({"guess": "Portland, OR"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert data["result"]["city"]["state"].upper() in ["OR", "OREGON"]


class TestRevealEndpoint:
    """Tests for /api/reveal endpoint."""

    def test_reveal_requires_post(self, client):
        """GET /api/reveal should not be allowed."""
        response = client.get("/api/reveal")
        assert response.status_code == 405

    def test_reveal_requires_confirm(self, client):
        """POST without confirm=true should return 400."""
        response = client.post(
            "/api/reveal",
            data=json.dumps({"confirm": False}),
            content_type="application/json"
        )
        assert response.status_code == 400

    def test_reveal_with_confirm_returns_target(self, client):
        """POST with confirm=true should return the target city."""
        response = client.post(
            "/api/reveal",
            data=json.dumps({"confirm": True}),
            content_type="application/json"
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "target" in data
        assert "name" in data["target"]
        assert "state" in data["target"]


class TestCitiesEndpoint:
    """Tests for /api/cities endpoint."""

    def test_cities_returns_200(self, client):
        """GET /api/cities should return 200 OK."""
        response = client.get("/api/cities")
        assert response.status_code == 200

    def test_cities_returns_list(self, client):
        """Response should contain a list of city strings."""
        response = client.get("/api/cities")
        data = json.loads(response.data)
        
        assert "cities" in data
        assert isinstance(data["cities"], list)
        assert len(data["cities"]) > 0

    def test_cities_format(self, client):
        """Each city should be in 'Name, State' format."""
        response = client.get("/api/cities")
        data = json.loads(response.data)
        
        for city in data["cities"][:5]:  # Check first 5
            assert ", " in city
            parts = city.split(", ")
            assert len(parts) == 2


class TestIndexPage:
    """Tests for serving the main page."""

    def test_index_returns_200(self, client):
        """GET / should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_returns_html(self, client):
        """GET / should return HTML content."""
        response = client.get("/")
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_city_to_dict_returns_dict(self):
        """_city_to_dict should return a dict with expected keys."""
        city = get_daily_city()
        result = _city_to_dict(city)
        
        assert isinstance(result, dict)
        assert "name" in result
        assert "state" in result
        assert "lat" in result
        assert "lng" in result
        assert "population" in result

    def test_city_to_dict_values_types(self):
        """_city_to_dict values should have correct types."""
        city = get_daily_city()
        result = _city_to_dict(city)
        
        assert isinstance(result["name"], str)
        assert isinstance(result["state"], str)
        assert isinstance(result["lat"], (int, float))
        assert isinstance(result["lng"], (int, float))
        assert isinstance(result["population"], int)
