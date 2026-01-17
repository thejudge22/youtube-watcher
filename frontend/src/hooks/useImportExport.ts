import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importExportApi, ExportData } from '../api/client';

export function useExportChannels() {
  return useMutation({
    mutationFn: async () => {
      const response = await importExportApi.exportChannels();
      downloadJson(response.data, 'youtube-watcher-channels');
    },
  });
}

export function useExportSavedVideos() {
  return useMutation({
    mutationFn: async () => {
      const response = await importExportApi.exportSavedVideos();
      downloadJson(response.data, 'youtube-watcher-saved-videos');
    },
  });
}

export function useExportAll() {
  return useMutation({
    mutationFn: async () => {
      const response = await importExportApi.exportAll();
      downloadJson(response.data, 'youtube-watcher-export');
    },
  });
}

export function useImportChannels() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (channels: ExportData['channels']) =>
      importExportApi.importChannels(channels).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });
}

export function useImportVideos() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (videos: ExportData['saved_videos']) =>
      importExportApi.importVideos(videos).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}

export function useImportVideoUrls() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (urls: string[]) =>
      importExportApi.importVideoUrls(urls).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}

// Helper function to trigger file download
function downloadJson(data: ExportData, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
