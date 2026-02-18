import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface HistoryRecord {
  id: number;
  device_type: string;
  device_name: string;
  timestamp: string;
  data: string;
}

export function HistoryTab() {
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history?hours=24');
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-4">Loading...</div>;
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
      const data = JSON.parse(h.data);
      return {
        timestamp: new Date(h.timestamp).toLocaleTimeString(),
        brightness: data.brightness || 0,
        is_on: data.is_on ? 1 : 0,
      };
    })
    .reverse();

  const wemoHistory: Record<string, { timestamp: string; on_minutes: number }[]> = {};
  history
    .filter(h => h.device_type === 'wemo')
    .forEach(h => {
      if (!wemoHistory[h.device_name]) {
        wemoHistory[h.device_name] = [];
      }
      const data = JSON.parse(h.data);
      wemoHistory[h.device_name].push({
        timestamp: new Date(h.timestamp).toLocaleTimeString(),
        on_minutes: data.is_on ? 30 : 0,
      });
    });

  Object.keys(wemoHistory).forEach(name => {
    wemoHistory[name].reverse();
  });

  const rinnaiHistory = history
    .filter(h => h.device_type === 'rinnai')
    .map(h => {
      const data = JSON.parse(h.data);
      return {
        timestamp: new Date(h.timestamp).toLocaleTimeString(),
        inlet_temp: data.inlet_temp || 0,
        outlet_temp: data.outlet_temp || 0,
        set_temp: data.set_temperature || 0,
      };
    })
    .reverse();

  const wemoTotalOn: Record<string, number> = {};
  Object.entries(wemoHistory).forEach(([name, records]) => {
    wemoTotalOn[name] = records.reduce((sum, r) => sum + r.on_minutes, 0);
  });

  const wemoTotalData = Object.entries(wemoTotalOn).map(([name, minutes]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    hours: Math.round((minutes / 60) * 10) / 10,
  }));

  return (
    <div className="space-y-6">
      {/* Hue Brightness */}
      {hueHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-3">💡 Baby Room 亮度 (24小时)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hueHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
              <YAxis domain={[0, 254]} />
              <Tooltip />
              <Line type="monotone" dataKey="brightness" stroke="#8884d8" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Wemo Summary */}
      {wemoTotalData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-3">🔌 开关开启时长 (24小时)</h2>
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

      {/* Rinnai Temperature */}
      {rinnaiHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-3">🚿 热水器温度 (24小时)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={rinnaiHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
              <YAxis domain={[0, 150]} />
              <Tooltip />
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
