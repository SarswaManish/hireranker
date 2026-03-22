'use client';

import { useParams, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import Header from '@/components/layout/Header';
import CompareView from '@/components/candidates/CompareView';
import { useCandidates } from '@/hooks/useCandidates';
import { useProject } from '@/hooks/useProjects';

export default function ComparePage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const projectId = params.id as string;

  const { data: project } = useProject(projectId);
  const { data: candidateData, isLoading } = useCandidates(projectId, {
    page_size: 100,
  });

  const candidates = candidateData?.candidates || [];

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header
        title="Compare Candidates"
        subtitle={project?.name || ''}
      />

      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
          </div>
        ) : (
          <CompareView candidates={candidates} projectId={projectId} />
        )}
      </div>
    </div>
  );
}
