import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

const PACIFIC_TZ = 'America/Los_Angeles';

function formatPacificTime(ts: number | string, options?: Intl.DateTimeFormatOptions): string {
  const date = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  return date.toLocaleTimeString('en-US', { timeZone: PACIFIC_TZ, ...options });
}

interface HistoryRecord {
  id: number;
  device_type: string;
  device_name: string;
  timestamp: string;
  data: string | Record<string, unknown>;
}

function parseData(data: string | Record<string, unknown>): Record<string, unknown> {
  if (typeof data === 'string') {
    try {
      return JSON.parse(data);
    } catch {
      return {};
    }
  }
  return data;
}

export function HistoryTab() {
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history?hours=24');
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      } else {
        setError('获取历史数据失败');
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
      setError('获取历史数据失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-4 text-gray-500">加载中...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  if (history.length === 0) {
    return (
      <div className="p-4 text-gray-500">
        暂无历史数据。数据每30分钟采集一次，请稍后再查看。
      </div>
    );
  }

  const hueHistory = history
    .filter(h => h.device_type === 'hue')
    .map(h => {
      const data = parseData(h.data);
      const ts = new Date(h.timestamp).getTime();
      return {
        time: ts,
        timestamp: formatPacificTime(h.timestamp),
        brightness: (data.brightness as number) || 0,
        is_on: data.is_on ? 1 : 0,
      };
    })
    .sort((a, b) => a.time - b.time);

  const wemoHistory: Record<string, { timestamp: string; on_minutes: number }[]> = {};
  history
    .filter(h => h.device_type === 'wemo')
    .forEach(h => {
      if (!wemoHistory[h.device_name]) {
        wemoHistory[h.device_name] = [];
      }
      const data = parseData(h.data);
      wemoHistory[h.device_name].push({
        timestamp: formatPacificTime(h.timestamp),
        on_minutes: data.is_on ? 30 : 0,
      });
    });

  Object.keys(wemoHistory).forEach(name => {
    wemoHistory[name].reverse();
  });

  const rinnaiHistory = history
    .filter(h => h.device_type === 'rinnai')
    .map(h => {
      const data = parseData(h.data);
      const ts = new Date(h.timestamp).getTime();
      return {
        time: ts,
        timestamp: formatPacificTime(h.timestamp),
        inlet_temp: (data.inlet_temp as number) ?? 0,
        outlet_temp: (data.outlet_temp as number) ?? 0,
        set_temp: (data.set_temperature as number) ?? 0,
      };
    })
    .sort((a, b) => a.time - b.time);

  const wemoTotalOn: Record<string, number> = {};
  Object.entries(wemoHistory).forEach(([name, records]) => {
    wemoTotalOn[name] = records.reduce((sum, r) => sum + r.on_minutes, 0);
  });

  const wemoTotalData = Object.entries(wemoTotalOn).map(([name, minutes]) => ({
    name: name === 'coffee' ? '咖啡机' :
           name === 'veggie' ? '蔬菜灯' :
           name === 'tree' ? '圣诞树' :
           name === 'bedroom light' ? '卧室灯' : name,
    hours: Math.round((minutes / 60) * 10) / 10,
  }));

  return (
    <div className="space-y-6">
      {hueHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-3">💡 卧室灯亮度（24小时）</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hueHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(ts) => formatPacificTime(ts, { hour: '2-digit', minute: '2-digit' })}
                tick={{ fontSize: 10 }}
              />
              <YAxis domain={[0, 254]} />
              <Tooltip labelFormatter={(ts) => formatPacificTime(Number(ts))} />
              <Line type="monotone" dataKey="brightness" stroke="#8884d8" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {wemoTotalData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-3">🔌 开关开启时长（24小时）</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={wemoTotalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: '小时', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Bar dataKey="hours" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {rinnaiHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-3">🚿 热水器温度（24小时）</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={rinnaiHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(ts) => formatPacificTime(ts, { hour: '2-digit', minute: '2-digit' })}
                tick={{ fontSize: 10 }}
              />
              <YAxis domain={[0, 150]} />
              <Tooltip labelFormatter={(ts) => formatPacificTime(Number(ts))} />
              <Legend verticalAlign="bottom" height={36} />
              <Line type="monotone" dataKey="set_temp" stroke="#8884d8" dot={false} name="设定温度" />
              <Line type="monotone" dataKey="inlet_temp" stroke="#82ca9d" dot={false} name="进水温度" />
              <Line type="monotone" dataKey="outlet_temp" stroke="#ffc658" dot={false} name="出水温度" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
