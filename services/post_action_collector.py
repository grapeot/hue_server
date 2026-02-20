import asyncio
import logging
import os
from typing import Optional

from models.database import save_device_state
from services.hue_service import hue_service
from services.wemo_service import wemo_service
from services.rinnai_service import rinnai_service

logger = logging.getLogger(__name__)

DEFAULT_DELAYS = {
    "hue": float(os.getenv("HUE_COLLECT_DELAY", "3")),
    "wemo": float(os.getenv("WEMO_COLLECT_DELAY", "3")),
    "rinnai": float(os.getenv("RINNAI_COLLECT_DELAY", "10")),
}


async def schedule_collection(
    device_type: str,
    device_name: str,
    delay_seconds: Optional[float] = None,
) -> None:
    if delay_seconds is None:
        delay_seconds = DEFAULT_DELAYS.get(device_type, 10.0)
    
    asyncio.create_task(_collect_and_save(device_type, device_name, delay_seconds))
    logger.debug(
        f"Scheduled collection for {device_type}/{device_name} in {delay_seconds}s"
    )


async def _collect_and_save(
    device_type: str, device_name: str, delay_seconds: float
) -> None:
    try:
        await asyncio.sleep(delay_seconds)
        
        data = await _fetch_device_status(device_type, device_name)
        if data is None:
            logger.warning(f"No data collected for {device_type}/{device_name}")
            return
        
        save_device_state(device_type, device_name, data)
        logger.info(f"Saved post-action collection for {device_type}/{device_name}")
        
    except Exception as e:
        logger.exception(f"Error in post-action collection for {device_type}/{device_name}: {e}")


async def _fetch_device_status(device_type: str, device_name: str) -> Optional[dict]:
    try:
        if device_type == "hue":
            status = hue_service.get_status()
            if "error" in status:
                return None
            is_on = status.get("is_on")
            return {
                "is_on": is_on,
                "brightness": status.get("brightness") if is_on else 0,
            }
        
        elif device_type == "wemo":
            all_status = wemo_service.get_all_status()
            status = all_status.get(device_name.lower())
            if status is None or "error" in status:
                return None
            return {"is_on": status.get("is_on")}
        
        elif device_type == "rinnai":
            status = await rinnai_service.get_status(trigger_maintenance=True)
            if "error" in status:
                return None
            inlet = status.get("inlet_temp")
            outlet = status.get("outlet_temp")
            if (inlet is None or inlet == 0) and (outlet is None or outlet == 0):
                return None
            return {
                "set_temperature": status.get("set_temperature"),
                "inlet_temp": inlet,
                "outlet_temp": outlet,
                "water_flow": status.get("water_flow"),
                "recirculation_enabled": status.get("recirculation_enabled"),
            }
        
        else:
            logger.warning(f"Unknown device type for collection: {device_type}")
            return None
            
    except Exception as e:
        logger.exception(f"Error fetching status for {device_type}/{device_name}: {e}")
        return None
