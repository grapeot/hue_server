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
    return await meross_service.toggle_door(door_index)
