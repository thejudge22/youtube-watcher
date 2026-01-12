import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { channelsApi, videosApi } from '../api/client';
import type { SavedVideosParams } from '../types';

export function useInboxVideos() {
  return useQuery({
    queryKey: ['videos', 'inbox'],
    queryFn: async () => {
      const { data } = await videosApi.getInbox();
      return data;
    },
  });
}

export function useSavedVideos(params?: SavedVideosParams) {
  return useQuery({
    queryKey: ['videos', 'saved', params],
    queryFn: async () => {
      const { data } = await videosApi.getSaved(params);
      return data;
    },
  });
}

export function useSaveVideo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => videosApi.save(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'inbox'] });
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved'] });
    },
  });
}

export function useDiscardVideo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => videosApi.discard(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'inbox'] });
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved'] });
    },
  });
}

export function useBulkSaveVideos() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (videoIds: string[]) => videosApi.bulkSave(videoIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'inbox'] });
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved'] });
    },
  });
}

export function useBulkDiscardVideos() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (videoIds: string[]) => videosApi.bulkDiscard(videoIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'inbox'] });
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved'] });
    },
  });
}

export function useAddVideoFromUrl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (url: string) => videosApi.fromUrl(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved'] });
    },
  });
}

export function useRefreshAllChannels() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => channelsApi.refreshAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      queryClient.invalidateQueries({ queryKey: ['videos', 'inbox'] });
    },
  });
}