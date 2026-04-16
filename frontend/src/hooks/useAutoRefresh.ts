import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { autoRefreshApi } from '../api/client';
import type { AutoRefreshSettings } from '../types';

export function useAutoRefreshSettings() {
  return useQuery({
    queryKey: ['auto-refresh', 'settings'],
    queryFn: async () => {
      const { data } = await autoRefreshApi.getSettings();
      return data;
    },
  });
}

export function useUpdateAutoRefreshSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: AutoRefreshSettings) => autoRefreshApi.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-refresh', 'settings'] });
      queryClient.invalidateQueries({ queryKey: ['auto-refresh', 'status'] });
      queryClient.invalidateQueries({ queryKey: ['videos', 'inbox'] });
    },
  });
}

export function useAutoRefreshStatus() {
  return useQuery({
    queryKey: ['auto-refresh', 'status'],
    queryFn: async () => {
      const { data } = await autoRefreshApi.getStatus();
      return data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
}