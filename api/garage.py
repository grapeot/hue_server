from fastapi import APIRouter
from services.meross_service import meross_service

router = APIRouter(prefix="/api/garage", tags=["garage"])

@router.get("/status")
async def get_garage_status():
    return {
        "door_count": meross_service.get_door_count(),
        "available": meross_service._connected
    }

@router.get("/{door_index}/toggle")
async def garage_toggle(door_index: int):
    door_count = meross_service.get_door_count()
    if door_index < 1 or door_index > door_count:
        from fastapi import HTTPException
        raise HTTPException(400, f"door_index 须在 1–{door_count} 之间")
    return await meross_service.toggle_door(door_index)
