from fastapi import APIRouter
from services.hue_service import hue_service
from services.post_action_collector import schedule_collection

router = APIRouter(prefix="/api/hue", tags=["hue"])

@router.get("/status")
async def get_hue_status():
    return hue_service.get_status()

@router.get("/off")
async def hue_off():
    result = hue_service.turn_off()
    await schedule_collection("hue", "baby_room")
    return result

@router.get("/on")
async def hue_on():
    result = hue_service.turn_on(brightness=128)
    await schedule_collection("hue", "baby_room")
    return result

@router.get("/on/{brightness}")
async def hue_on_with_brightness(brightness: int):
    result = hue_service.turn_on(brightness=brightness)
    await schedule_collection("hue", "baby_room")
    return result

@router.get("/toggle")
async def hue_toggle():
    result = hue_service.toggle()
    await schedule_collection("hue", "baby_room")
    return result
