import asyncio
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
        self.light_name = os.getenv("HUE_LIGHT_NAME", "Baby room")
        self.timer_task: Optional[asyncio.Task] = None
    
    def connect(self) -> bool:
        try:
            bridge_ip = os.getenv("HUE_BRIDGE_IP")
            if not bridge_ip:
                logger.error("HUE_BRIDGE_IP not set")
                return False
            logger.info(f"Connecting to Hue Bridge at {bridge_ip}")
            self.bridge = Bridge(bridge_ip)
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
                "timer_active": self.timer_task is not None and not self.timer_task.done()
            }
        except OSError as e:
            logger.warning(f"Hue Bridge unreachable: {e}")
            err_msg = "Hue Bridge 不可达" if "route to host" in str(e).lower() or "errno 65" in str(e).lower() else str(e)
            return {"name": self.light_name, "error": err_msg, "is_on": False, "brightness": 0, "timer_active": False}
    
    def turn_off(self) -> dict:
        if not self.bridge:
            return {"status": "error", "message": "Bridge not connected"}
        try:
            light_id = self._get_light_id()
            if light_id is None:
                return {"status": "error", "message": f"Light {self.light_name} not found"}
            if self.timer_task and not self.timer_task.done():
                self.timer_task.cancel()
                self.timer_task = None
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
    
    async def _turn_off_after_delay(self, light_id: int, minutes: float, brightness: int):
        try:
            await asyncio.sleep(minutes * 60)
            if self.bridge:
                self.bridge.set_light(light_id, 'on', False)
                logger.info(f"Light {self.light_name} turned off after {minutes} minutes")
        except asyncio.CancelledError:
            logger.info(f"Timer for {self.light_name} cancelled")
            raise
    
    def set_timer(self, minutes: float, brightness: int = 10) -> dict:
        if not self.bridge:
            return {"status": "error", "message": "Bridge not connected"}
        try:
            light_id = self._get_light_id()
            if light_id is None:
                return {"status": "error", "message": f"Light {self.light_name} not found"}
            timer_reset = False
            if self.timer_task and not self.timer_task.done():
                self.timer_task.cancel()
                timer_reset = True
                logger.info(f"Cancelled existing timer, creating new {minutes}-minute timer")
            self.bridge.set_light(light_id, {'on': True, 'bri': brightness})
            turn_off_time = datetime.now().timestamp() + minutes * 60
            self.timer_task = asyncio.create_task(
                self._turn_off_after_delay(light_id, minutes, brightness)
            )
            return {
                "status": "success",
                "light": self.light_name,
                "action": "timer",
                "brightness": brightness,
                "minutes": minutes,
                "turn_off_at": datetime.fromtimestamp(turn_off_time).isoformat(),
                "timer_reset": timer_reset
            }
        except OSError as e:
            logger.warning(f"Hue Bridge unreachable: {e}")
            msg = "Hue Bridge 不可达" if "route to host" in str(e).lower() or "errno 65" in str(e).lower() else str(e)
            return {"status": "error", "message": msg}
    
    def cancel_timer(self) -> dict:
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
            self.timer_task = None
            return {
                "status": "success",
                "light": self.light_name,
                "message": "Timer cancelled",
                "timestamp": datetime.now().isoformat()
            }
        return {
            "status": "success",
            "light": self.light_name,
            "message": "No active timer"
        }

hue_service = HueService()
