import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { backupApi } from '../api/client';
import type { BackupSettings } from '../types';

export function useBackupSettings() {
  return useQuery({
    queryKey: ['backup', 'settings'],
    queryFn: async () => {
      const { data } = await backupApi.getSettings();
      return data;
    },
  });
}

export function useUpdateBackupSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: BackupSettings) => backupApi.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backup', 'settings'] });
      queryClient.invalidateQueries({ queryKey: ['backup', 'status'] });
    },
  });
}

export function useBackupStatus() {
  return useQuery({
    queryKey: ['backup', 'status'],
    queryFn: async () => {
      const { data } = await backupApi.getStatus();
      return data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
}

export function useBackupList() {
  return useQuery({
    queryKey: ['backup', 'list'],
    queryFn: async () => {
      const { data } = await backupApi.listBackups();
      return data;
    },
  });
}

export function useRunBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (format: string = 'json') => backupApi.runBackup(format),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backup', 'status'] });
      queryClient.invalidateQueries({ queryKey: ['backup', 'list'] });
    },
  });
}

export function useCleanupBackups() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => backupApi.cleanup(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backup', 'list'] });
    },
  });
}
