from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from phue import Bridge
import logging
import uvicorn
import traceback
import pywemo
from typing import Dict, Optional, List
from wemo_schedule import WemoScheduleManager

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = FastAPI(title="Hue & Wemo Control API")

# 全局变量存储Bridge实例
bridge = None
light_name = os.getenv("HUE_LIGHT_NAME", "Test Light")

# Wemo设备管理
wemo_devices: Dict[str, pywemo.WeMoDevice] = {}
wemo_schedule_manager: Optional[WemoScheduleManager] = None

class LightState(BaseModel):
    on: bool
    bri: int = 254  # 默认最大亮度

async def turn_off_light_after_delay(light_name: str, minutes: float):
    """在指定分钟数后关闭灯"""
    try:
        await asyncio.sleep(minutes * 60)  # 转换为秒
        if bridge:
            # 获取灯的ID
            light_id = None
            for l in bridge.lights:
                if l.name == light_name:
                    light_id = l.light_id
                    break
            
            if light_id:
                bridge.set_light(light_id, 'on', False)
                logger.info(f"Light {light_name} turned off after {minutes} minutes")
            else:
                logger.error(f"Light {light_name} not found")
    except Exception as e:
        logger.error(f"Error turning off light: {str(e)}\n{traceback.format_exc()}")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    global wemo_schedule_manager
    if wemo_schedule_manager:
        wemo_schedule_manager.stop()
        logger.info("Wemo定时任务调度器已停止")

@app.on_event("startup")
async def startup_event():
    """启动时初始化Bridge连接和Wemo设备"""
    global bridge, wemo_devices, wemo_schedule_manager
    
    # 初始化Hue Bridge
    try:
        bridge_ip = os.getenv("HUE_BRIDGE_IP")
        if not bridge_ip:
            logger.error("HUE_BRIDGE_IP not set in environment variables")
        else:
            bridge = Bridge(bridge_ip)
            # 首次运行时需要按下Bridge上的按钮
            bridge.connect()
            logger.info("Successfully connected to Hue Bridge")
    except Exception as e:
        logger.error(f"Error connecting to Hue Bridge: {str(e)}\n{traceback.format_exc()}")
    
    # 初始化Wemo设备
    try:
        import yaml
        from pathlib import Path
        
        # 加载配置文件
        config_file = os.getenv("WEMO_CONFIG_FILE", "wemo_config.yaml")
        config_path = Path(config_file)
        
        # 是否自动发现设备
        auto_discover = os.getenv("WEMO_AUTO_DISCOVER", "false").lower() == "true"
        
        if config_path.exists():
            # 从配置文件加载设备信息
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            devices_config = config.get('devices', [])
            
            logger.info(f"从配置文件加载 {len(devices_config)} 个设备")
            for device_config in devices_config:
                device_name = device_config.get('name', '')
                host = device_config.get('host', '')
                port = device_config.get('port', 49153)
                
                if not device_name or not host:
                    logger.warning(f"设备配置不完整，跳过: {device_config}")
                    continue
                
                try:
                    # 使用hardcode的IP和端口连接设备
                    url = pywemo.setup_url_for_address(host, port)
                    device = pywemo.device_from_description(url)
                    device_name_lower = device_name.lower()
                    wemo_devices[device_name_lower] = device
                    logger.info(f"  注册设备: {device_name} ({host}:{port})")
                except Exception as e:
                    logger.warning(f"无法连接设备 {device_name} ({host}:{port}): {str(e)}")
        
        # 如果启用自动发现，扫描网络
        if auto_discover:
            logger.info("自动发现模式：正在扫描局域网...")
            discovered_devices = pywemo.discover_devices()
            if discovered_devices:
                logger.info(f"发现 {len(discovered_devices)} 个Wemo设备")
                for device in discovered_devices:
                    device_name_lower = device.name.lower()
                    if device_name_lower not in wemo_devices:
                        wemo_devices[device_name_lower] = device
                        logger.info(f"  发现新设备: {device.name} ({device.host})")
        
        if not wemo_devices:
            logger.info("未找到任何Wemo设备")
        else:
            logger.info(f"共注册 {len(wemo_devices)} 个Wemo设备")
        
        # 初始化定时任务管理器
        wemo_schedule_manager = WemoScheduleManager(config_file)
        
        # 注册所有设备到schedule管理器
        for name, device in wemo_devices.items():
            wemo_schedule_manager.register_device(name, device)
        
        # 启动定时任务调度器
        wemo_schedule_manager.start()
        
    except Exception as e:
        logger.error(f"Error initializing Wemo devices: {str(e)}\n{traceback.format_exc()}")

def get_light_id(light_name: str) -> int:
    """获取灯的ID，如果找不到返回None"""
    if not bridge:
        logger.debug("Bridge is not connected")
        return None
    try:
        logger.debug(f"Looking for light with name: {light_name}")
        logger.debug(f"Available lights: {bridge.lights}")
        for l in bridge.lights:
            logger.debug(f"Checking light: {l}, name: {getattr(l, 'name', None)}, id: {getattr(l, 'light_id', None)}")
            if getattr(l, 'name', None) == light_name:
                light_id = getattr(l, 'light_id', None)
                logger.debug(f"Found light with ID: {light_id}")
                return light_id
        logger.debug("Light not found")
    except Exception as e:
        logger.error(f"Error getting light ID: {str(e)}\n{traceback.format_exc()}")
    return None

