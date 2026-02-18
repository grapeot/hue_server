import asyncio
import logging
import os
from typing import Optional
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MerossService:
    def __init__(self):
        self.client = None
        self.manager = None
        self.device = None
        self._connected = False
    
    async def connect(self) -> bool:
        email = os.getenv("MEROSS_EMAIL")
        password = os.getenv("MEROSS_PASSWORD")
        
        if not email or not password:
            logger.error("MEROSS_EMAIL or MEROSS_PASSWORD not set")
            return False
        
        try:
            from meross_iot.http_api import MerossHttpClient
            from meross_iot.manager import MerossManager
            
            self.client = await MerossHttpClient.async_from_user_password(
                api_base_url='https://iot.meross.com',
                email=email,
                password=password
            )
            
            self.manager = MerossManager(http_client=self.client)
            await self.manager.async_init()
            await self.manager.async_device_discovery()
            await asyncio.sleep(2)
            
            devices = self.manager.find_devices()
            if devices:
                self.device = devices[0]
                await self.device.async_update()
                self._connected = True
                logger.info(f"Connected to Meross device: {self.device.name}")
                return True
            else:
                logger.error("No Meross devices found")
                return False
        except Exception as e:
            logger.error(f"Error connecting to Meross: {e}")
            return False
    
    async def close(self):
        pass
    
    def get_door_count(self) -> int:
        if not self.device:
            return 0
        return len(self.device.channels) - 1
    
    async def toggle_door(self, door_index: int) -> dict:
        if not self.device:
            return {"status": "error", "message": "Not connected"}
        
        if door_index < 1 or door_index >= len(self.device.channels):
            return {"status": "error", "message": f"Invalid door index: {door_index}"}
        
        try:
            await self.device.async_toggle(door_index)
            return {
                "status": "success",
                "door": door_index,
                "action": "toggle",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error toggling door {door_index}: {e}")
            return {"status": "error", "message": str(e)}

meross_service = MerossService()
