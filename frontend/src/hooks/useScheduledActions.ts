import { useState, useEffect, useCallback } from 'react';

interface ScheduledAction {
  id: string;
  action: {
    type: string;
    params: Record<string, unknown>;
  };
  action_display: string;
  minutes: number;
  created_at: string;
  execute_at: string;
  status: string;
}

interface ScheduledActionsResponse {
  actions: ScheduledAction[];
}

export function useScheduledActions() {
  const [actions, setActions] = useState<ScheduledAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActions = useCallback(async () => {
    try {
      const res = await fetch('/api/schedule/actions?status=pending');
      if (res.ok) {
        const data: ScheduledActionsResponse = await res.json();
        setActions(data.actions);
        setError(null);
      } else {
        setError('加载失败');
      }
    } catch (err) {
      console.error('Failed to fetch scheduled actions:', err);
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const cancelAction = useCallback(async (actionId: string): Promise<boolean> => {
    try {
      const res = await fetch(`/api/schedule/actions/${actionId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        await fetchActions();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Failed to cancel action:', err);
      return false;
    }
  }, [fetchActions]);

  useEffect(() => {
    fetchActions();
    const interval = setInterval(fetchActions, 30000);
    return () => clearInterval(interval);
  }, [fetchActions]);

  return { actions, loading, error, cancelAction, refresh: fetchActions };
}
