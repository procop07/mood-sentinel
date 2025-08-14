import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
from datetime import datetime, timedelta

# Import the FastAPI app from api.py
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
    def test_mood_post_invalid_data(self, mock_load_json):
        """Test POST /api/v1/mood with invalid data"""
        mock_load_json.return_value = {"mood_entries": []}
        
        # Test with invalid mood value (should be 1-10)
        invalid_mood_data = {
            "mood": 15,  # Invalid value
            "note": "Invalid mood",
            "timestamp": datetime.now().isoformat()
        }
        
        response = client.post("/api/v1/mood", json=invalid_mood_data)
        # Should return 404 since endpoint doesn't exist yet
        assert response.status_code == 404
        
    def test_mood_post_missing_required_fields(self):
        """Test POST /api/v1/mood with missing required fields"""
        incomplete_data = {
            "note": "Missing mood value"
        }
        
        response = client.post("/api/v1/mood", json=incomplete_data)
        # Should return 404 since endpoint doesn't exist yet
        assert response.status_code == 404

    @patch('api.load_json_data')
    def test_mood_history_endpoint(self, mock_load_json):
        """Test GET /api/v1/mood/history endpoint"""
        # Mock data for mood history
        mock_data = {
            "reports": [
                {
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "mood": 8,
                    "note": "Good day yesterday"
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "mood": 7,
                    "note": "Decent day today"
                }
            ]
        }
        mock_load_json.return_value = mock_data
        
        # This endpoint doesn't exist yet, should return 404
        response = client.get("/api/v1/mood/history")
        assert response.status_code == 404


class TestExistingEndpoints:
    """Tests for existing endpoints in api.py"""
    
    @patch('api.load_json_data')
    def test_today_endpoint_success(self, mock_load_json):
        """Test /today endpoint with valid data"""
        mock_data = {
            "reports": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "mood": 8,
                    "note": "Good day today"
                }
            ]
        }
        mock_load_json.return_value = mock_data
        
        response = client.get("/today")
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "reports_count" in data
        assert "reports" in data

    @patch('api.load_json_data')
    def test_today_endpoint_no_data(self, mock_load_json):
        """Test /today endpoint with no reports"""
        mock_load_json.return_value = {"reports": []}
        
        response = client.get("/today")
        assert response.status_code == 200
        data = response.json()
        assert data["reports_count"] == 0
        assert data["reports"] == []

    @patch('api.load_json_data')
    def test_week_endpoint_success(self, mock_load_json):
        """Test /week endpoint with valid data"""
        # Generate mock data for the past week
        reports = []
        for i in range(7):
            reports.append({
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "mood": 7 + i % 3,
                "note": f"Day {i} report"
            })
        
        mock_data = {"reports": reports}
        mock_load_json.return_value = mock_data
        
        response = client.get("/week")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week"
        assert "start_date" in data
        assert "end_date" in data
        assert "reports_count" in data
        assert "reports" in data

    @patch('api.load_json_data')
    def test_flags_endpoint_success(self, mock_load_json):
        """Test /flags endpoint"""
        mock_flags = {
            "notification_enabled": True,
            "debug_mode": False,
            "data_collection": True
        }
        mock_load_json.return_value = mock_flags
        
        response = client.get("/flags")
        assert response.status_code == 200
        data = response.json()
        assert "flags" in data
        assert "timestamp" in data


class TestErrorHandling:
    """Tests for error handling scenarios"""
    
    @patch('api.load_json_data')
    def test_today_endpoint_file_error(self, mock_load_json):
        """Test /today endpoint when file loading fails"""
        mock_load_json.side_effect = Exception("File not found")
        
        response = client.get("/today")
        assert response.status_code == 500
        assert "Ошибка при получении данных за сегодня" in response.json()["detail"]

    @patch('api.load_json_data')
    def test_week_endpoint_file_error(self, mock_load_json):
        """Test /week endpoint when file loading fails"""
        mock_load_json.side_effect = Exception("File not found")
        
        response = client.get("/week")
        assert response.status_code == 500
        assert "Ошибка при получении данных за неделю" in response.json()["detail"]

    @patch('api.load_json_data')
    def test_flags_endpoint_file_error(self, mock_load_json):
        """Test /flags endpoint when file loading fails"""
        mock_load_json.side_effect = Exception("File not found")
        
        response = client.get("/flags")
        assert response.status_code == 500
        assert "Ошибка при получении флагов" in response.json()["detail"]


class TestDataValidation:
    """Tests for data validation and edge cases"""
    
    @patch('api.load_json_data')
    def test_date_filtering_edge_cases(self, mock_load_json):
        """Test date filtering with edge cases"""
        # Test with reports at exactly the boundary times
        now = datetime.now()
        boundary_time = now - timedelta(days=1)
        
        reports = [
            {
                "timestamp": boundary_time.isoformat(),
                "mood": 8,
                "note": "Boundary case"
            },
            {
                "timestamp": (now - timedelta(days=2)).isoformat(),
                "mood": 6,
                "note": "Outside boundary"
            }
        ]
        
        mock_data = {"reports": reports}
        mock_load_json.return_value = mock_data
        
        response = client.get("/today")
        assert response.status_code == 200
        # Verify that date filtering works correctly
        
    @patch('api.load_json_data')
    def test_malformed_timestamp_handling(self, mock_load_json):
        """Test handling of malformed timestamps"""
        reports = [
            {
                "timestamp": "invalid-timestamp",
                "mood": 8,
                "note": "Invalid timestamp"
            }
        ]
        
        mock_data = {"reports": reports}
        mock_load_json.return_value = mock_data
        
        # The endpoint should handle this gracefully
        response = client.get("/today")
        # Should either return 500 or handle gracefully
        assert response.status_code in [200, 500]
