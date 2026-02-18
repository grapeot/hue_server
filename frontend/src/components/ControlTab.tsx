import { useEffect } from 'react';
import { useDeviceStore } from '../stores/deviceStore';

export function ControlTab() {
  const { status, loading, error, fetchStatus, toggleHue, toggleWemo, circulateRinnai, toggleGarage } = useDeviceStore();

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (loading && !status) {
    return <div className="p-4">Loading...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">Error: {error}</div>;
  }

  const wemoDevices = status?.wemo ? Object.entries(status.wemo) : [];

  return (
    <div className="space-y-6">
      {/* Hue Light */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">💡</span> 灯光
        </h2>
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">{status?.hue?.name || 'Baby Room'}</div>
            <div className="text-sm text-gray-500">
              {status?.hue?.is_on ? `亮度: ${status.hue.brightness}` : '关闭'}
              {status?.hue?.timer_active && ' (Timer 活跃)'}
            </div>
          </div>
          <button
            onClick={toggleHue}
            className={`px-4 py-2 rounded-lg font-medium ${
              status?.hue?.is_on
                ? 'bg-yellow-500 text-white hover:bg-yellow-600'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {status?.hue?.is_on ? '关闭' : '开启'}
          </button>
        </div>
      </div>

      {/* Wemo Switches */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">🔌</span> 开关
        </h2>
        <div className="space-y-3">
          {wemoDevices.map(([name, device]) => (
            <div key={name} className="flex items-center justify-between">
              <div>
                <div className="font-medium capitalize">{name}</div>
                <div className="text-sm text-gray-500">
                  {device.is_on === null ? '未知' : device.is_on ? '开启' : '关闭'}
                </div>
              </div>
              <button
                onClick={() => toggleWemo(name)}
                className={`px-4 py-2 rounded-lg font-medium ${
                  device.is_on
                    ? 'bg-green-500 text-white hover:bg-green-600'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                切换
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Rinnai Heater */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">🚿</span> 热水器
        </h2>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">状态</span>
            <span className={status?.rinnai?.is_online ? 'text-green-500' : 'text-red-500'}>
              {status?.rinnai?.is_online ? '在线' : '离线'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">设定温度</span>
            <span>{status?.rinnai?.set_temperature}°F</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">进水温度</span>
            <span>{status?.rinnai?.inlet_temp}°F</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">出水温度</span>
            <span>{status?.rinnai?.outlet_temp}°F</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">循环状态</span>
            <span>{status?.rinnai?.recirculation_enabled ? '运行中' : '停止'}</span>
          </div>
        </div>
        <button
          onClick={() => circulateRinnai(5)}
          className="mt-4 w-full px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600"
        >
          触发5分钟循环
        </button>
      </div>

      {/* Garage Doors */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">🚗</span> 车库门
        </h2>
        <div className="space-y-3">
          {status?.garage?.available && Array.from({ length: Math.min(status.garage.door_count, 2) }, (_, i) => (
            <div key={i + 1} className="flex items-center justify-between">
              <div className="font-medium">Garage Door {i + 1}</div>
              <button
                onClick={() => toggleGarage(i + 1)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
              >
                触发开关
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
