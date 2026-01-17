import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { videosApi } from '../api/client';
import type { SavedVideosParams } from '../types';

export function useInboxVideos(channelId?: string) {
  return useQuery({
    queryKey: ['videos', 'inbox', channelId],
    queryFn: async () => {
      const { data } = await videosApi.getInbox(channelId);
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

export function useDiscardedVideos(days?: number) {
  return useQuery({
    queryKey: ['videos', 'discarded', days],
    queryFn: async () => {
      const { data } = await videosApi.getDiscarded(days);
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'discarded'] });
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'discarded'] });
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'discarded'] });
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'discarded'] });
    },
  });
}

export function useAddVideoFromUrl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (url: string) => videosApi.fromUrl(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved'] });
      queryClient.invalidateQueries({ queryKey: ['videos', 'discarded'] });
    },
  });
}

export function usePurgeAllDiscarded() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => videosApi.purgeAllDiscarded(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'discarded'] });
    },
  });
}