import asyncio
import logging
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import pytz

from services.action_executor import action_executor, get_action_display

logger = logging.getLogger(__name__)

PACIFIC_TZ = pytz.timezone('America/Los_Angeles')

MAX_COMPLETED_ACTIONS = 50


@dataclass
class ScheduledAction:
    id: str
    action_type: str
    action_params: dict
    minutes: float
    created_at: datetime
    execute_at: datetime
    status: str = 'pending'
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'action': {
                'type': self.action_type,
                'params': self.action_params,
            },
            'action_display': get_action_display(self.action_type, self.action_params),
            'minutes': self.minutes,
            'created_at': self.created_at.isoformat(),
            'execute_at': self.execute_at.isoformat(),
            'status': self.status,
        }


class DynamicScheduler:
    def __init__(self):
        self.pending_actions: dict[str, ScheduledAction] = {}
        self.completed_actions: deque[ScheduledAction] = deque(maxlen=MAX_COMPLETED_ACTIONS)
        self._tasks: dict[str, asyncio.Task] = {}
    
    def schedule(self, action_type: str, action_params: dict, minutes: float) -> ScheduledAction:
        action_id = str(uuid.uuid4())[:8]
        now = datetime.now(PACIFIC_TZ)
        execute_at = now + timedelta(minutes=minutes)
        
        action = ScheduledAction(
            id=action_id,
            action_type=action_type,
            action_params=action_params,
            minutes=minutes,
            created_at=now,
            execute_at=execute_at,
            status='pending',
        )
        
        self.pending_actions[action_id] = action
        task = asyncio.create_task(self._execute_after(action))
        self._tasks[action_id] = task
        
        logger.info(f"Scheduled action {action_id}: {action_type} in {minutes} minutes (at {execute_at})")
        return action
    
    async def _execute_after(self, action: ScheduledAction):
        try:
            delay_seconds = action.minutes * 60
            await asyncio.sleep(delay_seconds)
            
            if action.status == 'cancelled':
                return
            
            logger.info(f"Executing action {action.id}: {action.action_type}")
            result = await action_executor.execute(action.action_type, action.action_params)
            logger.info(f"Action {action.id} result: {result}")
            
            action.status = 'completed'
            self._move_to_completed(action)
            
        except asyncio.CancelledError:
            logger.info(f"Action {action.id} was cancelled")
            action.status = 'cancelled'
            self._move_to_completed(action)
            raise
        except Exception as e:
            logger.exception(f"Error executing action {action.id}: {e}")
            action.status = 'failed'
            self._move_to_completed(action)
    
    def _move_to_completed(self, action: ScheduledAction):
        if action.id in self.pending_actions:
            del self.pending_actions[action.id]
        if action.id in self._tasks:
            del self._tasks[action.id]
        self.completed_actions.append(action)
    
    def cancel(self, action_id: str) -> Optional[ScheduledAction]:
        action = self.pending_actions.get(action_id)
        if not action:
            return None
        
        task = self._tasks.get(action_id)
        if task and not task.done():
            task.cancel()
        
        action.status = 'cancelled'
        self._move_to_completed(action)
        logger.info(f"Cancelled action {action_id}")
        return action
    
    def get_pending(self) -> list[ScheduledAction]:
        return sorted(self.pending_actions.values(), key=lambda a: a.execute_at)
    
    def get_completed(self) -> list[ScheduledAction]:
        return list(self.completed_actions)
    
    def get_all(self, status: Optional[str] = None) -> list[ScheduledAction]:
        if status == 'pending':
            return self.get_pending()
        elif status == 'completed':
            return self.get_completed()
        elif status == 'cancelled':
            return [a for a in self.completed_actions if a.status == 'cancelled']
        else:
            return self.get_pending() + self.get_completed()


dynamic_scheduler = DynamicScheduler()
