import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock

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

    @patch('services.wemo_service.wemo_service.get_all_status')
    def test_get_status_devices_wemo_only(self, mock_wemo):
        mock_wemo.return_value = {"coffee": {"name": "coffee", "is_on": True}}
        response = client.get("/api/status?devices=wemo")
        assert response.status_code == 200
        data = response.json()
        assert "wemo" in data
        assert "hue" not in data
        assert "rinnai" not in data
        assert "garage" not in data


class TestHistoryEndpoint:

    @patch('api.history.get_device_history')
    def test_history_timestamps_have_utc_suffix(self, mock_get_history):
        mock_get_history.return_value = [
            {
                "id": 1,
                "device_type": "rinnai",
                "device_name": "main_house",
                "timestamp": "2026-02-19 00:47:05",
                "data": {"inlet_temp": 66, "outlet_temp": 125},
            },
        ]
        response = client.get("/api/history?hours=24")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == "2026-02-19T00:47:05Z"


class TestScheduleEndpoints:
    
    def test_create_action(self):
        with patch('api.schedule.dynamic_scheduler.schedule') as mock_schedule:
            mock_action = Mock()
            mock_action.to_dict.return_value = {
                'id': 'test123',
                'action': {'type': 'wemo.off', 'params': {'device': 'tree'}},
                'action_display': '关闭 tree',
                'minutes': 5,
                'created_at': '2026-02-19T12:00:00',
                'execute_at': '2026-02-19T12:05:00',
                'status': 'pending',
            }
            mock_schedule.return_value = mock_action
            
            response = client.post("/api/schedule/actions", json={
                "minutes": 5,
                "action": {"type": "wemo.off", "params": {"device": "tree"}}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["action"]["type"] == "wemo.off"
            assert data["minutes"] == 5
            assert data["status"] == "pending"
    
    def test_create_action_invalid_minutes(self):
        response = client.post("/api/schedule/actions", json={
            "minutes": 0,
            "action": {"type": "wemo.off", "params": {}}
        })
        assert response.status_code == 400
    
    def test_list_actions(self):
        with patch('api.schedule.dynamic_scheduler.get_all') as mock_get_all:
            mock_get_all.return_value = []
            
            response = client.get("/api/schedule/actions")
            assert response.status_code == 200
            data = response.json()
            assert "actions" in data
    
    def test_list_actions_with_status_filter(self):
        with patch('api.schedule.dynamic_scheduler.get_all') as mock_get_all:
            mock_get_all.return_value = []
            
            response = client.get("/api/schedule/actions?status=pending")
            assert response.status_code == 200
            data = response.json()
            assert "actions" in data
    
    def test_cancel_action(self):
        with patch('api.schedule.dynamic_scheduler.cancel') as mock_cancel:
            mock_action = Mock()
            mock_action.to_dict.return_value = {
                'id': 'test123',
                'status': 'cancelled',
            }
            mock_cancel.return_value = mock_action
            
            response = client.delete("/api/schedule/actions/test123")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"
    
    def test_cancel_nonexistent_action(self):
        with patch('api.schedule.dynamic_scheduler.cancel') as mock_cancel:
            mock_cancel.return_value = None
            
            response = client.delete("/api/schedule/actions/nonexistent")
            assert response.status_code == 404
