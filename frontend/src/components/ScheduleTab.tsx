import { useEffect, useState } from 'react';

interface RinnaiSchedule {
  id: string;
  name: string;
  days: string[];
  times: string[];
  active: boolean;
}

const HUE_SCHEDULE = [
  { time: '20:00', action: 'on', brightness: 128, description: '开灯，亮度 128' },
  { time: '08:20', action: 'off', description: '关灯' },
];

const WEMO_SCHEDULE = [
  { device: 'Coffee', time: '07:45', action: 'on', description: '开启咖啡机' },
  { device: 'Coffee', time: '11:00', action: 'off', description: '关闭咖啡机' },
];

const WEMO_NAMES: Record<string, string> = {
  'Coffee': '咖啡机',
  'Veggie': '蔬菜灯',
  'Tree': '圣诞树',
  'Bedroom Light': '卧室灯',
};

export function ScheduleTab() {
  const [rinnaiSchedules, setRinnaiSchedules] = useState<RinnaiSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRinnaiSchedules();
  }, []);

  const fetchRinnaiSchedules = async () => {
    try {
      const res = await fetch('/api/rinnai/schedules');
      if (res.ok) {
        const data = await res.json();
        setRinnaiSchedules(data);
      } else {
        setError('加载失败');
      }
    } catch (err) {
      console.error('Failed to fetch Rinnai schedules:', err);
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const parseDays = (days: string[]) => {
    if (!days || days.length === 0) return '每天';
    if (days[0].includes('0=Su') && days[0].includes('6=S')) return '每天';
    return days.join(', ');
  };

  const parseTime = (times: string[]) => {
    if (!times || times.length === 0) return '';
    const match = times[0].match(/\{start=(\d{2}:\d{2}),end=(\d{2}:\d{2})\}/);
    if (match) {
      return `${match[1]} - ${match[2]}`;
    }
    return times[0];
  };

  return (
    <div className="space-y-4">
      {/* 灯光定时 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-yellow-50 to-orange-50 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800 flex items-center">
            <span className="text-xl mr-2">💡</span>
            灯光定时任务
          </h2>
        </div>
        <div className="divide-y divide-gray-50">
          {HUE_SCHEDULE.map((schedule, index) => (
            <div key={index} className="flex items-center justify-between px-4 py-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    {schedule.time}
                  </span>
                  <span className="font-medium text-gray-900">{schedule.description}</span>
                </div>
              </div>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">每天</span>
            </div>
          ))}
        </div>
      </section>

      {/* 开关定时 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-green-50 to-teal-50 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800 flex items-center">
            <span className="text-xl mr-2">🔌</span>
            开关定时任务
          </h2>
        </div>
        <div className="divide-y divide-gray-50">
          {WEMO_SCHEDULE.map((schedule, index) => (
            <div key={index} className="flex items-center justify-between px-4 py-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm bg-green-100 text-green-700 px-2 py-0.5 rounded">
                    {schedule.time}
                  </span>
                  <span className="font-medium text-gray-900">
                    {WEMO_NAMES[schedule.device] || schedule.device}
                  </span>
                  <span className="text-sm text-gray-500">{schedule.description}</span>
                </div>
              </div>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">每天</span>
            </div>
          ))}
        </div>
      </section>

      {/* 热水器定时 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800 flex items-center">
            <span className="text-xl mr-2">🚿</span>
            热水器定时任务
            <span className="ml-2 text-xs font-normal text-gray-500">（来自设备）</span>
          </h2>
        </div>
        {loading ? (
          <div className="p-4 text-gray-500 text-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500 mx-auto"></div>
          </div>
        ) : error ? (
          <div className="p-4 text-red-500 text-center">{error}</div>
        ) : rinnaiSchedules.length === 0 ? (
          <div className="p-4 text-gray-500 text-center">无定时任务</div>
        ) : (
          <div className="divide-y divide-gray-50">
            {rinnaiSchedules.map((schedule) => (
              <div key={schedule.id} className="flex items-center justify-between px-4 py-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                      {parseTime(schedule.times)}
                    </span>
                    <span className="font-medium text-gray-900">{schedule.name}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {parseDays(schedule.days)}
                  </span>
                  {schedule.active && (
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
