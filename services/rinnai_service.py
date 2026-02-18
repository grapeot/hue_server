import asyncio
import logging
import os
from typing import Optional
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RinnaiService:
    def __init__(self):
        self.api = None
        self.device_id: Optional[str] = None
        self._connected = False
    
    async def connect(self) -> bool:
        username = os.getenv("RINNAI_USERNAME")
        password = os.getenv("RINNAI_PASSWORD")
        
        if not username or not password:
            logger.error("RINNAI_USERNAME or RINNAI_PASSWORD not set")
            return False
        
        try:
            from aiorinnai import API
            self.api = API()
            await self.api.async_login(username, password)
            
            user_info = await self.api.user.get_info()
            devices = user_info.get("devices", {}).get("items", [])
            
            if devices:
                self.device_id = devices[0].get("id")
                self._connected = True
                logger.info(f"Connected to Rinnai device: {self.device_id}")
                return True
            else:
                logger.error("No Rinnai devices found")
                return False
        except Exception as e:
            logger.error(f"Error connecting to Rinnai: {e}")
            return False
    
    async def close(self):
        if self.api:
            await self.api.close()
    
    async def get_status(self) -> dict:
        if not self.api or not self.device_id:
            return {"error": "Not connected", "is_online": False}
        
        try:
            info = await self.api.device.get_info(self.device_id)
            data = info.get("data", {}).get("getDevice", {})
            shadow = data.get("shadow", {})
            sensor = data.get("info", {})
            
            return {
                "device_id": self.device_id,
                "name": data.get("device_name", "Unknown"),
                "is_online": True,
                "set_temperature": int(shadow.get("set_domestic_temperature", 0)),
                "operation_enabled": shadow.get("operation_enabled", False),
                "recirculation_enabled": shadow.get("recirculation_enabled", False),
                "inlet_temp": int(sensor.get("m08_inlet_temperature", 0)),
                "outlet_temp": int(sensor.get("m02_outlet_temperature", 0)),
                "water_flow": int(sensor.get("m01_water_flow_rate_raw", 0)),
                "firmware": data.get("firmware", "unknown")
            }
        except Exception as e:
            logger.error(f"Error getting Rinnai status: {e}")
            return {"error": str(e), "is_online": False}
    
    async def start_circulation(self, duration: int = 5) -> dict:
        if not self.api or not self.device_id:
            return {"status": "error", "message": "Not connected"}
        
        try:
            user_info = await self.api.user.get_info()
            devices = user_info.get("devices", {}).get("items", [])
            if devices:
                device = devices[0]
                await self.api.device.start_recirculation(device, duration)
                return {
                    "status": "success",
                    "device": self.device_id,
                    "action": "circulation",
                    "duration_minutes": duration,
                    "timestamp": datetime.now().isoformat()
                }
            return {"status": "error", "message": "Device not found"}
        except Exception as e:
            logger.error(f"Error starting circulation: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_schedules(self) -> list:
        if not self.api or not self.device_id:
            return []
        
        try:
            info = await self.api.device.get_info(self.device_id)
            schedules = info.get("data", {}).get("getDevice", {}).get("schedule", {}).get("items", [])
            
            result = []
            for s in schedules:
                result.append({
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "days": s.get("days", []),
                    "times": s.get("times", []),
                    "active": s.get("active", False)
                })
            return result
        except Exception as e:
            logger.error(f"Error getting schedules: {e}")
            return []

rinnai_service = RinnaiService()
