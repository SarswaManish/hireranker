'use client';

import { useParams } from 'next/navigation';
import { Loader2, AlertCircle } from 'lucide-react';
import Header from '@/components/layout/Header';
import CandidateDetail from '@/components/candidates/CandidateDetail';
import { useCandidate } from '@/hooks/useCandidates';

export default function CandidateDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const candidateId = params.candidateId as string;

  const { data: candidate, isLoading, error } = useCandidate(projectId, candidateId);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header
        title={candidate?.name || 'Candidate'}
        subtitle={candidate?.recommendation ? `Recommendation: ${candidate.recommendation.replace('_', ' ')}` : 'Loading...'}
      />

      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mx-auto mb-2" />
              <p className="text-sm text-gray-500">Loading candidate profile...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <p className="text-gray-600">Could not load candidate profile.</p>
              <p className="text-sm text-gray-400">Please try again or check your connection.</p>
            </div>
          </div>
        ) : candidate ? (
          <CandidateDetail candidate={candidate} projectId={projectId} />
        ) : null}
      </div>
    </div>
  );
}
