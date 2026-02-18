import { useState } from 'react';
import { ControlTab } from './components/ControlTab';
import { ScheduleTab } from './components/ScheduleTab';
import { HistoryTab } from './components/HistoryTab';

type Tab = 'control' | 'schedule' | 'history';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('control');

  const tabs: { key: Tab; label: string }[] = [
    { key: 'control', label: 'Control' },
    { key: 'schedule', label: 'Schedule' },
    { key: 'history', label: 'History' },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-800">🏠 Smart Home Dashboard</h1>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex space-x-4">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {activeTab === 'control' && <ControlTab />}
        {activeTab === 'schedule' && <ScheduleTab />}
        {activeTab === 'history' && <HistoryTab />}
      </main>
    </div>
  );
}

export default App;
