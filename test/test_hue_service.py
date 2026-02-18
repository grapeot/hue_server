import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from services.hue_service import HueService


class TestHueService:
    
    @pytest.fixture
    def hue_service(self):
        service = HueService()
        service.light_name = "Baby room"
        return service
    
    def test_get_status_bridge_not_connected(self, hue_service):
        result = hue_service.get_status()
        assert "error" in result
        assert result["is_on"] == False
    
    @patch('services.hue_service.Bridge')
    def test_connect_success(self, mock_bridge, hue_service):
        mock_bridge_instance = Mock()
        mock_bridge.return_value = mock_bridge_instance
        
        with patch.dict('os.environ', {'HUE_BRIDGE_IP': '192.168.1.1'}):
            result = hue_service.connect()
        
        assert result == True
        assert hue_service.bridge is not None
    
    def test_turn_off_no_bridge(self, hue_service):
        result = hue_service.turn_off()
        assert result["status"] == "error"
    
    def test_turn_on_no_bridge(self, hue_service):
        result = hue_service.turn_on(brightness=128)
        assert result["status"] == "error"
    
    def test_set_timer_no_bridge(self, hue_service):
        result = hue_service.set_timer(7, brightness=10)
        assert result["status"] == "error"
    
    def test_cancel_timer_no_active_timer(self, hue_service):
        result = hue_service.cancel_timer()
        assert result["status"] == "success"
        assert "No active timer" in result["message"]
