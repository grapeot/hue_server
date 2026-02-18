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

export function ScheduleTab() {
  const [rinnaiSchedules, setRinnaiSchedules] = useState<RinnaiSchedule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRinnaiSchedules();
  }, []);

  const fetchRinnaiSchedules = async () => {
    try {
      const res = await fetch('/api/rinnai/schedules');
      if (res.ok) {
        const data = await res.json();
        setRinnaiSchedules(data);
      }
    } catch (error) {
      console.error('Failed to fetch Rinnai schedules:', error);
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
    <div className="space-y-6">
      {/* Hue Schedule */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">💡</span> Hue 定时任务
        </h2>
        <div className="space-y-2">
          {HUE_SCHEDULE.map((schedule, index) => (
            <div key={index} className="flex justify-between items-center py-2 border-b last:border-b-0">
              <div>
                <div className="font-medium">{schedule.time}</div>
                <div className="text-sm text-gray-500">{schedule.description}</div>
              </div>
              <div className="text-sm bg-gray-100 px-2 py-1 rounded">每天</div>
            </div>
          ))}
        </div>
      </div>

      {/* Wemo Schedule */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">🔌</span> Wemo 定时任务
        </h2>
        <div className="space-y-2">
          {WEMO_SCHEDULE.map((schedule, index) => (
            <div key={index} className="flex justify-between items-center py-2 border-b last:border-b-0">
              <div>
                <div className="font-medium capitalize">{schedule.device} - {schedule.time}</div>
                <div className="text-sm text-gray-500">{schedule.description}</div>
              </div>
              <div className="text-sm bg-gray-100 px-2 py-1 rounded">每天</div>
            </div>
          ))}
        </div>
      </div>

      {/* Rinnai Schedule */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">🚿</span> 热水器定时任务 (来自设备)
        </h2>
        {loading ? (
          <div className="text-gray-500">加载中...</div>
        ) : rinnaiSchedules.length === 0 ? (
          <div className="text-gray-500">无定时任务</div>
        ) : (
          <div className="space-y-2">
            {rinnaiSchedules.map((schedule) => (
              <div key={schedule.id} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <div>
                  <div className="font-medium">{schedule.name}</div>
                  <div className="text-sm text-gray-500">{parseTime(schedule.times)}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm bg-gray-100 px-2 py-1 rounded">{parseDays(schedule.days)}</span>
                  {schedule.active && <span className="text-green-500 text-sm">✓</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
