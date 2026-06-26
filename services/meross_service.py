import asyncio
import hashlib
import logging
import os
import secrets
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MerossService:
    def __init__(self):
        self.client = None
        self.manager = None
        self.device = None
        self._local_ip = None
        self._key = None
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
                self._local_ip = getattr(self.device, "_inner_ip", None)
                self._key = self.client.cloud_credentials.key
                self._connected = True
                logger.info(f"Connected to Meross device: {self.device.name} ({self._local_ip})")
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

    def _build_local_message(self, namespace: str, method: str, payload: dict) -> dict:
        timestamp = int(time.time())
        message_id = secrets.token_hex(16)
        sign = hashlib.md5(
            f"{message_id}{self._key}{timestamp}".encode(),
            usedforsecurity=False,
        ).hexdigest()
        return {
            "header": {
                "messageId": message_id,
                "namespace": namespace,
                "method": method,
                "payloadVersion": 1,
                "from": f"http://{self._local_ip}/config",
                "triggerSrc": "AndroidLocal",
                "timestamp": timestamp,
                "timestampMs": 0,
                "sign": sign,
                "uuid": self.device.uuid,
            },
            "payload": payload,
        }

    def _local_request(self, namespace: str, method: str, payload: dict) -> dict:
        if not self._local_ip or not self._key:
            raise RuntimeError("Meross local IP or key is not available")

        response = requests.post(
            f"http://{self._local_ip}/config",
            json=self._build_local_message(namespace, method, payload),
            timeout=8,
        )
        response.raise_for_status()
        return response.json().get("payload", {})

    def _get_current_open_state(self, door_index: int, current_state: dict) -> bool:
        if "open" in current_state:
            return bool(current_state["open"])
        return bool(self.device.get_is_open(door_index))
    
    async def toggle_door(self, door_index: int) -> dict:
        if not self.device:
            return {"status": "error", "message": "Not connected"}
        
        if door_index < 1 or door_index >= len(self.device.channels):
            return {"status": "error", "message": f"Invalid door index: {door_index}"}
        
        try:
            if not hasattr(self.device, "get_is_open"):
                return {"status": "error", "message": "Connected Meross device is not a garage opener"}

            current_payload = await asyncio.to_thread(
                self._local_request,
                "Appliance.GarageDoor.State",
                "GET",
                {"state": {"channel": door_index}},
            )
            current_state = current_payload.get("state", {})
            current_is_open = self._get_current_open_state(door_index, current_state)
            target_open = 0 if current_is_open else 1
            response_payload = await asyncio.to_thread(
                self._local_request,
                "Appliance.GarageDoor.State",
                "SET",
                {
                    "state": {
                        "channel": door_index,
                        "open": target_open,
                        "uuid": self.device.uuid,
                    }
                },
            )
            state = response_payload.get("state") if isinstance(response_payload, dict) else None
            if isinstance(state, list):
                state = state[0] if state else None
            return {
                "status": "success",
                "door": door_index,
                "action": "toggle",
                "backend": "meross_local_http",
                "previous_state": current_state,
                "target_open": bool(target_open),
                "reported_state": state,
                "executed": state.get("execute") if isinstance(state, dict) else None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error toggling door {door_index}: {e}")
            return {"status": "error", "message": str(e)}

meross_service = MerossService()
