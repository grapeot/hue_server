import logging
import os
from typing import Dict, Optional
from datetime import datetime

import pywemo
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class WemoService:
    def __init__(self):
        self.devices: Dict[str, pywemo.WeMoDevice] = {}
        self.config_file = os.getenv("WEMO_CONFIG_FILE", "wemo_config.yaml")
    
    def init_devices(self) -> bool:
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Wemo config file not found: {self.config_file}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            devices_config = config.get('devices', [])
            logger.info(f"Loading {len(devices_config)} Wemo devices from config")
            
            for device_config in devices_config:
                name = device_config.get('name', '')
                host = device_config.get('host', '')
                port = device_config.get('port', 49153)
                
                if not name or not host:
                    continue
                
                try:
                    url = pywemo.setup_url_for_address(host, port)
                    device = pywemo.device_from_description(url)
                    self.devices[name.lower()] = device
                    logger.info(f"Registered Wemo device: {name} ({host}:{port})")
                except Exception as e:
                    logger.warning(f"Failed to connect to {name}: {e}")
            
            return len(self.devices) > 0
        except Exception as e:
            logger.error(f"Error initializing Wemo devices: {e}")
            return False
    
    def get_all_status(self) -> dict:
        result = {}
        for name, device in self.devices.items():
            try:
                state = device.get_state()
                result[name] = {
                    "name": name,
                    "is_on": state,
                    "host": device.host
                }
            except Exception as e:
                result[name] = {
                    "name": name,
                    "is_on": None,
                    "error": str(e)
                }
        return result
    
    def get_device(self, name: str) -> Optional[pywemo.WeMoDevice]:
        return self.devices.get(name.lower())
    
    def turn_on(self, name: str) -> dict:
        device = self.get_device(name)
        if not device:
            return {"status": "error", "message": f"Device {name} not found"}
        
        try:
            device.on()
            return {
                "status": "success",
                "device": name,
                "action": "on",
                "is_on": device.get_state(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def turn_off(self, name: str) -> dict:
        device = self.get_device(name)
        if not device:
            return {"status": "error", "message": f"Device {name} not found"}
        
        try:
            device.off()
            return {
                "status": "success",
                "device": name,
                "action": "off",
                "is_on": device.get_state(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def toggle(self, name: str) -> dict:
        device = self.get_device(name)
        if not device:
            return {"status": "error", "message": f"Device {name} not found"}
        
        try:
            current_state = device.get_state()
            if current_state:
                device.off()
            else:
                device.on()
            
            return {
                "status": "success",
                "device": name,
                "action": "toggle",
                "is_on": device.get_state(),
                "previous_state": current_state,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

wemo_service = WemoService()
