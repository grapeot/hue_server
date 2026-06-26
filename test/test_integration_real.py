import pytest
import asyncio
from unittest.mock import patch, AsyncMock

pytestmark = pytest.mark.skip(reason="Integration tests require real devices and are skipped by default. Run: pytest -m integration")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.mark.integration
class TestHueIntegration:
    """Hue light integration tests."""
    
    def test_hue_status_real(self, client):
        """Test real Hue status."""
        response = client.get("/api/hue/status")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "is_on" in data
    
    def test_hue_toggle_real(self, client):
        """Test real Hue toggle."""
        response = client.get("/api/hue/toggle")
        assert response.status_code == 200
        
        response2 = client.get("/api/hue/toggle")
        assert response2.status_code == 200
    
    def test_hue_timer_real(self, client):
        """Test real Hue timer."""
        response = client.get("/api/hue/timer/0.05?brightness=10")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        cancel_response = client.get("/api/hue/cancel")
        assert cancel_response.status_code == 200


@pytest.mark.integration
class TestWemoIntegration:
    """Wemo switch integration tests."""
    
    def test_wemo_status_real(self, client):
        """Test real Wemo status."""
        response = client.get("/api/wemo/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
    
    def test_wemo_toggle_real(self, client):
        """Test real Wemo toggle."""
        response = client.get("/api/wemo/coffee/toggle")
        assert response.status_code == 200
        
        response2 = client.get("/api/wemo/coffee/toggle")
        assert response2.status_code == 200


@pytest.mark.integration
class TestRinnaiIntegration:
    """Rinnai water heater integration tests."""
    
    def test_rinnai_status_real(self, client):
        """Test real Rinnai status."""
        response = client.get("/api/rinnai/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_online" in data
    
    def test_rinnai_schedules_real(self, client):
        """Test real Rinnai schedules."""
        response = client.get("/api/rinnai/schedules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.integration
class TestGarageIntegration:
    """Garage door integration tests."""
    
    def test_garage_status_real(self, client):
        """Test real garage status."""
        response = client.get("/api/garage/status")
        assert response.status_code == 200
        data = response.json()
        assert "door_count" in data


@pytest.mark.integration
class TestHistoryIntegration:
    """History integration tests."""
    
    def test_history_api_real(self, client):
        """Test history API."""
        response = client.get("/api/history?hours=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
