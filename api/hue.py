from fastapi import APIRouter, Path
from models.schemas import ActionResult, HueStatus
from services.hue_service import hue_service
from services.post_action_collector import schedule_collection

router = APIRouter(prefix="/api/hue", tags=["hue"])

@router.get("/status", response_model=HueStatus, summary="Get Hue light status")
async def get_hue_status():
    return hue_service.get_status()

@router.get("/off", response_model=ActionResult, summary="Turn the Hue light off")
async def hue_off():
    result = hue_service.turn_off()
    await schedule_collection("hue", "baby_room")
    return result

@router.get("/on", response_model=ActionResult, summary="Turn the Hue light on")
async def hue_on():
    result = hue_service.turn_on(brightness=128)
    await schedule_collection("hue", "baby_room")
    return result

@router.get("/on/{brightness}", response_model=ActionResult, summary="Turn the Hue light on with brightness")
async def hue_on_with_brightness(brightness: int = Path(..., ge=1, le=254)):
    result = hue_service.turn_on(brightness=brightness)
    await schedule_collection("hue", "baby_room")
    return result

@router.get("/toggle", response_model=ActionResult, summary="Toggle the Hue light")
async def hue_toggle():
    result = hue_service.toggle()
    await schedule_collection("hue", "baby_room")
    return result
