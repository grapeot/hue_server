import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

ACTION_DISPLAY_NAMES = {
    'hue.toggle': '切换灯',
    'hue.on': '开灯',
    'hue.off': '关灯',
    'wemo.toggle': '切换 {device}',
    'wemo.on': '开启 {device}',
    'wemo.off': '关闭 {device}',
    'rinnai.circulate': '触发热水器循环 {duration} 分钟',
    'garage.toggle': '触发车库门 {door}',
}


def get_action_display(action_type: str, params: dict) -> str:
    template = ACTION_DISPLAY_NAMES.get(action_type, action_type)
    try:
        return template.format(**params)
    except KeyError:
        return template


class ActionExecutor:
    def __init__(self):
        self._handlers: dict[str, Callable] = {}
    
    def register(self, action_type: str, handler: Callable):
        self._handlers[action_type] = handler
        logger.debug(f"Registered action handler: {action_type}")
    
    async def execute(self, action_type: str, params: dict) -> dict:
        handler = self._handlers.get(action_type)
        if not handler:
            return {"status": "error", "message": f"Unknown action type: {action_type}"}
        
        try:
            result = handler(params)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except Exception as e:
            logger.exception(f"Error executing action {action_type}: {e}")
            return {"status": "error", "message": str(e)}


action_executor = ActionExecutor()


def init_action_executor():
    from services.hue_service import hue_service
    from services.wemo_service import wemo_service
    from services.rinnai_service import rinnai_service
    from services.meross_service import meross_service
    
    action_executor.register('hue.toggle', lambda _: hue_service.toggle())
    action_executor.register('hue.on', lambda p: hue_service.turn_on(p.get('brightness', 128)))
    action_executor.register('hue.off', lambda _: hue_service.turn_off())
    
    action_executor.register('wemo.toggle', lambda p: wemo_service.toggle(p['device']))
    action_executor.register('wemo.on', lambda p: wemo_service.turn_on(p['device']))
    action_executor.register('wemo.off', lambda p: wemo_service.turn_off(p['device']))
    
    action_executor.register('rinnai.circulate', lambda p: rinnai_service.start_circulation(p.get('duration', 5)))
    action_executor.register('garage.toggle', lambda p: meross_service.toggle_door(p['door']))
    
    logger.info("Action executor initialized")
