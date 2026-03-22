'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { evaluationApi } from '@/lib/api';
import { projectKeys } from './useProjects';
import { candidateKeys } from './useCandidates';
import { RecruiterQuery } from '@/types';

export function useStartEvaluation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => evaluationApi.startEvaluation(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.stats(projectId) });
    },
  });
}

export function useEvaluationJob(projectId: string, jobId: string | null) {
  return useQuery({
    queryKey: ['evaluation', projectId, jobId],
    queryFn: () => evaluationApi.getJobStatus(projectId, jobId!),
    enabled: !!projectId && !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'pending' || data.status === 'running')) {
        return 2000;
      }
      return false;
    },
  });
}

export function useRecruiterQuery() {
  return useMutation({
    mutationFn: (data: RecruiterQuery) => evaluationApi.query(data),
  });
}

export function useQueryHistory(projectId: string) {
  return useQuery({
    queryKey: ['query-history', projectId],
    queryFn: () => evaluationApi.getQueryHistory(projectId),
    enabled: !!projectId,
  });
}
