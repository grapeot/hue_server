"""Debug/info 接口 - 用于排查配置和连接问题"""
import os
import socket
from pathlib import Path

from fastapi import APIRouter
from services.hue_service import hue_service

router = APIRouter(prefix="/api", tags=["debug"])


def _test_tcp_connect(host: str, port: int = 80, timeout: float = 3.0) -> dict:
    """测试 TCP 连接，返回结果便于排查 No route to host"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        err = s.connect_ex((host, port))
        s.close()
        return {"reachable": err == 0, "errno": err, "message": "连接成功" if err == 0 else f"connect_ex 返回 {err}"}
    except Exception as e:
        return {"reachable": False, "errno": getattr(e, "errno", None), "message": str(e)}


@router.get("/debug")
async def get_debug_info():
    """返回配置与连接状态，含实际 HUE_BRIDGE_IP 和 TCP 连通性测试"""
    hue_ip = hue_service.bridge_ip or os.getenv("HUE_BRIDGE_IP")
    env_path = Path(__file__).parent.parent / ".env"
    hue_connectivity = _test_tcp_connect(hue_ip) if hue_ip else {"reachable": False, "message": "IP 未配置"}
    return {
        "hue": {
            "bridge_ip": hue_ip or "(未配置)",
            "configured": bool(hue_ip),
            "light_name": hue_service.light_name,
            "connectivity_test": hue_connectivity,
        },
        "env": {
            "file_exists": env_path.exists(),
            "path": str(env_path),
        },
        "rinnai": {
            "username_set": bool(os.getenv("RINNAI_USERNAME")),
            "password_set": bool(os.getenv("RINNAI_PASSWORD")),
        },
    }
