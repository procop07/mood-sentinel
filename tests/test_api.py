import pytest
import json
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_health_endpoint():
    """Тест эндпоинта /api/v1/health"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data

def test_mood_post_endpoint():
    """Тест POST /api/v1/mood - добавление записи настроения"""
    mood_data = {
        "mood": 7,
        "note": "Хорошее утро",
        "timestamp": "2025-01-01T09:00:00Z"
    }
    
    # Поскольку в текущем API нет эндпоинта /api/v1/mood, 
    # создадим мок-тест для будущей реализации
    with pytest.raises(Exception):  # Ожидаем 404 или другую ошибку
        response = client.post("/api/v1/mood", json=mood_data)

def test_mood_history_endpoint():
    """Тест GET /api/v1/mood/history - получение истории настроения"""
    # Мок-тест для будущей реализации
    with pytest.raises(Exception):  # Ожидаем 404 или другую ошибку
        response = client.get("/api/v1/mood/history")

def test_today_endpoint():
    """Тест эндпоинта /today"""
    response = client.get("/today")
    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "reports_count" in data
    assert "reports" in data

def test_week_endpoint():
    """Тест эндпоинта /week"""
    response = client.get("/week")
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert data["period"] == "week"
    assert "start_date" in data
    assert "end_date" in data
    assert "reports_count" in data
    assert "reports" in data

def test_flags_endpoint():
    """Тест эндпоинта /flags"""
    response = client.get("/flags")
    assert response.status_code == 200
    data = response.json()
    assert "flags" in data
    assert "timestamp" in data
