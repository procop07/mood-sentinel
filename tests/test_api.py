import pytest
import os
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
from datetime import datetime, timedelta
from api import app

client = TestClient(app)

class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    def test_health_endpoint_success(self):
        """Test health endpoint returns successful status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    def test_health_endpoint_structure(self):
        """Test health endpoint returns correct data structure"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert field in data


class TestMoodEndpoints:
    """Tests for mood-related endpoints"""

    @patch('api.load_json_data')
    def test_mood_post_endpoint(self, mock_load_json):
        """Test POST /api/v1/mood endpoint (mock implementation)"""
        # Note: Since the current API doesn't have this endpoint implemented,
        # this is a test for the expected behavior
        mock_load_json.return_value = {"mood_entries": []}
        
        mood_data = {
            "mood": 7,
            "note": "Feeling good today",
            "timestamp": datetime.now().isoformat()
        }
        
        # This endpoint doesn't exist yet in api.py, so it should return 404
        response = client.post("/api/v1/mood", json=mood_data)
        assert response.status_code == 404
        
    @patch('api.load_json_data')
    def test_mood_history_endpoint(self, mock_load_json):
        """Test GET /api/v1/mood/history endpoint"""
        mock_data = {
            "mood_entries": [
                {"id": 1, "mood": 7, "timestamp": "2023-01-01T12:00:00", "note": "Good day"},
                {"id": 2, "mood": 5, "timestamp": "2023-01-02T12:00:00", "note": "Average day"}
            ]
        }
        mock_load_json.return_value = mock_data
        
        # This endpoint doesn't exist yet, should return 404
        response = client.get("/api/v1/mood/history")
        assert response.status_code == 404


class TestAPIValidation:
    """Tests for API validation and error handling"""
    
    def test_invalid_endpoint(self):
        """Test that invalid endpoints return 404"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404
        
    def test_invalid_method(self):
        """Test that invalid HTTP methods return appropriate errors"""
        response = client.patch("/health")
        assert response.status_code == 405  # Method Not Allowed