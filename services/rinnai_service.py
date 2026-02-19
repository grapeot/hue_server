import asyncio
import logging
import os
import inspect
from datetime import datetime
from typing import Any, Optional, Callable, Awaitable

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class RinnaiService:
    def __init__(self):
        self.api: Optional[Any] = None
        self.device_id: Optional[str] = None
        self._device: Optional[dict] = None
        self._connected = False
        self._connect_lock = asyncio.Lock()

    def _to_int(self, value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _response_status(self, response) -> tuple[bool, str]:
        """Normalize aiorinnai response formats to (success, error_message)."""
        if response is None:
            return False, "empty response"

        if isinstance(response, dict):
            success = bool(response.get("success", True))
            raw_error = response.get("error")
            error = str(raw_error) if raw_error else ""
            return success, error

        if hasattr(response, "success"):
            success = bool(getattr(response, "success"))
            raw_error = getattr(response, "error", None)
            return success, str(raw_error) if raw_error else ""

        return True, ""

    async def connect(self) -> bool:
        username = os.getenv("RINNAI_USERNAME")
        password = os.getenv("RINNAI_PASSWORD")

        if not username or not password:
            logger.error("RINNAI_USERNAME or RINNAI_PASSWORD not set")
            return False

        try:
            from aiorinnai import API

            username_str = str(username)
            password_str = str(password)
            self.api = API()
            await self.api.async_login(username_str, password_str)

            user_info = await self.api.user.get_info()
            devices = user_info.get("devices", {}).get("items", [])

            if devices:
                self.device_id = devices[0].get("id")
                self._device = devices[0]
                self._connected = True
                logger.info(f"Connected to Rinnai device: {self.device_id}")
                return True

            logger.error("No Rinnai devices found")
            self._connected = False
            self.api = None
            return False
        except Exception as e:
            logger.error(f"Error connecting to Rinnai: {e}")
            self._connected = False
            self.api = None
            return False

    async def _ensure_connection(self) -> bool:
        if self._connected and self.api and getattr(self.api, "is_connected", False):
            return True

        async with self._connect_lock:
            if self._connected and self.api and getattr(self.api, "is_connected", False):
                return True

            if not self._connected or not self.api:
                return await self.connect()

            check_token = getattr(self.api, "async_check_token", None)
            if callable(check_token):
                try:
                    if inspect.iscoroutinefunction(check_token):
                        await check_token()
                    else:
                        check_token()
                    if getattr(self.api, "is_connected", False):
                        return True
                except Exception as exc:
                    logger.warning(f"Rinnai token check failed: {exc}")

            return await self.connect()

    async def _run_with_connection(self, operation: Callable[[], Awaitable[Any]]):
        if not await self._ensure_connection():
            return None

        try:
            return await operation()
        except Exception as exc:
            logger.warning(f"Rinnai operation failed, reconnecting: {exc}")
            if await self.connect():
                try:
                    return await operation()
                except Exception:
                    logger.exception("Rinnai operation failed after reconnect")
            return None

    async def _get_device(self) -> Optional[dict]:
        api = self.api
        if not api:
            return None

        if self._device and self._device.get("id") == self.device_id:
            return self._device

        try:
            user_info = await api.user.get_info()
            devices = user_info.get("devices", {}).get("items", [])
            for device in devices:
                if device.get("id") == self.device_id:
                    self._device = device
                    return device
            return None
        except Exception as exc:
            logger.error(f"Error getting Rinnai device list: {exc}")
            return None

    async def _get_info(self) -> Optional[dict]:
        api = self.api
        if not self.device_id or not api:
            return None
        info = await api.device.get_info(self.device_id)
        if not isinstance(info, dict):
            return None
        return info

    async def _fetch_status(self) -> dict:
        info = await self._get_info()
        if not info:
            return {"error": "Failed to fetch device info", "is_online": False}

        data = info.get("data", {}).get("getDevice", {})
        shadow = data.get("shadow", {}) or {}
        sensor = data.get("info", {}) or {}

        return {
            "device_id": self.device_id,
            "name": data.get("device_name", "Unknown"),
            "is_online": True,
            "set_temperature": self._to_int(shadow.get("set_domestic_temperature", 0)),
            "operation_enabled": bool(shadow.get("operation_enabled", False)),
            "recirculation_enabled": bool(shadow.get("recirculation_enabled", False)),
            "inlet_temp": self._to_int(sensor.get("m08_inlet_temperature", 0)),
            "outlet_temp": self._to_int(sensor.get("m02_outlet_temperature", 0)),
            "water_flow": self._to_int(sensor.get("m01_water_flow_rate_raw", 0)),
            "firmware": data.get("firmware", "unknown")
        }

    async def get_status(self, trigger_maintenance: bool = False) -> dict:
        if not self.device_id:
            return {"error": "Not connected", "is_online": False}

        if trigger_maintenance:
            maintenance = await self.trigger_maintenance_retrieval(wait_seconds=5, include_status=False)
            if maintenance.get("status") != "success":
                return maintenance

        status = await self._run_with_connection(self._fetch_status)
        if not status or "error" in status:
            return {"error": "Not connected", "is_online": False}

        return status

    async def trigger_maintenance_retrieval(self, wait_seconds: float = 5.0, include_status: bool = True) -> dict:
        if not self.device_id:
            return {"status": "error", "message": "Not connected", "is_online": False}

        async def retrieve():
            device = await self._get_device()
            if not device:
                return {"status": "error", "message": "Device not found", "is_online": False}

            api = self.api
            if not api:
                return {"status": "error", "message": "Not connected", "is_online": False}
            assert api is not None

            response = await api.device.do_maintenance_retrieval(device)
            success, error = self._response_status(response)
            if not success:
                return {
                    "status": "error",
                    "message": error or "Maintenance retrieval failed",
                    "is_online": False,
                }

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            if not include_status:
                return {
                    "status": "success",
                    "message": "Maintenance retrieval completed",
                    "is_online": True,
                }

            status = await self._fetch_status()
            if "error" in status:
                return {
                    "status": "error",
                    "message": status.get("error", "Failed to fetch status"),
                    "is_online": False,
                }

            status["maintenance_retrieval"] = {
                "status": "success",
                "wait_seconds": wait_seconds
            }
            return status

        result = await self._run_with_connection(retrieve)
        if not result:
            return {"status": "error", "message": "Not connected", "is_online": False}
        return result

    async def start_circulation(self, duration: int = 5) -> dict:
        if not self.api or not self.device_id:
            return {"status": "error", "message": "Not connected"}

        async def run() -> dict:
            device = await self._get_device()
            if not device:
                return {"status": "error", "message": "Device not found"}

            api = self.api
            if not api:
                return {"status": "error", "message": "Not connected"}

            response = await api.device.start_recirculation(device, duration)
            success, error = self._response_status(response)
            if not success:
                return {"status": "error", "message": error or "Failed to start circulation"}

            return {
                "status": "success",
                "device": self.device_id,
                "action": "circulation",
                "duration_minutes": duration,
                "timestamp": datetime.now().isoformat()
            }

        result = await self._run_with_connection(run)
        if not isinstance(result, dict):
            return {"status": "error", "message": "Failed to start circulation"}
        return result

    async def get_schedules(self) -> list:
        if not self.device_id:
            return []

        async def run() -> list:
            info = await self._get_info()
            if not info:
                return []

            schedules = info.get("data", {}).get("getDevice", {}).get("schedule", {}).get("items", [])
            result = []
            for schedule in schedules:
                result.append({
                    "id": schedule.get("id"),
                    "name": schedule.get("name"),
                    "days": schedule.get("days", []),
                    "times": schedule.get("times", []),
                    "active": schedule.get("active", False)
                })
            return result

        result = await self._run_with_connection(run)
        if not result:
            return []
        return result

    async def close(self):
        if self.api:
            await self.api.close()
            self.api = None
            self._connected = False


rinnai_service = RinnaiService()
