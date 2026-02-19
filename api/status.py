import logging

from fastapi import APIRouter, Query
from services.hue_service import hue_service
from services.wemo_service import wemo_service
from services.rinnai_service import rinnai_service
from services.meross_service import meross_service

router = APIRouter(tags=["status"])
logger = logging.getLogger(__name__)


def _safe_hue_status():
    try:
        return hue_service.get_status()
    except Exception as e:
        logger.warning(f"Hue status failed: {e}")
        return {
            "name": hue_service.light_name,
            "error": str(e),
            "is_on": False,
            "brightness": 0,
            "timer_active": False,
        }


def _safe_wemo_status():
    try:
        return wemo_service.get_all_status()
    except Exception as e:
        logger.warning(f"Wemo status failed: {e}")
        return {"error": str(e)}


@router.get("/api/status")
async def get_all_status(rinnai_refresh: bool = Query(False, description="Trigger Rinnai maintenance before fetching")):
    try:
        rinnai_status = await rinnai_service.get_status(trigger_maintenance=rinnai_refresh)
    except Exception as e:
        logger.warning(f"Rinnai status failed: {e}")
        rinnai_status = {"error": str(e), "is_online": False}

    try:
        garage_door_count = meross_service.get_door_count()
        garage_available = meross_service._connected
    except Exception as e:
        logger.warning(f"Garage status failed: {e}")
        garage_door_count = 0
        garage_available = False

    return {
        "hue": _safe_hue_status(),
        "wemo": _safe_wemo_status(),
        "rinnai": rinnai_status,
        "garage": {
            "door_count": garage_door_count,
            "available": garage_available
        }
    }
