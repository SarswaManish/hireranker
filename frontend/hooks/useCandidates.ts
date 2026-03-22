'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { candidatesApi } from '@/lib/api';
import { CandidateFilters } from '@/types';

export const candidateKeys = {
  all: ['candidates'] as const,
  lists: (projectId: string) => [...candidateKeys.all, 'list', projectId] as const,
  filtered: (projectId: string, filters: CandidateFilters) =>
    [...candidateKeys.lists(projectId), filters] as const,
  detail: (projectId: string, candidateId: string) =>
    [...candidateKeys.all, 'detail', projectId, candidateId] as const,
};

export function useCandidates(projectId: string, filters?: CandidateFilters) {
  return useQuery({
    queryKey: candidateKeys.filtered(projectId, filters || {}),
    queryFn: () => candidatesApi.list(projectId, filters),
    enabled: !!projectId,
  });
}

export function useCandidate(projectId: string, candidateId: string) {
  return useQuery({
    queryKey: candidateKeys.detail(projectId, candidateId),
    queryFn: () => candidatesApi.get(projectId, candidateId),
    enabled: !!projectId && !!candidateId,
  });
}

export function useUpdateCandidateNotes(projectId: string, candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notes: string) =>
      candidatesApi.updateNotes(projectId, candidateId, notes),
    onSuccess: (data) => {
      queryClient.setQueryData(
        candidateKeys.detail(projectId, candidateId),
        data
      );
    },
  });
}
