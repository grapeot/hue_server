from fastapi import APIRouter, Query
from services.hue_service import hue_service
from services.wemo_service import wemo_service
from services.rinnai_service import rinnai_service
from services.meross_service import meross_service

router = APIRouter(tags=["status"])

@router.get("/api/status")
async def get_all_status(rinnai_refresh: bool = Query(False, description="Trigger Rinnai maintenance before fetching")):
    rinnai_status = await rinnai_service.get_status(trigger_maintenance=rinnai_refresh)
    return {
        "hue": hue_service.get_status(),
        "wemo": wemo_service.get_all_status(),
        "rinnai": rinnai_status,
        "garage": {
            "door_count": meross_service.get_door_count(),
            "available": meross_service._connected
        }
    }
