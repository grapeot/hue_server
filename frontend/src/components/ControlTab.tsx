import { useEffect } from 'react';
import { useDeviceStore } from '../stores/deviceStore';

export function ControlTab() {
  const { status, loading, error, fetchStatus, toggleHue, toggleWemo, circulateRinnai, refreshRinnai, toggleGarage } = useDeviceStore();

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
        加载失败: {error}
      </div>
    );
  }

  const wemoDevices = status?.wemo ? Object.entries(status.wemo) : [];
  const wemoNames: Record<string, string> = {
    'coffee': '咖啡机',
    'veggie': '蔬菜灯',
    'tree': '圣诞树',
    'bedroom light': '卧室灯',
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-amber-700 text-sm">
          操作提示: {error}
        </div>
      )}

      {/* 灯光 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-yellow-50 to-orange-50 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800 flex items-center">
            <span className="text-xl mr-2">💡</span>
            灯光控制
          </h2>
        </div>
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">{status?.hue?.name || '卧室灯'}</div>
              <div className="text-sm text-gray-500 mt-0.5">
                {status?.hue?.error ? (
                  <span className="flex items-center text-amber-600">
                    <span className="w-2 h-2 bg-amber-400 rounded-full mr-1.5"></span>
                    离线 · {status.hue.error}
                  </span>
                ) : status?.hue?.is_on ? (
                  <span className="flex items-center">
                    <span className="w-2 h-2 bg-green-400 rounded-full mr-1.5"></span>
                    开启 · 亮度 {status.hue.brightness}
                    {status?.hue?.timer_active && <span className="ml-2 text-blue-500">⏱ 定时中</span>}
                  </span>
                ) : (
                  <span className="flex items-center">
                    <span className="w-2 h-2 bg-gray-300 rounded-full mr-1.5"></span>
                    关闭
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={toggleHue}
              className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                status?.hue?.is_on ? 'bg-blue-500' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform ${
                  status?.hue?.is_on ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </section>

      {/* 开关 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-green-50 to-teal-50 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800 flex items-center">
            <span className="text-xl mr-2">🔌</span>
            智能开关
          </h2>
        </div>
        <div className="divide-y divide-gray-50">
          {wemoDevices.map(([name, device]) => (
            <div key={name} className="flex items-center justify-between px-4 py-3">
              <div>
                <div className="font-medium text-gray-900">{wemoNames[name] || name}</div>
                <div className="text-sm text-gray-500">
                  {device.is_on === null ? '状态未知' : device.is_on ? '开启' : '关闭'}
                </div>
              </div>
              <button
                onClick={() => toggleWemo(name)}
                className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 ${
                  device.is_on ? 'bg-green-500' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform ${
                    device.is_on ? 'translate-x-7' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* 热水器 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800 flex items-center">
            <span className="text-xl mr-2">🚿</span>
            热水器
            <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${
              status?.rinnai?.is_online ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {status?.rinnai?.is_online ? '在线' : '离线'}
            </span>
          </h2>
        </div>
        <div className="p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-gray-50 rounded-lg px-3 py-2">
              <div className="text-gray-500">设定温度</div>
              <div className="font-semibold text-gray-900">{status?.rinnai?.set_temperature}°F</div>
            </div>
            <div className="bg-gray-50 rounded-lg px-3 py-2">
              <div className="text-gray-500">出水温度</div>
              <div className="font-semibold text-gray-900">{status?.rinnai?.outlet_temp}°F</div>
            </div>
            <div className="bg-gray-50 rounded-lg px-3 py-2">
              <div className="text-gray-500">进水温度</div>
              <div className="font-semibold text-gray-900">{status?.rinnai?.inlet_temp}°F</div>
            </div>
            <div className="bg-gray-50 rounded-lg px-3 py-2">
              <div className="text-gray-500">循环状态</div>
              <div className={`font-semibold ${status?.rinnai?.recirculation_enabled ? 'text-blue-600' : 'text-gray-900'}`}>
                {status?.rinnai?.recirculation_enabled ? '运行中' : '停止'}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            <button
              onClick={() => circulateRinnai(5)}
              className="px-4 py-2.5 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              触发 5 分钟循环
            </button>
            <button
              onClick={refreshRinnai}
              className="px-4 py-2.5 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
            >
              维护刷新
            </button>
          </div>
        </div>
      </section>

      {/* 车库门 */}
      {status?.garage?.available && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-4 py-3 bg-gradient-to-r from-gray-50 to-slate-50 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-800 flex items-center">
              <span className="text-xl mr-2">🚗</span>
              车库门
            </h2>
          </div>
          <div className="divide-y divide-gray-50">
            {Array.from({ length: Math.min(status.garage.door_count, 2) }, (_, i) => (
              <div key={i + 1} className="flex items-center justify-between px-4 py-3">
                <div>
                  <div className="font-medium text-gray-900">车库门 {i + 1}</div>
                  <div className="text-sm text-gray-500">点击触发开关</div>
                </div>
                <button
                  onClick={() => toggleGarage(i + 1)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
                >
                  触发
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
