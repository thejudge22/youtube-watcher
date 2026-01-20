import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { videosApi } from '../api/client';
import type { SavedVideosParams, ShortsFilter } from '../types';

export function useInboxVideos(channelId?: string, shortsFilter?: ShortsFilter) {
  // Convert filter to API parameter
  const isShort = shortsFilter === 'shorts' ? true : shortsFilter === 'regular' ? false : undefined;

  return useQuery({
    queryKey: ['videos', 'inbox', channelId, shortsFilter],
    queryFn: async () => {
      const { data } = await videosApi.getInbox(channelId, isShort);
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

export function useSavedVideoChannels() {
  return useQuery({
    queryKey: ['videos', 'saved', 'channels'],
    queryFn: async () => {
      const { data } = await videosApi.getSavedChannels();
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved', 'channels'] });
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved', 'channels'] });
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved', 'channels'] });
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved', 'channels'] });
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
      queryClient.invalidateQueries({ queryKey: ['videos', 'saved', 'channels'] });
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

// Issue #8: Shorts detection hooks
export function useDetectShort() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (videoId: string) => videosApi.detectShort(videoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}

export function useDetectShortsBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (videoIds?: string[]) => videosApi.detectShortsBatch(videoIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos', 'inbox'] });
    },
  });
}