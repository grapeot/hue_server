import asyncio
import pytest
from datetime import datetime, timedelta

from services.dynamic_scheduler import DynamicScheduler, ScheduledAction


class TestScheduledAction:
    
    def test_to_dict(self):
        now = datetime.now()
        execute_at = now + timedelta(minutes=5)
        
        action = ScheduledAction(
            id='test123',
            action_type='wemo.off',
            action_params={'device': 'tree'},
            minutes=5,
            created_at=now,
            execute_at=execute_at,
            status='pending',
        )
        
        result = action.to_dict()
        
        assert result['id'] == 'test123'
        assert result['action']['type'] == 'wemo.off'
        assert result['action']['params'] == {'device': 'tree'}
        assert result['action_display'] == '关闭 tree'
        assert result['minutes'] == 5
        assert result['status'] == 'pending'


class TestDynamicScheduler:
    
    @pytest.mark.asyncio
    async def test_schedule_creates_action(self):
        scheduler = DynamicScheduler()
        
        action = scheduler.schedule(
            action_type='wemo.off',
            action_params={'device': 'tree'},
            minutes=5,
        )
        
        assert action.id is not None
        assert action.action_type == 'wemo.off'
        assert action.status == 'pending'
        assert action in scheduler.pending_actions.values()
        
        scheduler.cancel(action.id)
    
    @pytest.mark.asyncio
    async def test_get_pending_returns_sorted_by_execute_at(self):
        scheduler = DynamicScheduler()
        
        action1 = scheduler.schedule('wemo.off', {'device': 'tree'}, minutes=10)
        action2 = scheduler.schedule('hue.off', {}, minutes=5)
        
        pending = scheduler.get_pending()
        
        assert len(pending) == 2
        assert pending[0].id == action2.id
        assert pending[1].id == action1.id
        
        scheduler.cancel(action1.id)
        scheduler.cancel(action2.id)
    
    @pytest.mark.asyncio
    async def test_cancel_action(self):
        scheduler = DynamicScheduler()
        
        action = scheduler.schedule('wemo.off', {'device': 'tree'}, minutes=5)
        
        result = scheduler.cancel(action.id)
        
        assert result is not None
        assert result.status == 'cancelled'
        assert action.id not in scheduler.pending_actions
    
    def test_cancel_nonexistent_action(self):
        scheduler = DynamicScheduler()
        
        result = scheduler.cancel('nonexistent')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_action_executes_after_delay(self):
        scheduler = DynamicScheduler()
        executed = []
        
        def handler(params):
            executed.append(params)
            return {'status': 'success'}
        
        from services.action_executor import action_executor
        action_executor.register('test.execute', handler)
        
        action = scheduler.schedule('test.execute', {'test': True}, minutes=0.01)
        
        await asyncio.sleep(0.8)
        
        assert len(executed) == 1
        assert executed[0] == {'test': True}
        assert action.status == 'completed'
        assert action.id not in scheduler.pending_actions
    
    @pytest.mark.asyncio
    async def test_cancelled_action_does_not_execute(self):
        scheduler = DynamicScheduler()
        executed = []
        
        def handler(params):
            executed.append(params)
            return {'status': 'success'}
        
        from services.action_executor import action_executor
        action_executor.register('test.cancel', handler)
        
        action = scheduler.schedule('test.cancel', {'test': True}, minutes=0.05)
        
        scheduler.cancel(action.id)
        
        await asyncio.sleep(0.1)
        
        assert len(executed) == 0
        assert action.status == 'cancelled'
    
    @pytest.mark.asyncio
    async def test_get_all_with_status_filter(self):
        scheduler = DynamicScheduler()
        
        action1 = scheduler.schedule('wemo.off', {'device': 'tree'}, minutes=5)
        action2 = scheduler.schedule('hue.off', {}, minutes=10)
        
        action1.status = 'completed'
        scheduler._move_to_completed(action1)
        
        pending = scheduler.get_all(status='pending')
        completed = scheduler.get_all(status='completed')
        
        assert len(pending) == 1
        assert len(completed) == 1
    
    @pytest.mark.asyncio
    async def test_completed_actions_limited(self):
        scheduler = DynamicScheduler()
        
        for i in range(60):
            action = scheduler.schedule('wemo.off', {'device': f'test{i}'}, minutes=i)
            action.status = 'completed'
            scheduler._move_to_completed(action)
        
        assert len(scheduler.completed_actions) == 50
