'use client';

import { Loader2, CheckCircle2, AlertCircle, Play } from 'lucide-react';
import { EvaluationJob } from '@/types';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useStartEvaluation, useEvaluationJob } from '@/hooks/useEvaluations';
import { useState } from 'react';

interface EvaluationStatusProps {
  projectId: string;
  candidateCount: number;
  evaluatedCount: number;
  onComplete?: () => void;
}

export default function EvaluationStatus({
  projectId,
  candidateCount,
  evaluatedCount,
  onComplete,
}: EvaluationStatusProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const startEvaluation = useStartEvaluation(projectId);
  const { data: job } = useEvaluationJob(projectId, jobId);

  const progress = candidateCount > 0 ? (evaluatedCount / candidateCount) * 100 : 0;
  const isAllEvaluated = evaluatedCount >= candidateCount && candidateCount > 0;
  const isRunning = job?.status === 'running' || job?.status === 'pending';
  const jobProgress = job ? (job.processed / Math.max(job.total, 1)) * 100 : 0;

  const handleStart = async () => {
    const j = await startEvaluation.mutateAsync();
    setJobId(j.id);
  };

  if (isAllEvaluated && !isRunning) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 border border-emerald-200 rounded-lg">
        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
        <span className="text-sm text-emerald-700 font-medium">
          All {candidateCount} candidates evaluated
        </span>
      </div>
    );
  }

  if (isRunning && job) {
    return (
      <div className="flex items-center gap-4 px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg">
        <Loader2 className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-blue-700">
            Evaluating candidates... {job.processed}/{job.total}
          </p>
          <Progress value={jobProgress} className="mt-1.5 h-1.5" />
        </div>
      </div>
    );
  }

  if (job?.status === 'failed') {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-red-50 border border-red-200 rounded-lg">
        <AlertCircle className="w-4 h-4 text-red-600" />
        <span className="text-sm text-red-700">Evaluation failed. </span>
        <button onClick={handleStart} className="text-sm text-red-700 underline">
          Retry
        </button>
      </div>
    );
  }

  return (
    <Button
      onClick={handleStart}
      disabled={startEvaluation.isPending || candidateCount === 0}
      className="gap-2"
    >
      {startEvaluation.isPending ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Play className="w-4 h-4" />
      )}
      Evaluate All ({candidateCount - evaluatedCount} remaining)
    </Button>
  );
}
