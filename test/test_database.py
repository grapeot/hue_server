import pytest
import tempfile
import os

from models.database import (
    get_connection,
    init_db,
    save_device_state,
    get_device_history
)


class TestDatabase:
    
    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        from models import database
        original_path = database.DB_PATH
        database.DB_PATH = tmp_path / "test.db"
        init_db()
        yield
        database.DB_PATH = original_path
    
    def test_save_and_get_hue_state(self):
        save_device_state("hue", "baby_room", {"is_on": True, "brightness": 128})
        
        history = get_device_history(device_type="hue", device_name="baby_room", hours=1)
        
        assert len(history) == 1
        assert history[0]["device_type"] == "hue"
        assert history[0]["device_name"] == "baby_room"
    
    def test_save_and_get_wemo_state(self):
        save_device_state("wemo", "coffee", {"is_on": True})
        
        history = get_device_history(device_type="wemo", device_name="coffee", hours=1)
        
        assert len(history) == 1
    
    def test_save_and_get_rinnai_state(self):
        save_device_state("rinnai", "main_house", {
            "set_temperature": 125,
            "inlet_temp": 103,
            "outlet_temp": 121
        })
        
        history = get_device_history(device_type="rinnai", device_name="main_house", hours=1)
        
        assert len(history) == 1
    
    def test_get_all_device_history(self):
        save_device_state("hue", "baby_room", {"is_on": True})
        save_device_state("wemo", "coffee", {"is_on": False})
        
        history = get_device_history(hours=1)
        
        assert len(history) == 2
