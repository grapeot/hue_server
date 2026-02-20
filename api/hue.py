from fastapi import APIRouter
from services.hue_service import hue_service

router = APIRouter(prefix="/api/hue", tags=["hue"])

@router.get("/status")
async def get_hue_status():
    return hue_service.get_status()

@router.get("/off")
async def hue_off():
    return hue_service.turn_off()

@router.get("/on")
async def hue_on():
    return hue_service.turn_on(brightness=128)

@router.get("/on/{brightness}")
async def hue_on_with_brightness(brightness: int):
    return hue_service.turn_on(brightness=brightness)

@router.get("/toggle")
async def hue_toggle():
    return hue_service.toggle()
