import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app


client = TestClient(app)


class TestHealthEndpoint:
    
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRootEndpoint:
    
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Smart Home Dashboard"
        assert "endpoints" in data


class TestHueEndpoints:
    
    @patch('services.hue_service.hue_service.get_status')
    def test_get_hue_status(self, mock_get_status):
        mock_get_status.return_value = {"name": "Baby room", "is_on": True, "brightness": 128}
        
        response = client.get("/api/hue/status")
        assert response.status_code == 200
        assert response.json()["is_on"] == True
    
    @patch('services.hue_service.hue_service.turn_off')
    def test_hue_off(self, mock_turn_off):
        mock_turn_off.return_value = {"status": "success", "light": "Baby room"}
        
        response = client.get("/api/hue/off")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    @patch('services.hue_service.hue_service.turn_on')
    def test_hue_on(self, mock_turn_on):
        mock_turn_on.return_value = {"status": "success", "light": "Baby room", "brightness": 128}
        
        response = client.get("/api/hue/on")
        assert response.status_code == 200
    
    @patch('services.hue_service.hue_service.set_timer')
    def test_hue_timer(self, mock_set_timer):
        mock_set_timer.return_value = {"status": "success", "minutes": 7}
        
        response = client.get("/api/hue/timer/7")
        assert response.status_code == 200
    
    @patch('services.hue_service.hue_service.cancel_timer')
    def test_hue_cancel(self, mock_cancel_timer):
        mock_cancel_timer.return_value = {"status": "success", "message": "Timer cancelled"}
        
        response = client.get("/api/hue/cancel")
        assert response.status_code == 200


class TestWemoEndpoints:
    
    @patch('services.wemo_service.wemo_service.get_all_status')
    def test_get_wemo_status(self, mock_get_status):
        mock_get_status.return_value = {"coffee": {"name": "coffee", "is_on": True}}
        
        response = client.get("/api/wemo/status")
        assert response.status_code == 200
    
    @patch('services.wemo_service.wemo_service.toggle')
    def test_wemo_toggle(self, mock_toggle):
        mock_toggle.return_value = {"status": "success", "device": "coffee"}
        
        response = client.get("/api/wemo/coffee/toggle")
        assert response.status_code == 200
