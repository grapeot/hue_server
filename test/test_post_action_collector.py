import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestPostActionCollector:
    
    @pytest.mark.asyncio
    async def test_schedule_collection_creates_task(self):
        from services.post_action_collector import schedule_collection
        
        with patch("services.post_action_collector._collect_and_save") as mock_collect:
            mock_collect.return_value = AsyncMock()
            
            await schedule_collection("hue", "baby_room", delay_seconds=0.1)
            
            await asyncio.sleep(0.05)
            
            assert mock_collect.call_count == 1
    
    @pytest.mark.asyncio
    async def test_collect_and_save_hue(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.hue_service") as mock_hue:
            mock_hue.get_status.return_value = {
                "is_on": True,
                "brightness": 128,
            }
            with patch("services.post_action_collector.save_device_state") as mock_save:
                await _collect_and_save("hue", "baby_room", delay_seconds=0.01)
                
                mock_save.assert_called_once_with(
                    "hue", "baby_room", {"is_on": True, "brightness": 128}
                )
    
    @pytest.mark.asyncio
    async def test_collect_and_save_hue_off(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.hue_service") as mock_hue:
            mock_hue.get_status.return_value = {
                "is_on": False,
                "brightness": 200,
            }
            with patch("services.post_action_collector.save_device_state") as mock_save:
                await _collect_and_save("hue", "baby_room", delay_seconds=0.01)
                
                mock_save.assert_called_once_with(
                    "hue", "baby_room", {"is_on": False, "brightness": 0}
                )
    
    @pytest.mark.asyncio
    async def test_collect_and_save_wemo(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.wemo_service") as mock_wemo:
            mock_wemo.get_all_status.return_value = {
                "coffee": {"is_on": True},
                "tree": {"is_on": False},
            }
            with patch("services.post_action_collector.save_device_state") as mock_save:
                await _collect_and_save("wemo", "coffee", delay_seconds=0.01)
                
                mock_save.assert_called_once_with(
                    "wemo", "coffee", {"is_on": True}
                )
    
    @pytest.mark.asyncio
    async def test_collect_and_save_wemo_case_insensitive(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.wemo_service") as mock_wemo:
            mock_wemo.get_all_status.return_value = {
                "coffee": {"is_on": True},
            }
            with patch("services.post_action_collector.save_device_state") as mock_save:
                await _collect_and_save("wemo", "Coffee", delay_seconds=0.01)
                
                mock_save.assert_called_once_with(
                    "wemo", "Coffee", {"is_on": True}
                )
    
    @pytest.mark.asyncio
    async def test_collect_and_save_wemo_not_found(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.wemo_service") as mock_wemo:
            mock_wemo.get_all_status.return_value = {
                "coffee": {"is_on": True},
            }
            with patch("services.post_action_collector.save_device_state") as mock_save:
                await _collect_and_save("wemo", "nonexistent", delay_seconds=0.01)
                
                mock_save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_collect_and_save_rinnai(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.rinnai_service") as mock_rinnai:
            mock_rinnai.get_status = AsyncMock(return_value={
                "set_temperature": 125,
                "inlet_temp": 103,
                "outlet_temp": 121,
                "water_flow": 26,
                "recirculation_enabled": True,
            })
            with patch("services.post_action_collector.save_device_state") as mock_save:
                await _collect_and_save("rinnai", "main_house", delay_seconds=0.01)
                
                mock_save.assert_called_once_with(
                    "rinnai", "main_house", {
                        "set_temperature": 125,
                        "inlet_temp": 103,
                        "outlet_temp": 121,
                        "water_flow": 26,
                        "recirculation_enabled": True,
                    }
                )
    
    @pytest.mark.asyncio
    async def test_collect_and_save_rinnai_zero_temp_skipped(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.rinnai_service") as mock_rinnai:
            mock_rinnai.get_status = AsyncMock(return_value={
                "set_temperature": 125,
                "inlet_temp": 0,
                "outlet_temp": 0,
                "water_flow": 0,
            })
            with patch("services.post_action_collector.save_device_state") as mock_save:
                await _collect_and_save("rinnai", "main_house", delay_seconds=0.01)
                
                mock_save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_collect_and_save_handles_error(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.hue_service") as mock_hue:
            mock_hue.get_status.side_effect = Exception("Connection failed")
            with patch("services.post_action_collector.save_device_state") as mock_save:
                await _collect_and_save("hue", "baby_room", delay_seconds=0.01)
                
                mock_save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_collect_and_save_unknown_device_type(self):
        from services.post_action_collector import _collect_and_save
        
        with patch("services.post_action_collector.save_device_state") as mock_save:
            await _collect_and_save("unknown", "device", delay_seconds=0.01)
            
            mock_save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fetch_device_status_with_error_in_status(self):
        from services.post_action_collector import _fetch_device_status
        
        with patch("services.post_action_collector.hue_service") as mock_hue:
            mock_hue.get_status.return_value = {"error": "Device offline"}
            
            result = await _fetch_device_status("hue", "baby_room")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_device_status_wemo_with_error(self):
        from services.post_action_collector import _fetch_device_status
        
        with patch("services.post_action_collector.wemo_service") as mock_wemo:
            mock_wemo.get_all_status.return_value = {
                "coffee": {"error": "Connection failed"},
            }
            
            result = await _fetch_device_status("wemo", "coffee")
            
            assert result is None
