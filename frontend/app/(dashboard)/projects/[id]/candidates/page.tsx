'use client';

import { useState, useCallback, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Upload, MessageSquare, Loader2, Users, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Header from '@/components/layout/Header';
import CandidatesTable from '@/components/candidates/CandidatesTable';
import CandidateFilters from '@/components/candidates/CandidateFilters';
import EvaluationStatus from '@/components/evaluation/EvaluationStatus';
import RecruiterQuery from '@/components/evaluation/RecruiterQuery';
import { useCandidates } from '@/hooks/useCandidates';
import { useProject, useProjectStats } from '@/hooks/useProjects';
import { CandidateFilters as FiltersType, Recommendation } from '@/types';
import { getScoreColor } from '@/lib/utils';
import { candidatesApi } from '@/lib/api';

function StatBadge({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${color}`}>
      <span className="text-lg font-bold">{value}</span>
      <span className="text-xs font-medium">{label}</span>
    </div>
  );
}

export default function CandidatesPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [filters, setFilters] = useState<FiltersType>({ page: 1, page_size: 25 });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isQueryOpen, setIsQueryOpen] = useState(false);

  const { data: project } = useProject(projectId);
  const { data: stats, refetch: refetchStats } = useProjectStats(projectId);
  const { data: candidateData, isLoading } = useCandidates(projectId, filters);

  const candidates = candidateData?.candidates || [];
  const total = candidateData?.total || 0;
  const totalPages = candidateData?.total_pages || 1;

  const handleSelectToggle = useCallback((id: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((i) => i !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  }, []);

  const handleCompare = () => {
    if (selectedIds.length === 2) {
      router.push(
        `/projects/${projectId}/compare?a=${selectedIds[0]}&b=${selectedIds[1]}`
      );
    }
  };

  const handleExport = async () => {
    try {
      const blob = await candidatesApi.exportCSV(projectId, filters);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project?.name || 'candidates'}-export.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Export failed', e);
    }
  };

  const handleFiltersChange = useCallback((newFilters: FiltersType) => {
    setFilters(newFilters);
  }, []);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header
        title={project?.name || 'Candidates'}
        subtitle={project ? `${project.role_title} · ${project.company}` : ''}
      />

      <div className="flex-1 overflow-y-auto">
        {/* Stats bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex flex-wrap items-center gap-3">
            {stats && (
              <>
                <div className="flex items-center gap-1.5 text-gray-600">
                  <Users className="w-4 h-4" />
                  <span className="font-semibold">{stats.total_candidates}</span>
                  <span className="text-sm">total</span>
                </div>
                <span className="text-gray-200">|</span>
                <StatBadge label="Strong Yes" value={stats.strong_yes_count} color="bg-emerald-50 text-emerald-700" />
                <StatBadge label="Yes" value={stats.yes_count} color="bg-blue-50 text-blue-700" />
                <StatBadge label="Maybe" value={stats.maybe_count} color="bg-amber-50 text-amber-700" />
                <StatBadge label="No" value={stats.no_count} color="bg-red-50 text-red-700" />
                {stats.avg_score > 0 && (
                  <>
                    <span className="text-gray-200">|</span>
                    <div className="flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-500">Avg score:</span>
                      <span className={`text-sm font-bold px-1.5 py-0.5 rounded ${getScoreColor(stats.avg_score)}`}>
                        {Math.round(stats.avg_score)}
                      </span>
                    </div>
                  </>
                )}
              </>
            )}
            <div className="ml-auto flex items-center gap-2">
              <Link href={`/projects/${projectId}/import`}>
                <Button variant="outline" size="sm" className="gap-1.5">
                  <Upload className="w-4 h-4" />
                  Import
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsQueryOpen(true)}
                className="gap-1.5"
              >
                <MessageSquare className="w-4 h-4" />
                Ask AI
              </Button>
              {stats && (
                <EvaluationStatus
                  projectId={projectId}
                  candidateCount={stats.total_candidates}
                  evaluatedCount={stats.evaluated_candidates}
                  onComplete={refetchStats}
                />
              )}
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Filters */}
          <CandidateFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
          />

          {/* Table */}
          <CandidatesTable
            candidates={candidates}
            projectId={projectId}
            isLoading={isLoading}
            selectedIds={selectedIds}
            onSelectToggle={handleSelectToggle}
            onExport={handleExport}
            onCompare={handleCompare}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Showing {candidates.length} of {total} candidates
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilters((f) => ({ ...f, page: Math.max(1, (f.page || 1) - 1) }))}
                  disabled={!filters.page || filters.page <= 1}
                >
                  Previous
                </Button>
                <span className="text-sm text-gray-500 px-2">
                  Page {filters.page || 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilters((f) => ({ ...f, page: Math.min(totalPages, (f.page || 1) + 1) }))}
                  disabled={(filters.page || 1) >= totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recruiter query sidebar */}
      <RecruiterQuery
        projectId={projectId}
        isOpen={isQueryOpen}
        onClose={() => setIsQueryOpen(false)}
      />
    </div>
  );
}