def find_wemo_device(device_name: str) -> Optional[pywemo.WeMoDevice]:
    """
    查找Wemo设备（精确匹配，不区分大小写）
    
    Args:
        device_name: 设备名称（必须与配置中的name字段完全匹配，不区分大小写）
        
    Returns:
        找到的设备对象，如果未找到返回None
    """
    device_name_lower = device_name.lower()
    
    # 从缓存中精确匹配
    device = wemo_devices.get(device_name_lower)
    if device:
        return device
    
    # 如果缓存中没有，尝试重新发现设备（按需发现）
    logger.info(f"设备 {device_name} 未在缓存中找到，尝试重新发现...")
    try:
        devices = pywemo.discover_devices()
        
        # 精确匹配
        for d in devices:
            if d.name.lower() == device_name_lower:
                wemo_devices[device_name_lower] = d
                return d
    except Exception as e:
        logger.error(f"重新发现设备时出错: {str(e)}")
    
    return None

@app.get("/light/{minutes}")
async def control_light(minutes: float):
    """
    打开灯并在指定分钟数后关闭
    如果minutes为0，则立即关闭
    """
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not connected")
    
    if minutes < 0:
        raise HTTPException(status_code=400, detail="Minutes must be greater than or equal to 0")
    
    try:
        # 获取灯的ID
        light_id = get_light_id(light_name)
        if light_id is None:
            raise HTTPException(status_code=404, detail=f"Light {light_name} not found")
        
        if minutes == 0:
            # 立即关闭
            bridge.set_light(light_id, 'on', False)
            return {
                "status": "success",
                "message": "Light turned off immediately",
                "light_name": light_name,
                "turn_off_time": datetime.now().isoformat()
            }
        else:
            # 打开灯并设置延时关闭
            bridge.set_light(light_id, 'on', True)
            bridge.set_light(light_id, 'bri', 10)  # 设置亮度为最低（避免太亮）
            
            # 启动异步任务在指定时间后关闭灯
            asyncio.create_task(turn_off_light_after_delay(light_name, minutes))
            
            return {
                "status": "success",
                "message": f"Light turned on and will turn off in {minutes} minutes",
                "light_name": light_name,
                "turn_on_time": datetime.now().isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling light: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """获取灯的当前状态"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not connected")
    
    try:
        light_id = get_light_id(light_name)
        if light_id is None:
            raise HTTPException(status_code=404, detail=f"Light {light_name} not found")
        
        light = bridge.get_light(light_id)
        return {
            "name": light_name,
            "state": light["state"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting light status: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/state")
async def set_state(state: LightState):
    """设置灯的状态"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not connected")
    
    try:
        light_id = get_light_id(light_name)
        if light_id is None:
            raise HTTPException(status_code=404, detail=f"Light {light_name} not found")
        
        # 设置灯的状态
        bridge.set_light(light_id, {
            'on': state.on,
            'bri': state.bri
        })
        
        return {
            "status": "success",
            "message": "Light state updated",
            "light_name": light_name,
            "new_state": {
                "on": state.on,
                "bri": state.bri
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting light state: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Wemo API Endpoints ====================

@app.get("/wemo/devices")
async def list_wemo_devices():
    """列出所有发现的Wemo设备"""
    try:
        # 重新发现设备（可选，也可以只返回已发现的）
        devices = pywemo.discover_devices()
        
        device_list = []
        for device in devices:
            try:
                state = device.get_state()
                device_list.append({
                    "name": device.name,
                    "host": device.host,
                    "port": device.port,
                    "type": type(device).__name__,
                    "state": "on" if state else "off"
                })
            except Exception as e:
                logger.warning(f"获取设备 {device.name} 状态时出错: {str(e)}")
                device_list.append({
                    "name": device.name,
                    "host": device.host,
                    "port": device.port,
                    "type": type(device).__name__,
                    "state": "unknown",
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "count": len(device_list),
            "devices": device_list
        }
    except Exception as e:
        logger.error(f"Error listing Wemo devices: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/wemo/{device_name}/on")
async def wemo_turn_on(device_name: str):
    """开启指定的Wemo设备"""
    try:
        device = find_wemo_device(device_name)
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Wemo device '{device_name}' not found")
        
        device.on()
        current_state = device.get_state()
        
        return {
            "status": "success",
            "message": f"Device {device_name} turned on",
            "device_name": device.name,
            "state": "on" if current_state else "off",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error turning on Wemo device: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/wemo/{device_name}/off")
async def wemo_turn_off(device_name: str):
    """关闭指定的Wemo设备"""
    try:
        device = find_wemo_device(device_name)
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Wemo device '{device_name}' not found")
        
        device.off()
        current_state = device.get_state()
        
        return {
            "status": "success",
            "message": f"Device {device_name} turned off",
            "device_name": device.name,
            "state": "on" if current_state else "off",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error turning off Wemo device: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wemo/{device_name}/status")
async def wemo_get_status(device_name: str):
    """获取指定Wemo设备的状态"""
    try:
        device = find_wemo_device(device_name)
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Wemo device '{device_name}' not found")
        
        state = device.get_state()
        
        return {
            "name": device.name,
            "host": device.host,
            "port": device.port,
            "type": type(device).__name__,
            "state": "on" if state else "off",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Wemo device status: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wemo/schedule/tasks")
async def get_schedule_tasks():
    """获取所有已安排的定时任务"""
    try:
        if not wemo_schedule_manager:
            raise HTTPException(status_code=503, detail="Schedule manager not initialized")
        
        tasks = wemo_schedule_manager.get_scheduled_tasks()
        
        return {
            "status": "success",
            "count": len(tasks),
            "tasks": tasks,
            "config_file": wemo_schedule_manager.config_file
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule tasks: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """主函数，启动FastAPI服务器"""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main() 