import logging
import os
from datetime import datetime
from typing import Optional

from phue import Bridge
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class HueService:
    def __init__(self):
        self.bridge: Optional[Bridge] = None
        self.bridge_ip: Optional[str] = os.getenv("HUE_BRIDGE_IP")
        self.light_name = os.getenv("HUE_LIGHT_NAME", "Baby room")
    
    def connect(self) -> bool:
        try:
            self.bridge_ip = os.getenv("HUE_BRIDGE_IP")
            if not self.bridge_ip:
                logger.error("HUE_BRIDGE_IP not set")
                return False
            logger.info(f"Connecting to Hue Bridge at {self.bridge_ip}")
            self.bridge = Bridge(self.bridge_ip)
            self.bridge.connect()
            logger.info("Connected to Hue Bridge")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Hue Bridge: {e}")
            return False
    
    def _get_light_id(self) -> Optional[int]:
        if not self.bridge:
            return None
        for light in self.bridge.lights:
            if light.name == self.light_name:
                return light.light_id
        return None
    
    def get_status(self) -> dict:
        if not self.bridge:
            return {"error": "Bridge not connected", "is_on": False, "brightness": 0}
        try:
            light_id = self._get_light_id()
            if light_id is None:
                return {"error": f"Light {self.light_name} not found", "is_on": False, "brightness": 0}
            light = self.bridge.get_light(light_id)
            state = light.get("state", {})
            return {
                "name": self.light_name,
                "is_on": state.get("on", False),
                "brightness": state.get("bri", 0),
            }
        except OSError as e:
            logger.warning(f"Hue Bridge unreachable: {e}")
            err_msg = "Hue Bridge 不可达" if "route to host" in str(e).lower() or "errno 65" in str(e).lower() else str(e)
            return {"name": self.light_name, "error": err_msg, "is_on": False, "brightness": 0}
    
    def turn_off(self) -> dict:
        if not self.bridge:
            return {"status": "error", "message": "Bridge not connected"}
        try:
            light_id = self._get_light_id()
            if light_id is None:
                return {"status": "error", "message": f"Light {self.light_name} not found"}
            self.bridge.set_light(light_id, 'on', False)
            return {
                "status": "success",
                "light": self.light_name,
                "action": "off",
                "timestamp": datetime.now().isoformat()
            }
        except OSError as e:
            logger.warning(f"Hue Bridge unreachable: {e}")
            msg = "Hue Bridge 不可达" if "route to host" in str(e).lower() or "errno 65" in str(e).lower() else str(e)
            return {"status": "error", "message": msg}
    
    def turn_on(self, brightness: int = 128) -> dict:
        if not self.bridge:
            return {"status": "error", "message": "Bridge not connected"}
        try:
            light_id = self._get_light_id()
            if light_id is None:
                return {"status": "error", "message": f"Light {self.light_name} not found"}
            self.bridge.set_light(light_id, {'on': True, 'bri': brightness})
            return {
                "status": "success",
                "light": self.light_name,
                "action": "on",
                "brightness": brightness,
                "timestamp": datetime.now().isoformat()
            }
        except OSError as e:
            logger.warning(f"Hue Bridge unreachable: {e}")
            msg = "Hue Bridge 不可达" if "route to host" in str(e).lower() or "errno 65" in str(e).lower() else str(e)
            return {"status": "error", "message": msg}
    
    def toggle(self) -> dict:
        status = self.get_status()
        if status.get("error"):
            return {"status": "error", "message": status["error"]}
        if status.get("is_on"):
            return self.turn_off()
        else:
            return self.turn_on()

hue_service = HueService()
