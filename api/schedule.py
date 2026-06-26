from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from models.schemas import CreateActionRequest, ScheduledActionListResponse, ScheduledActionResponse
from services.auth import require_control_auth

from services.dynamic_scheduler import dynamic_scheduler

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.post("/actions", response_model=ScheduledActionResponse, summary="Schedule a delayed action", dependencies=[Depends(require_control_auth)])
async def create_action(request: CreateActionRequest):
    action = dynamic_scheduler.schedule(
        action_type=request.action.type,
        action_params=request.action.params,
        minutes=request.minutes,
    )
    return action.to_dict()


@router.get("/actions", response_model=ScheduledActionListResponse, summary="List delayed actions")
async def list_actions(status: Optional[str] = Query(None, description="Optional action status filter")):
    actions = dynamic_scheduler.get_all(status)
    return {
        "actions": [a.to_dict() for a in actions]
    }


@router.delete("/actions/{action_id}", response_model=ScheduledActionResponse, summary="Cancel a delayed action", dependencies=[Depends(require_control_auth)])
async def cancel_action(action_id: str):
    action = dynamic_scheduler.cancel(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action.to_dict()
