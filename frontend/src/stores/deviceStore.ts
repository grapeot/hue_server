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
      if (!res.ok) throw new Error('Failed to toggle Hue');
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
      await get().fetchStatus();
    } catch (error) {
      set({ error: String(error) });
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
