import asyncio
import hashlib
import logging
import os
import secrets
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

from services.notification_service import notification_service

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
        self._verify_timeout_seconds = float(os.getenv("MEROSS_GARAGE_VERIFY_TIMEOUT_SECONDS", "20"))
        self._verify_poll_interval_seconds = float(os.getenv("MEROSS_GARAGE_VERIFY_POLL_INTERVAL_SECONDS", "2"))

    def _select_garage_device(self, devices: list):
        expected_uuid = os.getenv("MEROSS_GARAGE_UUID")
        expected_name = os.getenv("MEROSS_GARAGE_NAME")

        if expected_uuid:
            for device in devices:
                if getattr(device, "uuid", None) == expected_uuid:
                    return device
            return None

        if expected_name:
            expected_name_lower = expected_name.lower()
            for device in devices:
                if getattr(device, "name", "").lower() == expected_name_lower:
                    return device
            return None

        if len(devices) == 1:
            return devices[0]

        return None
    
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
            selected_device = self._select_garage_device(devices)
            if selected_device:
                self.device = selected_device
                await self.device.async_update()
                self._local_ip = getattr(self.device, "_inner_ip", None)
                self._key = self.client.cloud_credentials.key
                self._connected = True
                logger.info(f"Connected to Meross device: {self.device.name} ({self._local_ip})")
                return True
            else:
                logger.error("No matching Meross garage device found; set MEROSS_GARAGE_UUID or MEROSS_GARAGE_NAME")
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

    def _read_door_state(self, door_index: int) -> tuple[dict, bool]:
        payload = self._local_request(
            "Appliance.GarageDoor.State",
            "GET",
            {"state": {"channel": door_index}},
        )
        state = payload.get("state", {}) if isinstance(payload, dict) else {}
        return state, self._get_current_open_state(door_index, state)

    async def _wait_for_target_state(self, door_index: int, target_open: bool) -> tuple[bool, dict]:
        timeout = max(0.0, self._verify_timeout_seconds)
        interval = max(0.1, self._verify_poll_interval_seconds)
        deadline = time.monotonic() + timeout
        last_state = {}

        while True:
            last_state, is_open = await asyncio.to_thread(self._read_door_state, door_index)
            if is_open == target_open:
                return True, last_state

            if time.monotonic() >= deadline:
                return False, last_state

            await asyncio.sleep(min(interval, max(0.0, deadline - time.monotonic())))
    
    async def toggle_door(self, door_index: int) -> dict:
        if not self.device:
            return {"status": "error", "message": "Not connected"}
        
        if door_index < 1 or door_index >= len(self.device.channels):
            return {"status": "error", "message": f"Invalid door index: {door_index}"}
        
        try:
            if not hasattr(self.device, "get_is_open"):
                return {"status": "error", "message": "Connected Meross device is not a garage opener"}

            current_state, current_is_open = await asyncio.to_thread(self._read_door_state, door_index)
            target_open = not current_is_open
            response_payload = await asyncio.to_thread(
                self._local_request,
                "Appliance.GarageDoor.State",
                "SET",
                {
                    "state": {
                        "channel": door_index,
                        "open": int(target_open),
                        "uuid": self.device.uuid,
                    }
                },
            )
            state = response_payload.get("state") if isinstance(response_payload, dict) else None
            if isinstance(state, list):
                state = state[0] if state else None
            verified, final_state = await self._wait_for_target_state(door_index, target_open)
            status = "success" if verified else "triggered_unverified"
            result = {
                "status": status,
                "door": door_index,
                "action": "toggle",
                "backend": "meross_local_http",
                "previous_state": current_state,
                "target_open": target_open,
                "reported_state": state,
                "final_state": final_state,
                "verified": verified,
                "executed": state.get("execute") if isinstance(state, dict) else None,
                "timestamp": datetime.now().isoformat()
            }
            if not verified:
                result["message"] = "Garage command was sent, but final door state was not verified"
            try:
                result["notification"] = await asyncio.to_thread(
                    notification_service.send_garage_toggle,
                    result,
                )
            except Exception as e:
                logger.error(f"Error sending garage notification: {e}")
                result["notification"] = {"enabled": True, "sent": False, "error": str(e)}
            return result
        except Exception as e:
            logger.error(f"Error toggling door {door_index}: {e}")
            return {"status": "error", "message": str(e)}

meross_service = MerossService()
