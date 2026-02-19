import { create } from 'zustand';
import type { DeviceStatus } from '../types';

type DeviceKey = 'hue' | 'wemo' | 'rinnai' | 'garage';

interface DeviceStore {
  status: DeviceStatus | null;
  loading: boolean;
  error: string | null;
  fetchStatus: (devices?: DeviceKey[]) => Promise<void>;
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

  fetchStatus: async (devices?: DeviceKey[]) => {
    set({ loading: true });
    try {
      const qs = devices?.length ? `?devices=${devices.join(',')}` : '';
      const res = await fetch(`${API_BASE}/status${qs}`);
      if (!res.ok) throw new Error('Failed to fetch status');
      const data = await res.json();
      const prev = get().status;
      const merged = prev ? { ...prev, ...data } : data;
      set({ status: merged, loading: false, error: null });
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
      await get().fetchStatus(['hue']);
    } catch (error) {
      set({ error: String(error) });
    }
  },

  toggleWemo: async (name: string) => {
    try {
      const res = await fetch(`${API_BASE}/wemo/${name}/toggle`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.status === 'error') {
        throw new Error(data.message || 'Failed to toggle Wemo');
      }
      await get().fetchStatus(['wemo']);
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
      const res = await fetch(`${API_BASE}/status?devices=rinnai&rinnai_refresh=true`);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `维护刷新失败 (${res.status})`);
      }
      const data = await res.json();
      const prev = get().status;
      set({ status: prev ? { ...prev, ...data } : data });
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
