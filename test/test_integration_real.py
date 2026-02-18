import pytest
import asyncio
from unittest.mock import patch, AsyncMock

pytestmark = pytest.mark.skip(reason="集成测试需要真实设备，默认跳过。运行: pytest -m integration")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.mark.integration
class TestHueIntegration:
    """Hue 灯光集成测试"""
    
    def test_hue_status_real(self, client):
        """测试获取真实 Hue 状态"""
        response = client.get("/api/hue/status")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "is_on" in data
    
    def test_hue_toggle_real(self, client):
        """测试真实切换 Hue"""
        response = client.get("/api/hue/toggle")
        assert response.status_code == 200
        
        response2 = client.get("/api/hue/toggle")
        assert response2.status_code == 200
    
    def test_hue_timer_real(self, client):
        """测试真实 Timer 功能"""
        response = client.get("/api/hue/timer/0.05?brightness=10")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        cancel_response = client.get("/api/hue/cancel")
        assert cancel_response.status_code == 200


@pytest.mark.integration
class TestWemoIntegration:
    """Wemo 开关集成测试"""
    
    def test_wemo_status_real(self, client):
        """测试获取真实 Wemo 状态"""
        response = client.get("/api/wemo/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
    
    def test_wemo_toggle_real(self, client):
        """测试真实切换 Wemo"""
        response = client.get("/api/wemo/coffee/toggle")
        assert response.status_code == 200
        
        response2 = client.get("/api/wemo/coffee/toggle")
        assert response2.status_code == 200


@pytest.mark.integration
class TestRinnaiIntegration:
    """Rinnai 热水器集成测试"""
    
    def test_rinnai_status_real(self, client):
        """测试获取真实 Rinnai 状态"""
        response = client.get("/api/rinnai/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_online" in data
    
    def test_rinnai_schedules_real(self, client):
        """测试获取真实 Rinnai Schedules"""
        response = client.get("/api/rinnai/schedules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.integration
class TestGarageIntegration:
    """车库门集成测试"""
    
    def test_garage_status_real(self, client):
        """测试获取真实车库门状态"""
        response = client.get("/api/garage/status")
        assert response.status_code == 200
        data = response.json()
        assert "door_count" in data


@pytest.mark.integration
class TestHistoryIntegration:
    """历史数据集成测试"""
    
    def test_history_api_real(self, client):
        """测试历史数据 API"""
        response = client.get("/api/history?hours=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
