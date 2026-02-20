from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.dynamic_scheduler import dynamic_scheduler

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


class ActionParams(BaseModel):
    type: str
    params: dict = {}


class CreateActionRequest(BaseModel):
    minutes: float
    action: ActionParams


class ActionResponse(BaseModel):
    id: str
    action: dict
    action_display: str
    minutes: float
    created_at: str
    execute_at: str
    status: str


@router.post("/actions", response_model=ActionResponse)
async def create_action(request: CreateActionRequest):
    if request.minutes <= 0:
        raise HTTPException(status_code=400, detail="minutes must be positive")
    
    action = dynamic_scheduler.schedule(
        action_type=request.action.type,
        action_params=request.action.params,
        minutes=request.minutes,
    )
    return action.to_dict()


@router.get("/actions")
async def list_actions(status: Optional[str] = None):
    actions = dynamic_scheduler.get_all(status)
    return {
        "actions": [a.to_dict() for a in actions]
    }


@router.delete("/actions/{action_id}")
async def cancel_action(action_id: str):
    action = dynamic_scheduler.cancel(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action.to_dict()
