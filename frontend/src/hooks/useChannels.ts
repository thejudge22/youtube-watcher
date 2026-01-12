import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { channelsApi } from '../api/client';
import type { Channel } from '../types';

export function useChannels() {
  return useQuery({
    queryKey: ['channels'],
    queryFn: async () => {
      const { data } = await channelsApi.list();
      return data;
    },
  });
}

export function useAddChannel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (url: string) => channelsApi.create(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });
}

export function useDeleteChannel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => channelsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });
}

export function useRefreshChannel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => channelsApi.refresh(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      queryClient.invalidateQueries({ queryKey: ['videos', 'inbox'] });
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