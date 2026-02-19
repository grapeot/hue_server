import { create } from 'zustand';
import type { DeviceStatus } from '../types';

interface DeviceStore {
  status: DeviceStatus | null;
  loading: boolean;
  error: string | null;
  fetchStatus: () => Promise<void>;
  toggleHue: () => Promise<void>;
  toggleWemo: (name: string) => Promise<void>;
  circulateRinnai: (duration?: number) => Promise<void>;
  refreshRinnai: () => Promise<void>;
  toggleGarage: (doorIndex: number) => Promise<void>;
}

const API_BASE = '/api';

export const useDeviceStore = create<DeviceStore>((set, get) => ({
  status: null,
  loading: false,
  error: null,

  fetchStatus: async () => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/status`);
      if (!res.ok) throw new Error('Failed to fetch status');
      const data = await res.json();
      set({ status: data, loading: false });
    } catch (error) {
      set({ error: String(error), loading: false });
    }
  },

  toggleHue: async () => {
    try {
      const res = await fetch(`${API_BASE}/hue/toggle`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.status === 'error') {
        throw new Error(data.message || 'Failed to toggle Hue');
      }
      await get().fetchStatus();
    } catch (error) {
      set({ error: String(error) });
    }
  },

  toggleWemo: async (name: string) => {
    try {
      const res = await fetch(`${API_BASE}/wemo/${name}/toggle`);
      if (!res.ok) throw new Error('Failed to toggle Wemo');
      await get().fetchStatus();
    } catch (error) {
      set({ error: String(error) });
    }
  },

  circulateRinnai: async (duration = 5) => {
    try {
      const res = await fetch(`${API_BASE}/rinnai/circulate?duration=${duration}`);
      if (!res.ok) throw new Error('Failed to start circulation');
      await get().refreshRinnai();
      setTimeout(() => get().fetchStatus(), 10000);
    } catch (error) {
      set({ error: String(error) });
    }
  },

  refreshRinnai: async () => {
    set({ error: null });
    try {
      // Single request: trigger maintenance + fetch all status (waits ~5s for device to report)
      const res = await fetch(`${API_BASE}/status?rinnai_refresh=true`);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `维护刷新失败 (${res.status})`);
      }
      const data = await res.json();
      set({ status: data });
      setTimeout(() => get().fetchStatus(), 10000);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : String(error) });
    }
  },

  toggleGarage: async (doorIndex: number) => {
    try {
      const res = await fetch(`${API_BASE}/garage/${doorIndex}/toggle`);
      if (!res.ok) throw new Error('Failed to toggle garage door');
    } catch (error) {
      set({ error: String(error) });
    }
  },
}));
