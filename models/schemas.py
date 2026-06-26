from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ApiError(FlexibleModel):
    detail: str


class HealthResponse(FlexibleModel):
    status: str = Field(..., description="Service health status")


class HueStatus(FlexibleModel):
    name: Optional[str] = None
    is_on: Optional[bool] = None
    brightness: Optional[int] = None
    timer_active: Optional[bool] = None
    error: Optional[str] = None


class ActionResult(FlexibleModel):
    status: Optional[str] = Field(None, description="Action result status, usually success or error")
    message: Optional[str] = None


class WemoDeviceStatus(FlexibleModel):
    name: Optional[str] = None
    is_on: Optional[bool] = None
    host: Optional[str] = None
    port: Optional[int] = None
    error: Optional[str] = None


class RinnaiStatus(FlexibleModel):
    device_id: Optional[str] = None
    is_online: Optional[bool] = None
    set_temperature: Optional[int] = None
    inlet_temp: Optional[int] = None
    outlet_temp: Optional[int] = None
    water_flow: Optional[int] = None
    recirculation_enabled: Optional[bool] = None
    error: Optional[str] = None


class GarageStatus(FlexibleModel):
    door_count: int
    available: bool


class NotificationResult(FlexibleModel):
    enabled: Optional[bool] = None
    sent: Optional[bool] = None
    recipients: Optional[int] = None
    resend_id: Optional[str] = None
    reason: Optional[str] = None
    error: Optional[str] = None


class GarageToggleResponse(ActionResult):
    door: Optional[int] = None
    action: Optional[str] = None
    backend: Optional[str] = None
    previous_state: Optional[Dict[str, Any]] = None
    target_open: Optional[bool] = None
    reported_state: Optional[Any] = None
    executed: Optional[int] = None
    timestamp: Optional[str] = None
    notification: Optional[NotificationResult] = None


class AllStatusResponse(FlexibleModel):
    hue: Optional[HueStatus] = None
    wemo: Optional[Dict[str, WemoDeviceStatus]] = None
    rinnai: Optional[RinnaiStatus] = None
    garage: Optional[GarageStatus] = None


class HistoryRecord(FlexibleModel):
    id: Optional[int] = None
    device_type: str
    device_name: str
    timestamp: str
    data: Dict[str, Any]


class CameraInfo(FlexibleModel):
    id: str
    name: str


class CameraListResponse(FlexibleModel):
    cameras: List[CameraInfo]


class ScheduleAction(FlexibleModel):
    type: str = Field(..., description="Action type such as wemo.off, hue.toggle, or garage.toggle")
    params: Dict[str, Any] = Field(default_factory=dict)


class CreateActionRequest(FlexibleModel):
    minutes: float = Field(..., gt=0, description="Delay before execution, in minutes")
    action: ScheduleAction


class ScheduledActionResponse(FlexibleModel):
    id: str
    action: Optional[Dict[str, Any]] = None
    action_display: Optional[str] = None
    minutes: Optional[float] = None
    created_at: Optional[str] = None
    execute_at: Optional[str] = None
    status: str


class ScheduledActionListResponse(FlexibleModel):
    actions: List[ScheduledActionResponse]


DeviceKind = Literal["hue", "wemo", "rinnai", "garage"]
