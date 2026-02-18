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
    
    def test_root_serves_spa(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "<!doctype html>" in response.text.lower() or "<html" in response.text.lower()


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


class TestRinnaiEndpoints:

    @patch('api.rinnai.rinnai_service.get_status', new_callable=AsyncMock)
    def test_get_rinnai_status(self, mock_get_status):
        mock_get_status.return_value = {
            "device_id": "test-device",
            "is_online": True,
            "set_temperature": 120
        }

        response = client.get("/api/rinnai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_online"] is True
        assert data["set_temperature"] == 120

    @patch('api.rinnai.rinnai_service.trigger_maintenance_retrieval', new_callable=AsyncMock)
    def test_get_rinnai_maintenance(self, mock_maintenance):
        mock_maintenance.return_value = {"status": "success", "is_online": True}

        response = client.get("/api/rinnai/maintenance")
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestStatusEndpoint:

    @patch('api.status.rinnai_service.get_status', new_callable=AsyncMock)
    def test_get_status_with_rinnai_refresh(self, mock_rinnai_status):
        mock_rinnai_status.return_value = {
            "device_id": "test",
            "is_online": True,
            "set_temperature": 125,
        }

        response = client.get("/api/status?rinnai_refresh=true")
        assert response.status_code == 200
        data = response.json()
        assert "rinnai" in data
        assert data["rinnai"]["is_online"] is True
        mock_rinnai_status.assert_called_once_with(trigger_maintenance=True)
