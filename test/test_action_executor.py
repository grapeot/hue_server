import pytest
from services.action_executor import ActionExecutor, get_action_display, init_action_executor


class TestGetActionDisplay:
    
    def test_hue_toggle(self):
        result = get_action_display('hue.toggle', {})
        assert result == '切换灯'
    
    def test_hue_on(self):
        result = get_action_display('hue.on', {})
        assert result == '开灯'
    
    def test_hue_off(self):
        result = get_action_display('hue.off', {})
        assert result == '关灯'
    
    def test_wemo_off(self):
        result = get_action_display('wemo.off', {'device': 'tree'})
        assert result == '关闭 tree'
    
    def test_wemo_on(self):
        result = get_action_display('wemo.on', {'device': 'coffee'})
        assert result == '开启 coffee'
    
    def test_rinnai_circulate(self):
        result = get_action_display('rinnai.circulate', {'duration': 5})
        assert result == '触发热水器循环 5 分钟'
    
    def test_unknown_action(self):
        result = get_action_display('unknown.action', {})
        assert result == 'unknown.action'
    
    def test_template_missing_param(self):
        result = get_action_display('wemo.off', {})
        assert result == 'wemo.off'
    
    @pytest.mark.asyncio
    async def test_register_and_execute_sync(self):
        executor = ActionExecutor()
        executor.register('test.sync', lambda p: {"status": "success", "value": p.get('x', 0)})
        
        result = await executor.execute('test.sync', {'x': 42})
        assert result['status'] == 'success'
        assert result['value'] == 42
    
    @pytest.mark.asyncio
    async def test_register_and_execute_async(self):
        executor = ActionExecutor()
        async def async_handler(p):
            return {"status": "success", "async": True}
        executor.register('test.async', async_handler)
        
        result = await executor.execute('test.async', {})
        assert result['status'] == 'success'
        assert result['async'] is True
    
    @pytest.mark.asyncio
    async def test_unknown_action_type(self):
        executor = ActionExecutor()
        
        result = await executor.execute('unknown', {})
        assert result['status'] == 'error'
        assert 'Unknown action type' in result['message']
    
    @pytest.mark.asyncio
    async def test_handler_exception(self):
        executor = ActionExecutor()
        executor.register('test.error', lambda p: 1/0)
        
        result = await executor.execute('test.error', {})
        assert result['status'] == 'error'


class TestInitActionExecutor:
    
    def test_init_registers_all_handlers(self):
        from services.action_executor import action_executor
        
        init_action_executor()
        
        expected_handlers = [
            'hue.toggle', 'hue.on', 'hue.off',
            'wemo.toggle', 'wemo.on', 'wemo.off',
            'rinnai.circulate', 'garage.toggle'
        ]
        
        for handler in expected_handlers:
            assert handler in action_executor._handlers, f"Missing handler: {handler}"
