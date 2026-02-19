import pytest
from unittest.mock import patch, AsyncMock

from models.database import save_device_state, get_device_history, init_db, DB_PATH
from pathlib import Path
import tempfile


class TestScheduler:
    
    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        from models import database
        original_path = database.DB_PATH
        database.DB_PATH = tmp_path / "test.db"
        init_db()
        yield
        database.DB_PATH = original_path
    
    @pytest.mark.asyncio
    async def test_collect_device_states_hue_off_brightness_zero(self):
        with patch('services.scheduler.hue_service') as mock_hue, \
             patch('services.scheduler.wemo_service') as mock_wemo, \
             patch('services.scheduler.rinnai_service') as mock_rinnai:
            
            mock_hue.get_status.return_value = {
                "name": "Baby room",
                "is_on": False,
                "brightness": 128
            }
            mock_wemo.get_all_status.return_value = {}
            mock_rinnai.get_status = AsyncMock(return_value={"error": "skipped"})
            
            from services.scheduler import collect_device_states
            await collect_device_states()
            
            history = get_device_history(device_type="hue", device_name="baby_room", hours=1)
            assert len(history) == 1
            import json
            data = json.loads(history[0]["data"]) if isinstance(history[0]["data"], str) else history[0]["data"]
            assert data["is_on"] == False
            assert data["brightness"] == 0
    
    @pytest.mark.asyncio
    async def test_collect_device_states_hue_on_uses_actual_brightness(self):
        with patch('services.scheduler.hue_service') as mock_hue, \
             patch('services.scheduler.wemo_service') as mock_wemo, \
             patch('services.scheduler.rinnai_service') as mock_rinnai:
            
            mock_hue.get_status.return_value = {
                "name": "Baby room",
                "is_on": True,
                "brightness": 200
            }
            mock_wemo.get_all_status.return_value = {}
            mock_rinnai.get_status = AsyncMock(return_value={"error": "skipped"})
            
            from services.scheduler import collect_device_states
            await collect_device_states()
            
            history = get_device_history(device_type="hue", device_name="baby_room", hours=1)
            assert len(history) == 1
            import json
            data = json.loads(history[0]["data"]) if isinstance(history[0]["data"], str) else history[0]["data"]
            assert data["is_on"] == True
            assert data["brightness"] == 200
